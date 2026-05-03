from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import numpy as np

from .common import create_raster_quicklooks, ensure_output, missing_geospatial_error, require_path, unique_output_path, write_manifest

try:
    import rasterio
except Exception:  # pragma: no cover
    rasterio = None


def _read(path: Path):
    if rasterio is None:
        missing_geospatial_error()
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        if src.nodata is not None:
            arr = np.where(arr == src.nodata, np.nan, arr)
        return arr, src.profile.copy()


def _write(path: Path, arr, profile, description: str) -> str:
    profile.update(dtype="float32", count=1, nodata=-9999.0, compress="deflate", predictor=2)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.where(np.isfinite(arr), arr, -9999.0).astype("float32"), 1)
        dst.set_band_description(1, description)
    return str(path)


def run_sentinel2_tool(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    output = ensure_output(params, Path("outputs") / "sentinel2")
    tool = params.get("tool", "ndvi")
    progress(10, "Reading bands")
    red, profile = _read(require_path(params, "red_band"))
    nir, _ = _read(require_path(params, "nir_band"))
    eps = 1e-6
    if tool == "ndvi":
        arr = (nir - red) / (nir + red + eps)
        name = "ndvi.tif"
    elif tool == "evi":
        blue, _ = _read(require_path(params, "blue_band"))
        arr = 2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1 + eps)
        name = "evi.tif"
    elif tool == "bsi":
        swir, _ = _read(require_path(params, "swir_band"))
        blue, _ = _read(require_path(params, "blue_band"))
        arr = ((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue) + eps)
        name = "bsi.tif"
    elif tool == "ndwi":
        swir, _ = _read(require_path(params, "swir_band"))
        arr = (nir - swir) / (nir + swir + eps)
        name = "ndwi.tif"
    elif tool == "lulc":
        swir, _ = _read(require_path(params, "swir_band"))
        blue, _ = _read(require_path(params, "blue_band"))
        ndvi = (nir - red) / (nir + red + eps)
        ndwi = (nir - swir) / (nir + swir + eps)
        bsi = ((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue) + eps)
        arr = np.full(red.shape, 1, dtype="float32")
        arr = np.where(ndwi > 0.18, 2, arr)  # water/moist surfaces
        arr = np.where(ndvi > 0.35, 3, arr)  # vegetation
        arr = np.where(bsi > 0.12, 4, arr)  # bare soil/rock
        arr = np.where(~np.isfinite(red + nir + swir + blue), np.nan, arr)
        name = "lulc.tif"
    else:
        raise ValueError(f"Unknown Sentinel-2 tool: {tool}")
    progress(80, "Writing index raster")
    if tool == "lulc":
        raster = _write(unique_output_path(output / name), arr, profile, tool.upper())
    else:
        raster = _write(unique_output_path(output / name), np.clip(arr, -1, 1), profile, tool.upper())
    progress(90, "Creating PNG and JPG map previews")
    previews = create_raster_quicklooks(raster, f"{tool.upper()} Map")
    manifest = write_manifest(output, tool, {"tool": tool, "output": raster})
    return [raster, *previews, manifest]
