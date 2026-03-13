# Changelog

All notable changes to abovepy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-03-13

### Added

- Custom exception hierarchy: `AbovepyError`, `SearchError`, `DownloadError`, `ReadError`, `MosaicError`, `ProductError`, `CountyError`, `BboxError`
- `py.typed` PEP 561 marker for typed package support
- Integration tests against the live STAC API (gated by `@pytest.mark.integration`)
- `mypy --strict` passes across all 17 source files
- mypy type checking added to CI workflow
- Full API reference docs: Client, Products, I/O, TiTiler, Utilities, Exceptions

### Changed

- Renamed internal modules `download.py` → `_download.py`, `mosaic.py` → `_mosaic.py` to fix import shadowing
- All custom exceptions replace raw `ValueError`/`RuntimeError` raises throughout the codebase
- `ProductError`, `CountyError`, `BboxError` inherit both `AbovepyError` and `ValueError` for backward compatibility
- Development status upgraded from Alpha to Production/Stable

### Fixed

- `abovepy.download` and `abovepy.mosaic` were module objects instead of callable functions due to import shadowing

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
