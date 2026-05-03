from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import math

import numpy as np


def ensure_output(params: dict[str, Any], default_dir: Path) -> Path:
    output = Path(params.get("output_folder") or default_dir)
    output.mkdir(parents=True, exist_ok=True)
    return output


def require_path(params: dict[str, Any], key: str) -> Path:
    value = params.get(key)
    if not value:
        raise ValueError(f"Missing required parameter: {key}")
    path = Path(value)
    if not path.exists():
        raise FileNotFoundError(f"{key} not found: {path}")
    return path


def write_manifest(output_dir: Path, name: str, payload: dict[str, Any]) -> str:
    path = output_dir / f"{name}_manifest.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def unique_output_path(path: str | Path) -> Path:
    """Return a non-existing path so raster writers never delete locked sidecars."""
    candidate = Path(path)
    if not candidate.exists() and not Path(str(candidate) + ".ovr").exists():
        return candidate
    for index in range(1, 1000):
        numbered = candidate.with_name(f"{candidate.stem}_{index:02d}{candidate.suffix}")
        if not numbered.exists() and not Path(str(numbered) + ".ovr").exists():
            return numbered
    raise RuntimeError(f"Could not find a free output filename near {candidate}")


def missing_geospatial_error() -> None:
    raise RuntimeError(
        "This tool needs geospatial Python packages. Install requirements.txt "
        "or use the bundled environment that contains rasterio/GDAL/geopandas."
    )


def create_raster_quicklooks(raster_path: str | Path, title: str | None = None, cmap: str | None = None) -> list[str]:
    """Create browser-friendly PNG/JPG map previews next to a GeoTIFF."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
        import rasterio
    except Exception:
        return []

    path = Path(raster_path)
    if not path.exists() or path.suffix.lower() not in {".tif", ".tiff"}:
        return []

    with rasterio.open(path) as src:
        data = src.read(1).astype("float32")
        nodata = src.nodata
        bounds = src.bounds
        crs = src.crs
        transform = src.transform

    if nodata is not None:
        data = np.where(data == nodata, np.nan, data)
    finite = np.isfinite(data)
    if not finite.any():
        return []

    low, high = np.nanpercentile(data, [2, 98])
    if math.isclose(float(low), float(high)):
        low, high = float(np.nanmin(data)), float(np.nanmax(data))

    name = path.stem.lower()
    if cmap is None:
        if "slope" in name:
            cmap = LinearSegmentedColormap.from_list(
                "slopeguard_risk",
                ["#f4f4dc", "#d7e7a9", "#acd39e", "#d9a441", "#bf6f37", "#9d3d2f"],
            )
        elif "aspect" in name:
            cmap = "twilight"
        elif "hillshade" in name:
            cmap = "gray"
        elif "ndvi" in name:
            cmap = LinearSegmentedColormap.from_list(
                "slopeguard_ndvi",
                ["#b54833", "#d7a542", "#f4f4dc", "#7aa35a", "#2f7d4f"],
            )
        elif "coherence" in name:
            cmap = LinearSegmentedColormap.from_list(
                "slopeguard_coherence",
                ["#f4f4dc", "#d7e7a9", "#7aa35a", "#2f7d4f"],
            )
        elif "velocity" in name or "insar" in name:
            cmap = LinearSegmentedColormap.from_list(
                "slopeguard_velocity",
                ["#2166ac", "#f4f4dc", "#b54833"],
            )
        elif "mask" in name:
            cmap = "gray_r"
        else:
            cmap = LinearSegmentedColormap.from_list(
                "slopeguard_terrain",
                ["#2f7d4f", "#7aa35a", "#d7a542", "#bf6f37"],
            )

    pretty_title = title or path.stem.replace("_", " ").title()
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    width_m = abs(transform.a) * data.shape[1]
    scale_km = max(1, round((width_m / 5) / 1000))

    outputs: list[str] = []
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=180)
    img = ax.imshow(data, cmap=cmap, vmin=low, vmax=high, extent=extent, origin="upper")
    ax.set_title(pretty_title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(f"CRS: {crs}" if crs else "Map coordinates")
    ax.set_ylabel("Map coordinates")
    ax.grid(color="white", linewidth=0.35, alpha=0.45)

    cbar = fig.colorbar(img, ax=ax, shrink=0.78, pad=0.02)
    cbar.ax.set_ylabel(path.stem.replace("_", " "), rotation=270, labelpad=16)

    ax.annotate(
        "N",
        xy=(0.94, 0.88),
        xytext=(0.94, 0.74),
        xycoords="axes fraction",
        arrowprops=dict(facecolor="black", width=4, headwidth=15),
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="black",
    )
    ax.plot([0.08, 0.22], [0.08, 0.08], transform=ax.transAxes, color="black", linewidth=4, solid_capstyle="butt")
    ax.text(0.23, 0.075, f"{scale_km} km", transform=ax.transAxes, fontsize=10, fontweight="bold", va="center")

    fig.tight_layout()
    for suffix, kwargs in (
        ("png", {}),
        ("jpg", {"pil_kwargs": {"quality": 92}}),
    ):
        out = path.with_name(f"{path.stem}_map.{suffix}")
        fig.savefig(out, bbox_inches="tight", facecolor="white", **kwargs)
        outputs.append(str(out))
    plt.close(fig)
    return outputs
