from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import json
import mimetypes
import sys

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
LOGS = ROOT / "logs"
OUTPUTS = ROOT / "outputs"
PROJECT_CONFIG = ROOT / "project_config.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from slideagent.config import ProjectConfig  # noqa: E402
from slideagent.jobs import JobStore  # noqa: E402
from slideagent.processing.dem import run_dem_tool  # noqa: E402
from slideagent.processing.insar import run_insar_tool  # noqa: E402
from slideagent.processing.inventory import run_inventory_tool  # noqa: E402
from slideagent.processing.ml import run_model_stub, run_stack_builder  # noqa: E402
from slideagent.processing.optical import run_sentinel2_tool  # noqa: E402
from slideagent.processing.preview import run_preview_tool  # noqa: E402
from slideagent.processing.report import run_interpretation, run_report  # noqa: E402

jobs = JobStore(LOGS)

TOOLS = {
    "dem": run_dem_tool,
    "sentinel2": run_sentinel2_tool,
    "insar": run_insar_tool,
    "inventory": run_inventory_tool,
    "stack": run_stack_builder,
    "ml": run_model_stub,
    "interpretation": run_interpretation,
    "report": run_report,
    "preview": run_preview_tool,
}


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/project":
            return self._json(ProjectConfig.load(PROJECT_CONFIG).__dict__)
        if path == "/api/jobs":
            return self._json([job.as_dict() for job in jobs.list()])
        if path.startswith("/api/jobs/"):
            job = jobs.get(path.rsplit("/", 1)[-1])
            return self._json(job.as_dict() if job else {"error": "Job not found"}, 200 if job else 404)
        if path == "/api/file":
            return self._file(parsed)
        return self._static(path)

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        payload = self._read_json()
        if path == "/api/project":
            config = ProjectConfig(**payload)
            config.save(PROJECT_CONFIG)
            return self._json({"ok": True, "path": str(PROJECT_CONFIG), "config": config.__dict__})
        if path.startswith("/api/run/"):
            tool = path.rsplit("/", 1)[-1]
            target = TOOLS.get(tool)
            if not target:
                return self._json({"error": f"Unknown tool: {tool}"}, 404)
            payload.setdefault("output_folder", str(OUTPUTS / tool))
            job = jobs.create(tool, payload, target)
            return self._json(job.as_dict(), 202)
        return self._json({"error": "Not found"}, 404)

    def _static(self, path):
        if path in ("", "/"):
            file_path = FRONTEND / "index.html"
        else:
            file_path = (FRONTEND / path.lstrip("/")).resolve()
            if FRONTEND.resolve() not in file_path.parents and file_path != FRONTEND.resolve():
                return self._json({"error": "Forbidden"}, 403)
        if not file_path.exists() or not file_path.is_file():
            return self._json({"error": "Not found"}, 404)
        data = file_path.read_bytes()
        ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, parsed):
        query = parse_qs(parsed.query)
        requested = query.get("path", [""])[0]
        if not requested:
            return self._json({"error": "Missing file path"}, 400)
        file_path = Path(unquote(requested))
        if not file_path.exists() or not file_path.is_file():
            return self._json({"error": f"File not found: {file_path}"}, 404)
        if file_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".json", ".csv", ".txt", ".pdf"}:
            return self._json({"error": "Only browser-safe output files can be opened here."}, 403)
        data = file_path.read_bytes()
        ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[SlopeGuard] {self.address_string()} - {fmt % args}")


def main():
    OUTPUTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    host = "127.0.0.1"
    port = 8765
    print(f"SlopeGuard AI running as a local desktop backend on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
