# Examples

Working examples for abovepy — KyFromAbove data access for Python.

## Scripts

| Script | Description |
|---|---|
| `scripts/quickstart.py` | Search, download, and mosaic DEM tiles |
| `scripts/frankfort_hillshade.py` | Full hillshade workflow with visualization |
| `scripts/county_ortho_download.py` | Download orthoimagery by county name |
| `scripts/stream_window.py` | Windowed read from a remote COG (no download) |
| `scripts/explore_products.py` | List all products and tile counts |
| `scripts/compare_dem_phases.py` | Compare DEM Phase 1 (5ft) vs Phase 3 (2ft) |
| `scripts/batch_county_search.py` | Search multiple counties, aggregate results |
| `scripts/inspect_remote_tile.py` | Inspect tile metadata without downloading |
| `scripts/ortho_rgb_extract.py` | Extract RGB bands from orthoimagery |
| `scripts/titiler_urls.py` | Generate TiTiler URLs for web maps |
| `scripts/export_search_results.py` | Export search results to GeoJSON/GPKG/CSV |
| `scripts/kentucky_river_rem.py` | Relative Elevation Model of the Kentucky River |
| `scripts/mine_volume_estimate.py` | Surface mine cut/fill volume estimation |

## Notebooks

| Notebook | Description |
|---|---|
| `notebooks/quickstart.ipynb` | Interactive walkthrough of core abovepy features |
| `notebooks/dem_analysis.ipynb` | DEM mosaic, hillshade, and elevation visualization |
| `notebooks/county_explorer.ipynb` | Explore all 120 Kentucky counties and their data |

## Web

| File | Description |
|---|---|
| `web/titiler_map.html` | Simple COG viewer via TiTiler |
| `web/kentucky_explorer.html` | Interactive KyFromAbove data explorer with layer controls |

## Docker

```bash
docker compose up -d    # Start local TiTiler at http://localhost:8000
```

## Running

```bash
pip install abovepy

# Basic example
python scripts/quickstart.py

# Hillshade (needs matplotlib)
pip install abovepy[viz]
python scripts/frankfort_hillshade.py

# REM analysis (needs scipy, shapely, matplotlib)
pip install abovepy[all]
python scripts/kentucky_river_rem.py

# Mine volume estimation (needs scipy, rasterio, geopandas)
python scripts/mine_volume_estimate.py

# County ortho download
python scripts/county_ortho_download.py --county Pike

# Notebooks
pip install jupyter
jupyter notebook notebooks/quickstart.ipynb
```
