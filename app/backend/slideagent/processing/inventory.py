from __future__ import annotations

from pathlib import Path
import shutil

import numpy as np

from .common import create_raster_quicklooks, ensure_output, missing_geospatial_error, require_path, unique_output_path, write_manifest

try:
    import rasterio
    from rasterio.features import rasterize
except ImportError:  # pragma: no cover - handled at runtime
    rasterio = None
    rasterize = None


def _load_vector_shapes(path: Path, buffer_m: float, target_crs: str):
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - handled at runtime
        raise RuntimeError("geopandas is required to rasterize vector landslide inventories.") from exc

    inventory = gpd.read_file(path)
    if inventory.empty:
        raise ValueError(f"No features found in inventory: {path}")
    if inventory.crs is None:
        inventory = inventory.set_crs(target_crs, allow_override=True)
    else:
        inventory = inventory.to_crs(target_crs)
    if buffer_m > 0:
        inventory["geometry"] = inventory.geometry.buffer(buffer_m)
    return [(geom, 1) for geom in inventory.geometry if geom and not geom.is_empty]


def run_inventory_tool(params, progress):
    if rasterio is None or rasterize is None:
        raise RuntimeError(missing_geospatial_error())

    output_dir = ensure_output(params, Path("outputs") / "inventory")
    inventory_path = require_path(params, "inventory_path")
    reference_grid = require_path(params, "reference_grid")
    inventory_type = str(params.get("inventory_type", "polygon")).lower()
    buffer_m = float(params.get("buffer_m") or 0)

    progress(10, "Reading reference grid")
    with rasterio.open(reference_grid) as ref:
        profile = ref.profile.copy()
        transform = ref.transform
        target_crs = ref.crs
        shape = (ref.height, ref.width)

    profile.update(count=1, dtype="uint8", nodata=255, compress="deflate")
    output_path = unique_output_path(output_dir / "landslide_mask.tif")

    if inventory_type == "raster" or inventory_path.suffix.lower() in {".tif", ".tiff"}:
        progress(45, "Registering raster inventory")
        with rasterio.open(inventory_path) as src:
            if src.crs == target_crs and src.transform == transform and (src.height, src.width) == shape:
                mask = src.read(1)
            else:
                from rasterio.warp import Resampling, reproject

                mask = np.zeros(shape, dtype=np.uint8)
                reproject(
                    source=rasterio.band(src, 1),
                    destination=mask,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest,
                )
        mask = np.where(mask > 0, 1, 0).astype(np.uint8)
    else:
        progress(45, "Rasterizing vector inventory")
        shapes = _load_vector_shapes(inventory_path, buffer_m, str(target_crs))
        if not shapes:
            raise ValueError("No valid landslide geometries were available for rasterization.")
        mask = rasterize(
            shapes,
            out_shape=shape,
            transform=transform,
            fill=0,
            dtype="uint8",
            all_touched=True,
        )

    progress(80, "Writing landslide mask")
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(mask, 1)

    progress(90, "Creating PNG and JPG map previews")
    previews = create_raster_quicklooks(output_path, "Landslide Inventory Mask")
    manifest = write_manifest(
        output_dir,
        "landslide_inventory",
        {
            "tool": "landslide_inventory",
            "inventory_path": str(inventory_path),
            "reference_grid": str(reference_grid),
            "inventory_type": inventory_type,
            "buffer_m": buffer_m,
            "outputs": [str(output_path)],
        },
    )
    progress(100, "Inventory mask ready")
    return [str(output_path), *previews, str(manifest)]
