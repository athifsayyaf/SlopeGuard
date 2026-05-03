from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import numpy as np

from .common import create_raster_quicklooks, ensure_output, missing_geospatial_error, require_path, unique_output_path, write_manifest

try:
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import calculate_default_transform, reproject
except Exception:  # pragma: no cover
    rasterio = None


def _read_projected_dem(dem_path: Path, crs: str, resolution: float):
    if rasterio is None:
        missing_geospatial_error()
    with rasterio.open(dem_path) as src:
        transform, width, height = calculate_default_transform(src.crs, crs, src.width, src.height, *src.bounds, resolution=resolution)
        dem = np.full((height, width), np.nan, dtype="float32")
        reproject(
            source=rasterio.band(src, 1),
            destination=dem,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=transform,
            dst_crs=crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
    return dem, transform, crs


def _write_raster(path: Path, array, transform, crs, description: str) -> str:
    profile = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": -9999.0,
        "compress": "deflate",
        "predictor": 2,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.where(np.isfinite(array), array, -9999.0).astype("float32"), 1)
        dst.set_band_description(1, description)
    return str(path)


def run_dem_tool(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    dem_path = require_path(params, "dem_path")
    output = ensure_output(params, Path("outputs") / "dem")
    crs = params.get("crs") or "EPSG:32644"
    resolution = float(params.get("resolution_m") or 30)
    tool = params.get("tool", "slope")
    progress(10, "Projecting DEM to analysis grid")
    dem, transform, crs = _read_projected_dem(dem_path, crs, resolution)
    filled = dem.copy()
    valid = np.isfinite(filled)
    if valid.any():
        filled[~valid] = np.nanmedian(filled[valid])
    yres = abs(transform.e)
    xres = abs(transform.a)
    dz_dy, dz_dx = np.gradient(filled, yres, xres)
    progress(55, f"Computing {tool}")
    if tool == "slope":
        out = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
        name = "slope.tif"
    elif tool == "aspect":
        dz_north = -dz_dy
        out = (np.degrees(np.arctan2(dz_dx, dz_north)) + 180.0) % 360.0
        name = "aspect.tif"
    elif tool == "hillshade":
        slope = np.pi / 2.0 - np.arctan(np.hypot(dz_dx, dz_dy))
        aspect = np.arctan2(-dz_dx, dz_dy)
        azimuth = np.radians(360 - float(params.get("azimuth", 315)) + 90)
        altitude = np.radians(float(params.get("altitude", 45)))
        out = 255 * ((np.sin(altitude) * np.sin(slope)) + (np.cos(altitude) * np.cos(slope) * np.cos(azimuth - aspect)) + 1) / 2
        name = "hillshade.tif"
    elif tool == "twi":
        slope = np.arctan(np.hypot(dz_dx, dz_dy))
        tan_slope = np.where(np.tan(slope) < 0.001, 0.001, np.tan(slope))
        out = np.log(abs(transform.a) / tan_slope)
        name = "twi.tif"
    else:
        raise ValueError(f"Unknown DEM tool: {tool}")
    out[~valid] = np.nan
    progress(80, "Writing GeoTIFF")
    raster_path = unique_output_path(output / name)
    raster = _write_raster(raster_path, out, transform, crs, tool)
    progress(90, "Creating PNG and JPG map previews")
    previews = create_raster_quicklooks(raster, f"{tool.title()} Map")
    manifest = write_manifest(output, tool, {"input": str(dem_path), "output": raster, "crs": crs, "resolution_m": resolution})
    return [raster, *previews, manifest]
