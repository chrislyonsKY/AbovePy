# CLAUDE.md — abovepy

> KyFromAbove LiDAR, DEM, and orthoimagery data access for Python & ArcGIS Pro
> Python 3.10+ · PyPI · pystac-client · rasterio · geopandas · GPL-3.0
> Repo: chrislyonsKY/abovepy

Read this file completely before doing anything.
Then read `ai-dev/architecture.md` for full context.
Then read `ai-dev/guardrails/` for hard constraints.

---

## Workflow Protocol

When starting a new task:
1. Read CLAUDE.md (this file)
2. Read ai-dev/architecture.md
3. Read ai-dev/guardrails/ for constraints that override all other guidance
4. Check ai-dev/decisions/ for prior decisions that may affect your work

---

## Compatibility Matrix

| Component | Version |
|---|---|
| Python | 3.10+ |
| pystac-client | ≥0.7 |
| rasterio | ≥1.3 |
| geopandas | ≥0.14 |
| httpx | ≥0.25 |
| ArcGIS Pro (toolbox only) | 3.2+ |

---

## Project Structure

```
abovepy/
├── CLAUDE.md                         # This file
├── README.md
├── LICENSE                           # GPL-3.0
├── pyproject.toml
├── mkdocs.yml
├── CHANGELOG.md
│
├── src/abovepy/                      # Python package (PyPI)
│   ├── __init__.py                   # Public API: search, download, read, mosaic, info
│   ├── _version.py
│   ├── _constants.py                 # STAC URL, S3 bucket, CRS
│   ├── client.py                     # KyFromAboveClient — main entry point
│   ├── stac.py                       # pystac-client wrapper + retry + cache
│   ├── products.py                   # Product registry: names → collection IDs
│   ├── download.py                   # Download manager (httpx, progress, retry)
│   ├── mosaic.py                     # VRT builder + rasterio.merge
│   ├── titiler.py                    # TiTiler URL helpers (< 100 lines)
│   ├── io/
│   │   ├── __init__.py
│   │   ├── cog.py                    # COG reads via rasterio (/vsicurl/, windowed)
│   │   └── pointcloud.py            # COPC/LAZ reads via pdal/laspy (optional)
│   └── utils/
│       ├── __init__.py
│       ├── crs.py                    # EPSG:3089 ↔ EPSG:4326
│       ├── bbox.py                   # Bbox validation + KY county lookup
│       └── cache.py                  # LRU cache for STAC responses
│
├── arcgis/                           # ArcGIS Pro Python Toolbox
│   ├── AbovePro.pyt                  # Toolbox entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── find_tiles.py
│   │   ├── download_tiles.py
│   │   ├── download_and_load.py
│   │   ├── dem_hillshade.py          # DEM → Hillshade workflow
│   │   └── county_download.py        # Download by county name
│   └── utils/
│       ├── __init__.py
│       └── parameters.py
│
├── examples/
│   ├── notebooks/                    # Jupyter workflows
│   ├── scripts/                      # Standalone Python scripts
│   ├── web/                          # MapLibre + TiTiler HTML
│   └── docker-compose.yml            # Local TiTiler
│
├── docs/                             # MkDocs site
├── tests/
├── ai-dev/
└── .github/workflows/
```

---

## Critical Conventions

- **One search() function, product is a parameter.** NOT separate lidar.search(), dem.search().
- **Product keys map to STAC collection IDs internally.** Users say "dem_phase3", code queries "dem-phase3".
- **All bbox inputs accept EPSG:4326.** KyFromAbove native CRS is EPSG:3089. Convert transparently.
- **No credentials required.** S3 bucket is public. Never prompt for AWS keys.
- **Return types:** search() → GeoDataFrame, download() → list[Path], read() → (ndarray, profile).
- **Default to VRT for mosaics.** Only write GeoTIFF if the user explicitly requests output file.
- **LiDAR is optional.** pdal/laspy are heavy deps. Gate behind `pip install abovepy[lidar]`.
- **Lazy imports for optional deps.** Import pdal, laspy, boto3 inside functions, not at module level.
- **County lookup is a first-class feature.** search(county="Pike", product="dem_phase3") must work.

---

## STAC Infrastructure

- **STAC API:** `https://spved5ihrl.execute-api.us-west-2.amazonaws.com/`
- **Type:** stac-fastapi with CQL2, OGC API Features, collection search
- **S3 Bucket:** `s3://kyfromabove/` (public, us-west-2)
- **Tile Grid:** 5000×5000 foot grid, EPSG:3089

### Confirmed Collection IDs (from AWS Open Data Registry)

| Product Key | Collection ID | Format | Resolution |
|---|---|---|---|
| dem_phase1 | dem-phase1 | COG | 5ft |
| dem_phase2 | dem-phase2 | COG | 2ft |
| dem_phase3 | dem-phase3 | COG | 2ft |
| ortho_phase1 | orthos-phase1 | COG | 6in |
| ortho_phase2 | orthos-phase2 | COG | 6in |
| ortho_phase3 | orthos-phase3 | COG | 3in |
| laz_phase1 | laz-phase1 | LAZ | varies |
| laz_phase2 | laz-phase2 | COPC | varies |
| laz_phase3 | laz-phase3 | COPC (partial) | varies |

---

## What NOT To Do

- Do NOT split modules by data domain (no lidar.py, dem.py, imagery.py)
- Do NOT use stackstac — KyFromAbove is not time-series satellite data
- Do NOT require AWS credentials — the bucket is public
- Do NOT make TiTiler a dependency — generate URLs only
- Do NOT hardcode collection IDs without a fallback discovery mechanism
- Do NOT use `requests` — use `httpx`
- Do NOT download full tiles when a bbox window is requested
- Do NOT import optional deps (pdal, laspy, boto3) at module level
