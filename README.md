# SlopeGuard AI

SlopeGuard AI is a desktop-style geospatial software prototype for landslide monitoring and landslide susceptibility mapping. It guides a user from DEM, Sentinel-2, Sentinel-1/InSAR, and landslide inventory inputs toward terrain derivatives, raster previews, feature-stack preparation, model comparison, interpretation, and report outputs.

## Quick Start For Windows

Use the packaged launcher:

```text
release/windows/SlopeGuard_AI.exe
```

Keep these support files beside the EXE:

```text
release/windows/SlopeGuard_AI.dll
release/windows/SlopeGuard_AI.deps.json
release/windows/SlopeGuard_AI.runtimeconfig.json
```

Keep the repository folder structure intact. The EXE looks for the application source in:

```text
app/
```

The EXE starts the local Python backend and opens SlopeGuard AI in a standalone app-style window.

## Run From Source

```powershell
cd app
python -m pip install -r requirements.txt
python backend\server.py
```

Then, in another terminal:

```powershell
.\SlopeGuard_AI_Desktop.bat
```

## Repository Structure

```text
app/                 Source application
  backend/           Local Python backend and geospatial processing modules
  frontend/          HTML/CSS/JS interface and assets
  examples/          Kuwari/Joshimath example workflow files
  tests/             Smoke tests using synthetic sample data
docs/                User manual and package notes
release/windows/     Windows launcher EXE and required support files
tools/               Launcher source and icon-generation utility
```

## Main Features

- DEM processing: slope, aspect, TWI, hillshade
- Sentinel-2 indices: NDVI, EVI, Bare Soil Index, NDWI, simple LULC
- InSAR layer registration: LOS velocity and coherence
- Landslide inventory rasterization
- TIFF visualization through PNG/JPG quicklooks
- Stack Builder scaffold
- ML model comparison scaffold: without InSAR vs with InSAR
- Interpretation and PDF report generator
- GIS-style icons and CartoColor-inspired map palettes

## Requirements

Python packages are listed in:

```text
app/requirements.txt
```

Important packages:

- rasterio
- geopandas
- numpy
- pandas
- scikit-learn
- xgboost
- shap
- matplotlib
- reportlab

The Windows launcher requires .NET 6 Desktop Runtime if it is not already installed.

## Testing

Run the smoke test:

```powershell
cd app
python .\tests\smoke_test_features.py
```

The test creates synthetic sample data and checks:

- DEM slope/aspect/TWI/hillshade
- Sentinel-2 NDVI/EVI/BSI/NDWI/LULC
- InSAR registration
- Inventory rasterization
- Preview generation
- Stack Builder
- ML scaffold
- Interpretation
- Report generator

## Manuals

Manuals are available in:

```text
docs/User_Manual_SlopeGuard_AI.md
docs/User_Manual_SlopeGuard_AI.html
```

## Design References

- Font-GIS: https://github.com/Viglino/font-gis
- CartoColor: https://github.com/CartoDB/CartoColor

SlopeGuard AI uses local icons and local color ramps inspired by those projects, so the app remains offline-friendly.
