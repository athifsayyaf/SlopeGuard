from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import shutil

from .common import create_raster_quicklooks, ensure_output, require_path, unique_output_path, write_manifest


def run_insar_tool(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    output = ensure_output(params, Path("outputs") / "insar")
    outputs: list[str] = []
    progress(15, "Registering InSAR inputs")
    velocity = params.get("velocity_path")
    coherence = params.get("coherence_path")
    if velocity:
        src = require_path(params, "velocity_path")
        dst = unique_output_path(output / "los_velocity.tif")
        shutil.copy2(src, dst)
        outputs.append(str(dst))
        outputs.extend(create_raster_quicklooks(dst, "LOS Velocity Map"))
    if coherence:
        src = require_path(params, "coherence_path")
        dst = unique_output_path(output / "mean_coherence.tif")
        shutil.copy2(src, dst)
        outputs.append(str(dst))
        outputs.extend(create_raster_quicklooks(dst, "Mean Coherence Map"))
    if not outputs:
        raise ValueError("Upload or point to at least a velocity or coherence raster.")
    progress(70, "Writing InSAR manifest")
    outputs.append(write_manifest(output, "insar", {"mode": params.get("mode", "preprocessed_upload"), "outputs": outputs}))
    return outputs
