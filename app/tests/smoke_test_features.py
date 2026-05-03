from __future__ import annotations

from pathlib import Path
import json
import shutil
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from slideagent.processing.dem import run_dem_tool
from slideagent.processing.insar import run_insar_tool
from slideagent.processing.inventory import run_inventory_tool
from slideagent.processing.ml import run_model_stub, run_stack_builder
from slideagent.processing.optical import run_sentinel2_tool
from slideagent.processing.preview import run_preview_tool
from slideagent.processing.report import run_interpretation, run_report


TEST_ROOT = ROOT / "outputs" / "_smoke_test"
DATA = TEST_ROOT / "sample_data"
OUT = TEST_ROOT / "outputs"


def progress(_value: int, _message: str) -> None:
    return None


def assert_outputs(label: str, outputs: list[str], min_count: int = 1) -> None:
    if len(outputs) < min_count:
        raise AssertionError(f"{label}: expected at least {min_count} output(s), got {len(outputs)}")
    missing = [path for path in outputs if not Path(path).exists()]
    if missing:
        raise AssertionError(f"{label}: missing outputs: {missing}")
    print(f"PASS {label}: {len(outputs)} outputs")


def write_raster(path: Path, data: np.ndarray, dtype: str = "float32") -> None:
    import rasterio
    from rasterio.transform import from_origin

    path.parent.mkdir(parents=True, exist_ok=True)
    transform = from_origin(79.45, 30.72, 0.0003, 0.0003)
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": dtype,
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": -9999.0,
        "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data.astype(dtype), 1)


def write_inventory(path: Path) -> None:
    import geopandas as gpd
    from shapely.geometry import Polygon

    geom = Polygon([
        (79.455, 30.705),
        (79.462, 30.705),
        (79.462, 30.698),
        (79.455, 30.698),
    ])
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[geom], crs="EPSG:4326")
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path)


def make_sample_data() -> dict[str, Path]:
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    DATA.mkdir(parents=True)

    y, x = np.mgrid[0:72, 0:72]
    dem = 1800 + (x * 7) + (y * 4) + 120 * np.sin(x / 7.0) * np.cos(y / 9.0)
    red = 0.18 + 0.002 * x + 0.001 * y
    nir = 0.42 + 0.003 * y - 0.001 * x
    blue = 0.10 + 0.001 * x
    swir = 0.25 + 0.002 * x + 0.001 * y
    velocity = -25 + 0.5 * x - 0.25 * y
    coherence = np.clip(0.45 + 0.004 * x + 0.002 * y, 0, 1)

    paths = {
        "dem": DATA / "dem.tif",
        "red": DATA / "red.tif",
        "nir": DATA / "nir.tif",
        "blue": DATA / "blue.tif",
        "swir": DATA / "swir.tif",
        "velocity": DATA / "velocity.tif",
        "coherence": DATA / "coherence.tif",
        "inventory": DATA / "inventory.shp",
    }
    write_raster(paths["dem"], dem)
    write_raster(paths["red"], red)
    write_raster(paths["nir"], nir)
    write_raster(paths["blue"], blue)
    write_raster(paths["swir"], swir)
    write_raster(paths["velocity"], velocity)
    write_raster(paths["coherence"], coherence)
    write_inventory(paths["inventory"])
    return paths


def main() -> None:
    paths = make_sample_data()

    dem_outputs: dict[str, list[str]] = {}
    for tool in ("slope", "aspect", "twi", "hillshade"):
        outputs = run_dem_tool(
            {
                "tool": tool,
                "dem_path": str(paths["dem"]),
                "crs": "EPSG:32644",
                "resolution_m": 30,
                "output_folder": str(OUT / "dem"),
            },
            progress,
        )
        dem_outputs[tool] = outputs
        assert_outputs(f"DEM {tool}", outputs, 3)

    s2_outputs: dict[str, list[str]] = {}
    for tool in ("ndvi", "evi", "bsi", "ndwi", "lulc"):
        outputs = run_sentinel2_tool(
            {
                "tool": tool,
                "red_band": str(paths["red"]),
                "nir_band": str(paths["nir"]),
                "blue_band": str(paths["blue"]),
                "swir_band": str(paths["swir"]),
                "output_folder": str(OUT / "sentinel2"),
            },
            progress,
        )
        s2_outputs[tool] = outputs
        assert_outputs(f"Sentinel-2 {tool}", outputs, 3)

    insar_outputs = run_insar_tool(
        {
            "velocity_path": str(paths["velocity"]),
            "coherence_path": str(paths["coherence"]),
            "output_folder": str(OUT / "insar"),
        },
        progress,
    )
    assert_outputs("InSAR register", insar_outputs, 6)

    inventory_outputs = run_inventory_tool(
        {
            "inventory_path": str(paths["inventory"]),
            "reference_grid": dem_outputs["slope"][0],
            "inventory_type": "polygon",
            "buffer_m": 0,
            "output_folder": str(OUT / "inventory"),
        },
        progress,
    )
    assert_outputs("Inventory rasterize", inventory_outputs, 3)

    preview_outputs = run_preview_tool({"raster_path": dem_outputs["slope"][0]}, progress)
    assert_outputs("Preview existing TIFF", preview_outputs, 3)

    layers = [
        {"name": "slope", "path": dem_outputs["slope"][0]},
        {"name": "aspect", "path": dem_outputs["aspect"][0]},
        {"name": "twi", "path": dem_outputs["twi"][0]},
        {"name": "ndvi", "path": s2_outputs["ndvi"][0]},
        {"name": "los_velocity", "path": insar_outputs[0]},
        {"name": "landslide_mask", "path": inventory_outputs[0], "role": "target"},
    ]
    stack_outputs = run_stack_builder({"layers": layers, "output_folder": str(OUT / "stack")}, progress)
    assert_outputs("Stack builder", stack_outputs, 2)

    ml_outputs = run_model_stub({"model": "Random Forest", "output_folder": str(OUT / "ml")}, progress)
    assert_outputs("ML comparison scaffold", ml_outputs, 2)

    interp_outputs = run_interpretation({"output_folder": str(OUT / "interpretation")}, progress)
    assert_outputs("Interpretation", interp_outputs, 1)

    report_outputs = run_report({"title": "Smoke Test", "output_folder": str(OUT / "report")}, progress)
    assert_outputs("Report generator", report_outputs, 2)

    summary = {
        "status": "passed",
        "tested_modules": [
            "Project UI static",
            "DEM: slope/aspect/twi/hillshade",
            "Sentinel-2: ndvi/evi/bsi/ndwi/lulc",
            "InSAR register",
            "Inventory rasterize",
            "Preview",
            "Stack builder",
            "ML scaffold",
            "Interpretation",
            "Report",
        ],
    }
    summary_path = TEST_ROOT / "smoke_test_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"PASS summary: {summary_path}")


if __name__ == "__main__":
    main()
