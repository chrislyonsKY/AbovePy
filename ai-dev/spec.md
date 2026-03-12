# abovepy — Spec

> Requirements, acceptance criteria, and constraints

---

## Overview

`abovepy` provides Python developers with simple, Pythonic access to Kentucky's KyFromAbove program — statewide LiDAR point clouds, DEMs, and orthoimagery. The data is publicly hosted on S3 with a STAC API for discovery. This package eliminates the need to manually navigate the STAC browser or write raw API calls.

---

## User Stories

### US-01: Find tiles covering my study area
**As a** Python developer working with Kentucky spatial data,
**I want to** find all KyFromAbove tiles that intersect my bounding box,
**So that** I can see what data is available before downloading.

**Acceptance Criteria:**
- `find_tiles(bbox, product)` returns a GeoDataFrame with tile metadata
- Bbox accepts EPSG:4326 (default) or any CRS with explicit `crs=` parameter
- Results include: tile_id, product, geometry, download_url, file_size, datetime
- Empty result returns empty GeoDataFrame (not None, not exception)

### US-02: Download tiles to local directory
**As a** data analyst,
**I want to** download specific tiles to a local directory with progress feedback,
**So that** I can work with them offline and track download progress.

**Acceptance Criteria:**
- `download(tiles_gdf, output_dir)` downloads all tiles in the GeoDataFrame
- Progress bar shown via tqdm
- Existing files are skipped unless `overwrite=True`
- Returns `list[Path]` of downloaded file paths
- Failed downloads retry 3x with exponential backoff
- Partial downloads are cleaned up on failure

### US-03: Stream raster data without downloading
**As a** cloud-native developer,
**I want to** read a specific bbox from a remote COG without downloading the full tile,
**So that** I only transfer the data I actually need.

**Acceptance Criteria:**
- `read(url, bbox=...)` performs a windowed read via `/vsicurl/`
- Returns numpy array with rasterio profile metadata
- Works with both S3 URIs and HTTPS URLs
- No local file created

### US-04: Mosaic multiple tiles
**As a** spatial analyst,
**I want to** combine multiple downloaded tiles into a single raster,
**So that** I have a seamless dataset covering my full study area.

**Acceptance Criteria:**
- `mosaic(paths)` creates a VRT by default (zero-copy)
- `mosaic(paths, output="merged.tif")` writes a merged GeoTIFF
- Optional `bbox=` clips to exact study area
- Optional `crs=` reprojects output

### US-05: Inspect available products
**As a** new user,
**I want to** see what KyFromAbove products are available and their metadata,
**So that** I can choose the right product for my analysis.

**Acceptance Criteria:**
- `info()` (no args) returns a table of all available products
- `info(product)` returns detailed metadata for one product
- `info(url)` returns metadata for a specific remote tile

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Python version | 3.10+ |
| Install size | < 50KB (excluding dependencies) |
| First query latency | < 2s for STAC search |
| Download throughput | Saturate available bandwidth |
| Zero-config | Must work with no credentials, no config files |
| Offline capability | Downloaded tiles work offline; STAC queries require network |

---

## Constraints

- **No AWS credentials required**: The S3 bucket is public. Never prompt for or require credentials.
- **EPSG:3089 is the native CRS**: All KyFromAbove data is in Kentucky Single Zone (US feet). The library accepts 4326 input and converts internally.
- **STAC API is the source of truth**: Never hardcode tile indices or URLs. Always discover via STAC.
- **Rasterio is the raster backend**: Don't introduce GDAL bindings directly. Rasterio wraps GDAL properly for Python.
- **No ArcPy dependency**: This is a general-purpose PyPI package. ArcPy integration lives in the sibling `abovepro` toolbox.

---

## Test Strategy

| Test Type | Scope | Infra |
|---|---|---|
| Unit tests | Bbox conversion, CRS handling, URL construction, product mapping | pytest, no network |
| Integration tests | STAC queries against live API, single tile download | pytest, requires network, marked `@pytest.mark.integration` |
| Smoke tests | Full workflow: find → download → mosaic | pytest, requires network + disk, marked `@pytest.mark.slow` |

Mock the STAC API and S3 for unit tests using `respx` (httpx mock) and `moto` (S3 mock).
