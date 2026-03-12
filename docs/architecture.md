# Architecture

Design decisions, dependency rationale, and how abovepy fits together.

## Overview

```
User Applications (Jupyter, ArcGIS Pro, scripts, web maps)
        │
        ▼
    abovepy  ──── COG URLs ───▶  TiTiler (external, optional)
        │
        ▼
  pystac-client
        │ HTTPS
        ▼
  KyFromAbove STAC API (stac-fastapi on AWS)
        │
        ▼
  s3://kyfromabove/ (public bucket: COGs, COPC, LAZ)
```

## Core Principles

### Product is a parameter, not a module

There are no `abovepy.dem`, `abovepy.lidar`, or `abovepy.imagery` modules. The STAC query pattern is identical for all products — the only difference is the collection ID. Product type is a parameter to `search()`.

```python
# One function, different products
abovepy.search(county="Pike", product="dem_phase3")
abovepy.search(county="Pike", product="ortho_phase3")
abovepy.search(county="Pike", product="laz_phase2")
```

### Kentucky-specific, not general-purpose

abovepy is not a STAC framework. It wraps [pystac-client](https://pystac-client.readthedocs.io/) with Kentucky-specific opinions: knowing which collections are DEMs vs orthos, knowing EPSG:3089, knowing the phase structure, providing county-name lookups. If you need a general STAC client, use pystac-client directly.

### Lazy evaluation

`search()` returns metadata (tile index). `download()` fetches bytes. `read()` streams without downloading. Data is never fetched until explicitly requested.

### VRT by default

Mosaics default to [VRT](https://gdal.org/drivers/raster/vrt.html) (Virtual Raster) — a zero-copy XML file that references the original tiles. GeoTIFF output is only created when the user explicitly requests a `.tif` path.

### No credentials required

The KyFromAbove S3 bucket is public. abovepy never prompts for or requires AWS credentials.

## Module Structure

```
src/abovepy/
├── __init__.py          # Public API (search, download, read, mosaic, info)
├── client.py            # KyFromAboveClient — main entry point
├── stac.py              # pystac-client wrapper + retry + cache
├── products.py          # Product registry: names → collection IDs
├── download.py          # Download manager (httpx, progress, retry)
├── mosaic.py            # VRT builder + rasterio.merge
├── titiler.py           # TiTiler URL helpers
├── io/
│   ├── cog.py           # COG reads via rasterio (/vsicurl/, windowed)
│   └── pointcloud.py    # COPC/LAZ reads (optional dep)
└── utils/
    ├── crs.py           # EPSG:3089 ↔ EPSG:4326
    ├── bbox.py          # Bbox validation + county lookup
    └── cache.py         # LRU cache for STAC responses
```

## Dependencies

### Required

| Package | Purpose |
|---|---|
| pystac-client | STAC API queries |
| rasterio | COG reading, windowed reads, mosaicking |
| geopandas | GeoDataFrame returns for tile indices |
| pyproj | CRS conversion (EPSG:4326 ↔ EPSG:3089) |
| httpx | HTTP client for downloads |
| tqdm | Download progress bars |
| shapely | Geometry operations |

### Optional

| Extra | Packages | Purpose |
|---|---|---|
| `lidar` | laspy | COPC/LAZ point cloud reads |
| `viz` | leafmap, matplotlib | Visualization |
| `s3` | boto3 | Direct S3 access |

### Why not...

| Package | Reason |
|---|---|
| `stackstac` | KyFromAbove is not time-series satellite data. stackstac adds xarray + dask for functionality we don't use. |
| `requests` | httpx provides async support, HTTP/2, and modern connection pooling. See [DL-001](https://github.com/chrislyonsKY/abovepy). |
| `titiler` (as dep) | abovepy generates TiTiler-compatible URLs. TiTiler itself is a server deployment, not a library dependency. |

## ArcGIS Pro Toolbox

The `arcgis/AbovePro.pyt` toolbox imports abovepy and adds:

- Native ArcGIS Pro parameter UI (extent widgets, dropdowns)
- Progress messaging via `arcpy.SetProgressor`
- Map integration (add layers directly to the project)
- Domain workflows: one-click hillshade, county-based downloads

The toolbox calls the Python library — it does not duplicate STAC logic.

## STAC API Capabilities

The KyFromAbove STAC API supports:

- **CQL2 filtering** (basic-cql2, cql2-json, cql2-text)
- **Collection search** with filter, sort, free-text, fields, query
- **OGC API Features** with fields, query, sort, filter
- **Item search** with fields, query, sort, filter

abovepy leverages server-side filtering rather than reimplementing it client-side.
