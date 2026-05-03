from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .common import create_raster_quicklooks, require_path


def run_preview_tool(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    raster = require_path(params, "raster_path")
    if raster.suffix.lower() not in {".tif", ".tiff"}:
        if raster.suffix.lower() in {".png", ".jpg", ".jpeg"}:
            return [str(raster)]
        raise ValueError("Preview supports GeoTIFF, PNG, and JPG files.")
    progress(40, "Creating browser map previews")
    outputs = create_raster_quicklooks(raster, params.get("title") or raster.stem.replace("_", " ").title())
    if not outputs:
        raise RuntimeError(f"Could not create preview for: {raster}")
    progress(100, "Preview ready")
    return [str(raster), *outputs]
