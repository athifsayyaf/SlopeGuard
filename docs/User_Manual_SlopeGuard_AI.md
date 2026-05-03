# SlopeGuard AI User Manual

## 1. What SlopeGuard AI Does

SlopeGuard AI is a desktop-style landslide monitoring and susceptibility mapping prototype. It guides the user from DEM, Sentinel-2, InSAR, and landslide inventory data toward terrain derivatives, raster previews, machine-learning experiment setup, interpretation, and report outputs.

The current version is a local software prototype. It starts a Python backend and opens the interface in a standalone app-style window.

## 2. How To Open The Software

Use:

```text
SlopeGuard_AI.exe
```

The executable starts the backend automatically and opens SlopeGuard AI as a desktop-style application window. You do not need to manually type `http://127.0.0.1:8765`.

If the app does not open, check:

```text
slideagent-ai\logs\desktop_backend.log
slideagent-ai\logs\desktop_backend_error.log
```

## 3. Main Interface

The interface follows a GIS-style layout inspired by QGIS, ArcGIS Pro, ENVI, Font-GIS icon language, and CartoColor map palettes.

- Left sidebar: workflow modules.
- Top bar: active workflow, layer visibility, raster preview opener.
- Center map canvas: raster/map preview.
- Right panel: parameters for the selected tool.
- Bottom panel: minimal status, progress, details, and output files.

## 4. Main Modules

### Project

Use this to set:

- Project name.
- Study area name.
- CRS.
- Resolution.
- Output folder.
- AOI vector.

The configuration is saved as:

```text
project_config.json
```

### DEM

Input:

- DEM GeoTIFF.

Tools:

- Slope.
- Aspect.
- TWI.
- Hillshade.

Outputs:

```text
slope.tif
aspect.tif
twi.tif
hillshade.tif
*_map.png
*_map.jpg
```

If an output already exists or is locked, the software saves a numbered file such as:

```text
slope_01.tif
slope_01_map.png
slope_01_map.jpg
```

### Sentinel-2

Inputs:

- Red band.
- NIR band.
- Blue band.
- SWIR band.

Tools:

- NDVI.
- EVI.
- Bare Soil Index.
- NDWI.
- LULC placeholder workflow.

Outputs:

```text
ndvi.tif
evi.tif
bsi.tif
ndwi.tif
*_map.png
*_map.jpg
```

### Sentinel-1 / InSAR

Use this for preprocessed InSAR rasters.

Inputs:

- LOS velocity raster.
- Mean coherence raster.

Outputs:

```text
los_velocity.tif
mean_coherence.tif
*_map.png
*_map.jpg
```

### Landslide Inventory

Inputs:

- Shapefile, GeoJSON, CSV, or raster inventory.
- Reference raster grid.

Output:

```text
landslide_mask.tif
```

Mask values:

- `1` = landslide.
- `0` = non-landslide.

### Stack Builder

Combines multiple raster layers into an analysis-ready stack.

Inputs include:

- Slope.
- Aspect.
- TWI.
- NDVI.
- LOS velocity.
- Coherence.
- Landslide mask.

Expected outputs:

```text
feature_stack.tif
feature_table.csv
```

### ML Model

The ML module is designed for landslide susceptibility modelling.

Required experiment:

- Run once without InSAR layers.
- Run once with InSAR layers.

Metrics:

- AUROC.
- F1-score.
- Precision.
- Recall.
- Confusion matrix.

Expected outputs:

```text
susceptibility_without_insar.tif
susceptibility_with_insar.tif
model_comparison.csv
feature_importance.png
shap_summary.png
```

### Interpretation

This module helps summarize:

- Which features influenced susceptibility.
- Whether InSAR improved model results.
- Whether high-risk zones match geomorphology.
- Limitations and uncertainty.
- Suggested next steps.

### Report

Generates report-style outputs:

- PDF report.
- One-slide PDF summary.
- Methodology summary.
- Metrics table.
- Interpretation draft.

## 5. Viewing TIFF Outputs

GeoTIFF files are scientific raster outputs. The software also creates PNG/JPG previews so they can be viewed inside the app.

To open an existing TIFF:

1. Copy the full TIFF path.
2. Paste it into the top preview box.
3. Click `Open`.

The software creates PNG/JPG previews and displays the image in the map canvas.

## 6. Output Folder

Default outputs are saved under:

```text
slideagent-ai\outputs
```

Job logs are saved under:

```text
slideagent-ai\logs
```

## 7. Troubleshooting

### The app window opens but says connection refused

The backend did not start. Run:

```powershell
cd "E:\Lenovo_path_moved\moved_due_to_storageissue\New project\slideagent-ai"
python backend\server.py
```

Then launch the EXE again.

### Permission denied for `.ovr`

This happens when Windows locks a raster overview file. SlopeGuard AI avoids overwriting locked files by creating numbered outputs.

### Missing Python package

Install requirements:

```powershell
cd "E:\Lenovo_path_moved\moved_due_to_storageissue\New project\slideagent-ai"
python -m pip install -r requirements.txt
```

### The desktop EXE cannot find the app folder

Keep the EXE in the delivery folder next to the original `slideagent-ai` folder, or copy the app folder beside the EXE as:

```text
SlopeGuard_AI_App
```

## 8. Design Notes

SlopeGuard AI uses:

- GIS-style icons inspired by Font-GIS.
- Map-friendly color ramps inspired by CartoColor.
- Green, white, and earth tones to match landslide, terrain, and hazard mapping.

## 9. Recommended Workflow For Joshimath / Kuwari

1. Set project CRS to `EPSG:32644`.
2. Load DEM.
3. Create slope, aspect, TWI, and hillshade.
4. Load Sentinel-2 bands or existing NDVI.
5. Register InSAR velocity/coherence rasters.
6. Rasterize landslide inventory.
7. Build feature stack.
8. Run ML comparison with and without InSAR.
9. Generate susceptibility map and report.

