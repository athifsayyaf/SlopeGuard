from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Callable
import json
import traceback
import uuid


@dataclass
class Job:
    id: str
    tool: str
    status: str = "queued"
    progress: int = 0
    message: str = "Queued"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    params: dict[str, Any] = field(default_factory=dict)
    outputs: list[str] = field(default_factory=list)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tool": self.tool,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "params": self.params,
            "outputs": self.outputs,
            "error": self.error,
        }


class JobStore:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

    def create(self, tool: str, params: dict[str, Any], target: Callable[[dict[str, Any], Callable[[int, str], None]], list[str]]) -> Job:
        job = Job(id=str(uuid.uuid4())[:8], tool=tool, params=params)
        with self._lock:
            self._jobs[job.id] = job
        thread = Thread(target=self._run, args=(job.id, target), daemon=True)
        thread.start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def _update(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in kwargs.items():
                setattr(job, key, value)
            job.updated_at = datetime.utcnow().isoformat() + "Z"
            self._write(job)

    def _write(self, job: Job) -> None:
        (self.log_dir / f"{job.id}_{job.tool}.json").write_text(json.dumps(job.as_dict(), indent=2), encoding="utf-8")

    def _run(self, job_id: str, target: Callable[[dict[str, Any], Callable[[int, str], None]], list[str]]) -> None:
        job = self.get(job_id)
        if not job:
            return

        def progress(value: int, message: str) -> None:
            self._update(job_id, progress=max(0, min(100, int(value))), message=message)

        try:
            self._update(job_id, status="running", progress=2, message="Starting")
            outputs = target(job.params, progress)
            self._update(job_id, status="completed", progress=100, message="Completed", outputs=outputs)
        except Exception as exc:  # noqa: BLE001 - job boundary should capture all failures.
            err = f"{exc}\n{traceback.format_exc()}"
            self._update(job_id, status="failed", message=str(exc), error=err)

