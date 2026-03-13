# Changelog

All notable changes to abovepy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] — 2026-03-12

### Added

- Product registry with 9 KyFromAbove collections (3 DEM, 3 ortho, 3 LiDAR)
- `search()` — find tiles by bbox or county name, returns GeoDataFrame
- `download()` — download tiles with progress bar, retry, and skip-existing
- `read()` — stream COG data via `/vsicurl/` with windowed reads by bbox
- `mosaic()` — build VRT from downloaded tiles
- `info()` — list available products and their metadata
- Kentucky county bbox lookup for all 120 counties
- STAC search via pystac-client with retry and TTL cache
- TiTiler URL helper functions (`cog_tile_url`, `cog_preview_url`, `cog_stats_url`)
- ArcGIS Pro Python Toolbox with 5 tools (Find Tiles, Download, Download & Load, Hillshade, County Download)
- Automatic CRS reprojection: bbox inputs in EPSG:4326, data in EPSG:3089
- Example scripts with generated output images (hillshade, REM, mine volume, ortho RGB, DEM comparison, search map)
- Jupyter notebooks (quickstart, DEM analysis, county explorer)
- Interactive web viewer (MapLibre GL JS + TiTiler)
- MkDocs documentation site with tutorials
- CI workflow (lint + test across Python 3.10–3.13, Linux/macOS/Windows)
- GitHub Pages deployment for docs
- PyPI publishing workflow

### Fixed

- `read()` now defaults bbox CRS to EPSG:4326 per project convention (was failing with empty window intersection when no CRS specified)
