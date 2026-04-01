# Changelog

All notable changes to abovepy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [2.1.3] — 2026-04-01

### Added

- **Codecov coverage reporting** — branch coverage uploaded to Codecov on every
  CI run with 75% minimum threshold enforced. Coverage badge added to README.
- **Cloud-native geospatial format references** — inline validation examples
  (rio-cogeo, pdal) in each collection section of the docs, plus links to the
  CNG Formats Guide, STAC Best Practices, COPC spec, and GeoParquet distribution guide.
- **Pre-commit hooks** — ruff lint + format enforced locally via `.pre-commit-config.yaml`
- **CODEOWNERS** — automatic PR review assignment
- **Makefile** — `make lint`, `test`, `typecheck`, `coverage`, `docs`, `build`, `clean`

### Changed

- **PyPI publishing hardened** — switched to OIDC trusted publishing (removed
  API token), added TestPyPI staging with smoke test before production publish,
  gated publish workflow on lint + test passing, added wheel content verification
  (py.typed, _version.py)
- **Single-source versioning** — `pyproject.toml` now reads version dynamically
  from `_version.py` via `[tool.hatch.version]`, eliminating version drift
- **CI improvements** — pip caching across all workflows, Codecov upload with
  branch coverage, integration tests now install all optional extras (`.[dev,all]`)
- **Docs workflow** — path filter added so docs only rebuild when docs, source,
  notebooks, or mkdocs config change
- **Broader ruff rules** — added S (security/bandit), PT (pytest), RUF, C4
  (comprehensions) rule sets with targeted per-file ignores for tests
- **pytest defaults** — `addopts` with `--strict-markers -ra` and marker filtering
  configured in `pyproject.toml`

### Fixed

- Operator precedence bug in `validate_s3_bucket()` — chained `and`/`or`
  now parenthesized correctly (RUF021)

## [2.1.2] — 2026-03-31

### Added

- **STL export for 3D printing** — `to_stl(data, profile, output)` converts a DEM
  into a watertight binary STL mesh with configurable vertical exaggeration, base
  height, and decimation. Ready for Bambu Studio, Cura, PrusaSlicer, or Blender.
  No external dependencies — pure numpy + struct.
- **QGIS auto-load with hillshade** — Download tool now auto-adds rasters to the
  QGIS project and applies hillshade symbology to DEM products. Controlled by
  "Load downloaded tiles into project" and "Apply hillshade styling" checkboxes.

## [2.1.1] — 2026-03-31

### Added

- **LandXML surface export** — `to_landxml(data, profile, output)` triangulates a
  DEM into a TIN surface and writes LandXML 1.2 XML. Importable by Civil 3D,
  Carlson, and OpenRoads Designer. Supports decimation for file size control,
  nodata masking, and automatic Imperial/Metric units based on CRS.
  Requires `pip install abovepy[analysis]` (scipy).
- Example script: `landxml_export.py` (DEM to LandXML for CAD import)

## [2.1.0] — 2026-03-31

### Added

- **QGIS plugin (AboveQGIS)** — Processing toolbox provider with 4 tools: Search
  Tiles, Download Tiles, Mosaic Tiles, Generate Hillshade Tile URL. County dropdown
  (all 120 counties), product selector, map extent support. Auto-installs abovepy
  dependency on first run. Available under Plugins menu and Processing Toolbox.
- **CLI `--buffer-feet` flag** on search, download, and estimate subcommands —
  uses EPSG:3089 projection for accurate feet-based spatial queries
- **CLI `--format provenance`** on search — outputs full provenance metadata as JSON
- **CLI automatic validation** — table output now runs `validate()` and prints
  warnings to stderr before results
- **`buffer_feet()` and `corridor_buffer()` exported at top level** —
  `import abovepy; abovepy.buffer_feet(point, 500)` works directly
- **Security: path traversal protection** — `sanitize_filename()` and
  `validate_path_segment()` prevent malicious filenames and collection IDs
  from escaping the output directory during downloads
- **Security: URL path injection prevention** — `validate_path_segment()` on
  all `item_id`, `search_id` parameters in TiTiler URL builders;
  `validate_image_format()` whitelists `fmt` to known image types
- **Security: S3 bucket name validation** — `validate_s3_bucket()` enforces
  AWS bucket naming rules in COPC reader and COG reader S3 URI conversion
- **Security: `json.dumps()` for algorithm params** — replaces f-string
  interpolation in TiTiler hillshade/slope/contour URL builders
- Example scripts: `engineering_geometry.py` (State Plane Northing/Easting
  workflows), `provenance_and_validation.py` (QA for deliverables),
  `cli_workflows.sh` (common CLI patterns)

### Changed

- **Security: `validate_remote_url()` now raises `ValueError`** for untrusted
  hosts instead of logging a warning. Pass `allow_untrusted=True` to opt in
  to untrusted hosts (logs warning instead of raising).
- Default concurrent download workers increased from 4 to 8
- Download chunk size increased from 64 KB to 256 KB
- CI: `github/codeql-action` pinned to commit SHA
- CI: `actions/dependency-review-action` pinned to commit SHA (v4.9.0)
- `search()` docstring updated to document `buffer_feet` parameter
- README: new sections for feet-based search, corridor search, validation,
  provenance, Kentucky Engineering Geometry, CLI usage, QGIS plugin badge

## [2.0.0] — 2026-03-30

### Breaking Changes

- **`search()` now returns `SearchResult`** instead of a bare `GeoDataFrame`.
  Access the raw GeoDataFrame via `.tiles` or `.to_geodataframe()`.
  `download()` and `mosaic()` accept both `SearchResult` and `GeoDataFrame`.

### Added

- **`SearchResult` workflow object** — chainable result from `search()` with
  `.download()`, `.preview()`, `.map()`, `.mosaic()`, `.estimate_size()`,
  `.to_geoparquet()`, `.to_geojson()`, `.compare()`, `.filter_by_bbox()`,
  `.head()`, and rich Jupyter display via `_repr_html_()`
- **Enhanced search parameters** — `intersects` (GeoJSON or Shapely geometry),
  `filter` (CQL2), `sortby`, `ids`, `fields` passed through to STAC API
- **Kentucky area selectors** — `point=(lon, lat)` + `buffer_miles=` for
  circular searches, `geometry=` for any Shapely geometry
- **Concurrent downloads** — `max_workers` parameter (default 4) uses
  `ThreadPoolExecutor` for parallel tile downloads
- **Resumable downloads** — `.part` file protocol with HTTP Range headers;
  interrupted downloads resume from where they left off
- **Cloud-native COPC reads** — `read_copc()` uses `laspy.CopcReader` for
  spatial and LOD queries over HTTP without downloading entire files
- **CLI `estimate` subcommand** — `abovepy estimate --county Pike` shows
  tile count and estimated download size
- **CLI improvements** — `--point`, `--buffer`, `--ids`, `--sortby` on search;
  `--workers`, `--no-resume` on download; `--open` on preview; summary lines
  on search and download output
- **Size estimation** — `Product.avg_tile_size_mb` field enables download
  size predictions per product type
- Community health documents: SUPPORT.md, MAINTAINERS.md, DEVELOPMENT.md,
  GOVERNANCE.md, RESPONSIBLE_USE.md, DISCLAIMER.md, PRIVACY.md, ATTRIBUTION.md

### Changed

- Download chunk size increased from 8 KB to 64 KB
- Cache key generation supports new search parameters
- `BboxError` message updated to list all available area selectors
- `__main__.py` now delegates to CLI subcommand parser

## [1.1.0] — 2026-03-16

### Added

- **Terrain analysis** — server-side DEM processing via TiTiler-pgSTAC algorithms:
  `hillshade_tile_url()`, `slope_tile_url()`, `contour_tile_url()`, `terrain_rgb_tile_url()`
- **pgSTAC search registration** — `register_search()` creates persistent virtual mosaics
  via `/searches/register`; `search_tile_url()`, `search_map_url()`, `search_bbox_url()`,
  `search_info_url()` build URLs from the returned hash
- **Visualization helpers** — `tile_url()` and `preview_url()` smart dispatchers that
  accept product + bbox/county; `show()` renders interactive leafmap in Jupyter notebooks
  with optional terrain algorithm overlay
- **Oblique imagery** — 4 new products (`oblique_phase3_bwd/fwd/left/right`) with
  `OBLIQUE` product type; `search_obliques()` and `list_oblique_seasons()` for S3-based
  discovery until the STAC collection is published
- `s3_prefix` field on `Product` dataclass for products with direct S3 access paths
- New example scripts: `explore_obliques.py`, `oblique_site_inspection.py`

### Changed

- All example visualizations updated for **WCAG 2.1 AA** compliance:
  - Colorblind-safe palettes (`cividis`, `inferno`, `viridis`, Paul Tol qualitative)
  - Replaced `hsv` (aspect), `RdBu` (change detection), `Reds` (mine volume)
  - Text contrast ratios meet AA minimums (4.5:1 normal, 3:1 large)
  - Dark theme web viewer text upgraded from `#888`/`#aaa` to `#b0b0b0`/`#c0c0c0`
- `titiler_urls.py` example expanded to demonstrate pgSTAC, terrain, viz, and search features
- README updated with terrain analysis, oblique imagery, and visualization sections

## [1.0.1] — 2026-03-13

### Added

- `list_counties()` exposed in top-level API for discoverability
- `Product.__repr__()` for cleaner REPL output
- `python -m abovepy` CLI entrypoint — prints version, products, and STAC API URL
- `bbox_intersects_kentucky()` CRS utility for early out-of-bounds warnings
- `cog_info_url()` and `cog_bounds_url()` TiTiler URL helpers
- CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md community health files
- GitHub issue templates (bug report + feature request forms)
- Pull request template
- Dependabot for pip and GitHub Actions updates
- Stale issue/PR bot workflow

### Changed

- CI: separated lint into dedicated job (runs once, not 12x across matrix)
- CI: added `ruff format --check` and `workflow_dispatch` trigger
- CI: `fail-fast: false` so all matrix jobs complete
- PyPI publish workflow upgraded to OIDC trusted publishing
- TTLCache uses `collections.deque` for O(1) eviction (was O(n) with list)
- Removed `ai-dev/` and `CLAUDE.md` from version control

### Fixed

- Download: raises `DownloadError` instead of bare exception after retry exhaustion
- Download: cleans up partial files on failure
- STAC retry: docstring now says `SearchError` (was `RuntimeError`)
- STAC retry: exception chaining with `raise ... from` for better tracebacks

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
