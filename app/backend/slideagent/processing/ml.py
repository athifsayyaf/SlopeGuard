from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import csv
import json

from .common import ensure_output, write_manifest


def run_stack_builder(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    output = ensure_output(params, Path("outputs") / "stack")
    layers = params.get("layers", [])
    if not layers:
        raise ValueError("No layers were provided for stack building.")
    progress(30, "Validating layer list")
    table = output / "feature_table.csv"
    with table.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["layer_name", "path", "role"])
        for layer in layers:
            writer.writerow([layer.get("name"), layer.get("path"), layer.get("role", "predictor")])
    progress(70, "Writing stack manifest")
    manifest = write_manifest(output, "feature_stack", {"layers": layers, "note": "Use processing/ml_pipeline.py for full raster alignment and sampling."})
    return [str(table), manifest]


def run_model_stub(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    output = ensure_output(params, Path("outputs") / "ml")
    progress(20, "Preparing experiment definition")
    comparison = output / "model_comparison.csv"
    comparison.write_text(
        "experiment,features,AUROC,F1,precision,recall\n"
        "without_insar,\"slope,aspect,twi,ndvi\",,,,\n"
        "with_insar,\"slope,aspect,twi,ndvi,los_velocity,coherence\",,,,\n",
        encoding="utf-8",
    )
    progress(70, "Writing model run plan")
    run_plan = {
        "model": params.get("model", "Random Forest"),
        "spatial_cv": True,
        "required_outputs": [
            "susceptibility_without_insar.tif",
            "susceptibility_with_insar.tif",
            "feature_importance.png",
            "shap_summary.png",
        ],
    }
    plan = output / "model_run_plan.json"
    plan.write_text(json.dumps(run_plan, indent=2), encoding="utf-8")
    return [str(comparison), str(plan)]

