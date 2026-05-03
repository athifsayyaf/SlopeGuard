from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass
class ProjectConfig:
    project_name: str = "Kuwari Uttarakhand Monitoring"
    study_area_name: str = "Kuwari/Joshimath, Uttarakhand"
    crs: str = "EPSG:32644"
    resolution_m: float = 30.0
    output_folder: str = "outputs"
    bbox_wgs84: list[float] | None = None
    aoi_vector: str | None = None
    dem_path: str | None = None
    sentinel2_path: str | None = None
    insar_velocity_path: str | None = None
    insar_coherence_path: str | None = None
    landslide_inventory_path: str | None = None

    @classmethod
    def load(cls, path: Path) -> "ProjectConfig":
        if not path.exists():
            return cls()
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

