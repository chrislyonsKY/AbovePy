# abovepy — Architectural Analysis & Refined Design

> Critical analysis of proposed architecture, refined design, and implementation recommendations
> Prepared for Chris Lyons | `chrislyonsKY/abovepy` | GPL-3.0
> 2026-03-12

---

## Resolved Decisions

| Decision | Resolution | Rationale |
|---|---|---|
| Package name | `abovepy` | Consistent with aboveR, AboveQ naming. `pip install abovepy`, `import abovepy` |
| License | GPL-3.0 | Government-funded work, copyleft intentional |
| GitHub location | `chrislyonsKY/abovepy` | Personal account, not org. Consistent with `chrislyonsKY/tissot` |
| STAC endpoint | Dynamic API (stac-fastapi) | Full search/filter server-side. Static catalog is 403 and lacks search |
| TiTiler | URL helpers in library + docker-compose in examples | Not a core dependency |
| STAC client library | `pystac-client` | Dynamic API supports it; CQL2 filtering, pagination |

---

## 1. Critical Analysis of Proposed Architecture

### What's Right

The high-level flow (STAC → pystac-client → abovepy → consumers) is fundamentally sound. Using pystac-client against a stac-fastapi deployment is the correct pattern. The separation of Python library and ArcGIS Pro toolbox is good.

### What's Wrong or Missing

#### Issue 1: The STAC API is more capable than assumed

The live API at `spved5ihrl.execute-api.us-west-2.amazonaws.com` supports:

- **CQL2 filtering** (basic-cql2, cql2-json, cql2-text)
- **Collection search** with filter, sort, free-text, fields, query
- **OGC API Features** with fields, query, sort, filter, and transactions
- **Item search** with fields, query, sort, filter

This means abovepy doesn't need to do much client-side filtering. The server handles spatial and temporal queries natively. Your library should leverage this rather than reimplementing it.

#### Issue 2: `stackstac` is the wrong dependency for this catalog

`stackstac` creates xarray DataArrays from STAC item collections — it's designed for satellite imagery (Sentinel-2, Landsat) where you want a 4D data cube (time × band × y × x). KyFromAbove data is fundamentally different:

- **DEMs** are single-band, single-epoch rasters on a tile grid — not time series
- **Orthoimagery** is RGB, single-epoch — not multi-temporal
- **LiDAR** is point cloud data — `stackstac` doesn't handle point clouds at all

`stackstac` adds `xarray`, `dask`, and `rioxarray` to your dependency tree for functionality you won't meaningfully use. **Drop it.** Use `rasterio` directly for COG reads and `rasterio.merge` for mosaicking. If someone wants xarray, they can wrap your output — don't force it.

#### Issue 3: The domain-split module design creates duplication

The proposed structure:

```
src/abovepy/
    client.py
    lidar.py
    dem.py
    imagery.py
    utils.py
```

This splits by *data domain*, but the STAC interaction pattern is identical for all three. `lidar.py`, `dem.py`, and `imagery.py` would all contain nearly identical code: query STAC → filter by collection → extract asset URLs. The only difference is which STAC collection IDs they target.

A better pattern: split by *operation*, not by domain. The collection (DEM vs ortho vs LiDAR) is a parameter, not a module.

#### Issue 4: No consideration of ArcGIS Pro's native STAC support

ArcGIS Pro 3.4+ has built-in STAC connectivity via the Explore STAC pane. Users can already connect to the KyFromAbove STAC API directly in Pro. This changes the value proposition of the ArcGIS toolbox.

The toolbox shouldn't just wrap STAC queries — Pro already does that. The toolbox should provide the **domain-specific workflows** that Pro's generic STAC browser doesn't: "give me the DEM for this county," "generate a hillshade from these tiles," "download Phase 3 ortho for my project area." These are opinionated, Kentucky-specific shortcuts.

#### Issue 5: No caching strategy

STAC queries over HTTP add latency. If someone calls `abovepy.search()` twice with the same bbox, they hit the API twice. For interactive use (Jupyter notebooks, ArcGIS Pro), this matters.

Consider a simple in-memory LRU cache for STAC responses, and an optional disk cache for tile indices.

#### Issue 6: TiTiler coupling is too tight

TiTiler is a deployment concern, not a library concern. The proposed architecture diagram shows it as a direct layer in the stack:

```
abovepy → TiTiler → Web maps
```

This implies abovepy depends on a running TiTiler instance. That's fragile — a Python library shouldn't require a web server to function. The correct pattern:

```
abovepy → COG URLs → (optionally) TiTiler → map tiles
```

abovepy's job is to find and return COG URLs. TiTiler can consume those URLs, but it's external to the library.

#### Issue 7: Missing error handling for API instability

The STAC API is hosted on AWS API Gateway + Lambda (the `spved5ihrl.execute-api` domain pattern). This is serverless — cold starts, rate limits, and occasional 5xx errors are expected. The library needs retry logic, timeout handling, and graceful degradation.

#### Issue 8: LiDAR requires fundamentally different handling

COGs and point clouds are different data types that need different read paths:

- **COGs (DEM, ortho)**: `rasterio` for windowed reads, streaming, mosaicking
- **COPC (LiDAR)**: `pdal` or `laspy` for point cloud access — completely different API surface

The proposed `lidar.py` can't share much code with `dem.py`. This is actually an argument *for* some domain separation — but at the read/processing level, not the STAC query level.

---

## 2. Design Question Responses

### Q1: API Design — Domain-Specific vs Generic STAC

**Recommendation: Thin domain layer over a generic STAC core.**

The public API should look like this:

```python
import abovepy

# Domain-specific convenience (what 80% of users want)
tiles = abovepy.search(bbox=(-84.5, 38.0, -84.3, 38.2), product="dem_phase3")

# The same thing, more explicit
tiles = abovepy.search(
    bbox=(-84.5, 38.0, -84.3, 38.2),
    collections=["ky-dem-phase3"],
    datetime="2022-01-01/.."
)

# Generic STAC escape hatch (what power users want)
client = abovepy.get_stac_client()
results = client.search(collections=["ky-dem-phase3"], bbox=bbox).item_collection()
```

**NOT** this:

```python
# Too fragmented — users need to know which module to import
abovepy.lidar.search()
abovepy.dem.load()
abovepy.imagery.stream()
```

The domain split should be in the *product* parameter, not in the module structure. One `search()` function with a `product=` argument is discoverable and simple. The product parameter maps to STAC collection IDs internally.

### Q2: TiTiler Integration

**Recommendation: Option C — URL helpers in library, docker-compose in examples, NOT a dependency.**

```python
# abovepy generates TiTiler-compatible URLs
tile_url = abovepy.titiler_url(
    cog_url="https://s3.amazonaws.com/kyfromabove/.../dem.tif",
    titiler_endpoint="https://titiler.example.com"
)
# Returns: "https://titiler.example.com/cog/tilejson.json?url=..."

# For local development, examples/docker-compose.yml spins up TiTiler
```

The URL helper belongs in a `titiler.py` module — 50 lines max. The docker-compose belongs in `examples/`, not at the repo root.

### Q3: ArcGIS Toolbox Integration

**Recommendation: Call the Python library directly. Not TiTiler.**

The ArcGIS Pro toolbox imports `abovepy` and delegates all STAC/S3 logic to it. The toolbox adds:

1. Native ArcGIS Pro parameter UI (GPExtent, ValueList dropdowns)
2. Progress messaging (`arcpy.SetProgressor`)
3. Map integration (`addDataFromPath`, group layers)
4. Domain-specific workflows (hillshade generation, county-based queries)

TiTiler makes no sense in the ArcGIS Pro context — Pro renders rasters natively. TiTiler is for web maps.

### Q4: Performance Considerations

**COG streaming**: Already handled by rasterio's `/vsicurl/` driver. KyFromAbove COGs are properly formatted (internal tiling, overviews). Windowed reads work out of the box.

**Large LiDAR datasets**: COPC files support spatial indexing — you can read a bbox without downloading the full file. Use `pdal` with a COPC reader and `bounds` filter. Make this an optional dependency (`pip install abovepy[lidar]`).

**Tile rendering**: Not abovepy's job. TiTiler or ArcGIS Pro handles this.

**Mosaicking**: For DEMs, use `rasterio.merge.merge()` for small areas (< 20 tiles). For large areas, build a VRT (`gdal.BuildVRT`) — zero-copy, instant. **Default to VRT.**

**Key pattern**: Lazy evaluation. `search()` returns metadata (tile index). `download()` fetches bytes. `read()` streams without download. Never fetch data the user didn't ask for.

### Q5: Kentucky-Specific vs General Framework

**Recommendation: Kentucky-specific. Do not generalize.**

This is a sharp-focus package for one dataset. The moment you try to generalize it into "a STAC client framework," you're competing with `pystac-client` (which already exists and is maintained by the STAC community). Your value is the domain knowledge: knowing which collections are DEMs vs ortho, knowing EPSG:3089, knowing the phase structure, knowing that Phase 1 point clouds are LAZ not COPC.

If someone wants a general STAC client for Python, they should use `pystac-client`. abovepy wraps it with Kentucky-specific opinions.

### Q6: Documentation Design

**Recommendation: B then C then A — workflow tutorials first, visual examples second, API reference auto-generated.**

The documentation that gets people to install your package is not the API reference — it's the workflow tutorial that shows them getting a hillshade of their county in 10 lines of Python. Lead with visual, concrete examples. Let `mkdocstrings` auto-generate the API reference from docstrings.

Priority:
1. **Getting Started** — install, search, download, visualize in under 2 minutes
2. **Workflow tutorials** — Frankfort DEM + hillshade, county-level ortho, LiDAR point cloud
3. **Visual examples** — embedded maps, rendered outputs, notebook screenshots
4. **API reference** — auto-generated from docstrings via mkdocstrings

---

## 3. Refined Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Applications                     │
│                                                         │
│  Jupyter    ArcGIS Pro     Python        Web Maps        │
│  Notebooks  Toolbox (.pyt) Scripts     (via TiTiler)    │
└────┬────────────┬──────────┬──────────────┬─────────────┘
     │            │          │              │
     └────────────┴──────────┘              │
                  │                         │
          ┌───────▼──────────┐     ┌────────▼────────┐
          │     abovepy      │     │    TiTiler       │
          │   (GPL-3.0)      │     │  (external)      │
          │                  │     │  COG tile server  │
          │  search()        │     └────────▲────────┘
          │  download()      │              │
          │  read()          │──── COG URLs ┘
          │  mosaic()        │
          │  info()          │
          │  titiler_url()   │
          └───────┬──────────┘
                  │
          ┌───────▼──────────┐
          │   pystac-client  │
          │   (STAC queries) │
          └───────┬──────────┘
                  │ HTTPS
          ┌───────▼──────────────────────────────────┐
          │  KyFromAbove STAC API (stac-fastapi)     │
          │  spved5ihrl.execute-api.us-west-2...     │
          │                                          │
          │  Collections:                            │
          │  ├── DEM Phase 1/2/3                     │
          │  ├── Ortho Phase 1/2/3                   │
          │  ├── Point Cloud Phase 1/2/3             │
          │  └── (discover actual IDs at runtime)    │
          └───────┬──────────────────────────────────┘
                  │
          ┌───────▼──────────┐
          │  s3://kyfromabove │
          │  (public bucket)  │
          │  COGs, COPC, LAZ  │
          └──────────────────┘
```

### Refined Repository Structure

```
abovepy/
│
├── src/abovepy/
│   ├── __init__.py              # Public API: search, download, read, mosaic, info
│   ├── _version.py              # Version string
│   ├── _constants.py            # STAC URL, S3 bucket, product→collection mapping
│   │
│   ├── client.py                # KyFromAboveClient class (main entry point)
│   ├── stac.py                  # STAC query wrapper (pystac-client + retry + cache)
│   ├── products.py              # Product registry: names, collection IDs, metadata
│   ├── download.py              # Download manager (httpx, progress, retry)
│   ├── mosaic.py                # VRT builder + rasterio.merge
│   ├── titiler.py               # TiTiler URL helpers (< 100 lines)
│   │
│   ├── io/                      # Format-specific read/write
│   │   ├── __init__.py
│   │   ├── cog.py               # COG reads via rasterio (/vsicurl/, windowed)
│   │   └── pointcloud.py        # COPC/LAZ reads via pdal/laspy (optional dep)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── crs.py               # EPSG:3089 ↔ EPSG:4326 conversion
│       ├── bbox.py              # Bbox validation, county bbox lookup
│       └── cache.py             # LRU cache for STAC responses
│
├── arcgis/
│   ├── AbovePro.pyt             # Python Toolbox entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── find_tiles.py        # Find KyFromAbove Tiles
│   │   ├── download_tiles.py    # Download Tiles
│   │   ├── download_and_load.py # Download + Add to Map
│   │   ├── dem_hillshade.py     # DEM → Hillshade workflow (domain-specific!)
│   │   └── preview_tile.py      # Stream COG preview
│   └── utils/
│       ├── __init__.py
│       └── parameters.py        # Product dropdown, extent conversion
│
├── examples/
│   ├── notebooks/
│   │   ├── 01_quickstart.ipynb           # Search + download + plot
│   │   ├── 02_frankfort_dem.ipynb        # Frankfort DEM + hillshade
│   │   ├── 03_lidar_workflow.ipynb       # Point cloud access
│   │   └── 04_titiler_webmap.ipynb       # TiTiler + leafmap
│   ├── scripts/
│   │   ├── frankfort_dem_workflow.py     # Standalone script version
│   │   └── county_ortho_download.py     # Download ortho for a county
│   ├── web/
│   │   └── titiler_map.html             # MapLibre + TiTiler example
│   └── docker-compose.yml               # Local TiTiler for development
│
├── docs/
│   ├── index.md                 # Landing page
│   ├── getting-started.md       # Install + first query in 2 minutes
│   ├── architecture.md          # Design decisions, dependency rationale
│   ├── tutorials/
│   │   ├── dem-hillshade.md     # Frankfort DEM workflow
│   │   ├── lidar-access.md      # Point cloud workflows
│   │   ├── titiler-maps.md      # Web visualization
│   │   └── arcgis-pro.md        # ArcGIS Pro toolbox guide
│   ├── api/                     # Auto-generated by mkdocstrings
│   │   └── reference.md
│   └── stac-collections.md      # KyFromAbove collection reference
│
├── tests/
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_stac.py
│   ├── test_products.py
│   ├── test_cog.py
│   └── test_titiler.py
│
├── CLAUDE.md                    # AI-dev context
├── .github/copilot-instructions.md
├── ai-dev/
│   ├── architecture.md
│   ├── spec.md
│   └── guardrails/
│       └── coding-standards.md
│
├── pyproject.toml
├── mkdocs.yml
├── LICENSE                      # GPL-3.0
├── README.md
└── CHANGELOG.md
```

### Key Changes from Proposed Structure

| Proposed | Refined | Rationale |
|---|---|---|
| `lidar.py`, `dem.py`, `imagery.py` | `products.py` + `io/cog.py` + `io/pointcloud.py` | Split by operation (query vs read), not by domain. Product is a parameter. |
| `utils.py` (single file) | `utils/` directory with `crs.py`, `bbox.py`, `cache.py` | Each utility has a clear responsibility |
| `arcgis/kyabove_tools.pyt` | `arcgis/AbovePro.pyt` + `tools/` directory | One tool per file, consistent with the scaffolding pattern |
| No caching | `utils/cache.py` | LRU cache for STAC responses to avoid redundant API calls |
| `stackstac` in deps | Removed | Wrong tool for this dataset — adds heavy deps for unused functionality |
| TiTiler as architecture layer | `titiler.py` URL helper + `examples/docker-compose.yml` | Library generates URLs; TiTiler is external |
| Flat examples/ | `examples/notebooks/`, `examples/scripts/`, `examples/web/` | Organized by format for discoverability |
| No `products.py` | `products.py` | Centralized product registry mapping names → collection IDs |

---

## 4. Product Registry Design

The `products.py` module is architecturally important. It maps human-readable product names to STAC collection IDs and holds per-product metadata. This is the single source of truth for "what data exists."

```python
# products.py — KyFromAbove product registry

from dataclasses import dataclass
from enum import Enum


class ProductType(Enum):
    """KyFromAbove product types."""
    DEM = "dem"
    ORTHO = "ortho"
    POINTCLOUD = "pointcloud"


@dataclass(frozen=True)
class Product:
    """A KyFromAbove data product."""
    key: str                    # e.g., "dem_phase3"
    display_name: str           # e.g., "DEM Phase 3 (2ft)"
    collection_id: str          # STAC collection ID (discovered from API)
    product_type: ProductType   # DEM, ORTHO, or POINTCLOUD
    resolution: str             # e.g., "2ft", "6in", "varies"
    format: str                 # "COG", "COPC", "LAZ"
    phase: int                  # 1, 2, or 3
    native_crs: str = "EPSG:3089"


# TODO: Collection IDs must be discovered from the live API.
# These are placeholders based on the STAC catalog description.
# Run: pystac_client.Client.open(STAC_URL).get_collections()
# to get the actual IDs before v0.1.0.
PRODUCTS = {
    "dem_phase1": Product(
        key="dem_phase1",
        display_name="DEM Phase 1 (5ft)",
        collection_id="TBD",  # DISCOVER FROM API
        product_type=ProductType.DEM,
        resolution="5ft",
        format="COG",
        phase=1,
    ),
    # ... etc
}
```

**Critical implementation note:** The STAC collection IDs in the API need to be discovered by actually querying `/collections`. I could not fetch that endpoint due to tool constraints, but this must be done before any code is written. The collection IDs are the contract between your library and the API — get them wrong and nothing works.

The first task before writing any library code:

```python
from pystac_client import Client

client = Client.open("https://spved5ihrl.execute-api.us-west-2.amazonaws.com/")
for collection in client.get_collections():
    print(f"{collection.id}: {collection.title}")
    print(f"  Extent: {collection.extent.spatial.bboxes}")
    print(f"  Description: {collection.description[:100]}")
```

---

## 5. Dependency Recommendations

### Required Dependencies

| Package | Purpose | Why This One |
|---|---|---|
| `pystac-client` | STAC API queries | The standard Python STAC client. Dynamic API requires it. |
| `rasterio` | COG reading, windowed reads, mosaicking | The standard Python raster I/O library. Wraps GDAL properly. |
| `geopandas` | GeoDataFrame returns for tile indices | Users expect DataFrame-like objects. Also handles CRS. |
| `pyproj` | CRS conversion (EPSG:4326 ↔ EPSG:3089) | Bundled with rasterio/geopandas anyway. |
| `httpx` | HTTP client for downloads | Async support, connection pooling, modern API. |
| `tqdm` | Download progress bars | Standard, lightweight. |

### Remove from Proposed Stack

| Package | Why Remove |
|---|---|
| `stackstac` | Wrong tool. KyFromAbove isn't time-series satellite imagery. Adds xarray, dask, rioxarray for nothing. |
| `numpy` | Don't list as a direct dependency — it's a transitive dep of rasterio and geopandas already. |

### Optional Dependencies

```toml
[project.optional-dependencies]
lidar = ["pdal>=3.2", "laspy>=2.5"]
titiler = ["titiler.core>=0.18"]
viz = ["leafmap>=0.30", "matplotlib>=3.8"]
all = ["abovepy[lidar,viz]"]
dev = ["pytest", "respx", "ruff", "mypy", "mkdocs-material", "mkdocstrings[python]"]
```

Note: `titiler` is NOT in `all`. It's a server deployment, not a library dependency. The `titiler.py` module in abovepy only generates URLs — it doesn't import titiler.

---

## 6. ArcGIS Pro Toolbox: Revised Value Proposition

Since ArcGIS Pro 3.4+ has native STAC support, the toolbox's value is NOT "connect to STAC" — Pro already does that. The value is domain-specific workflows.

### Tools to Build (Revised)

| Tool | Value Over Native Pro | Description |
|---|---|---|
| **Find KyFromAbove Tiles** | Preconfigured endpoint, product dropdown | Users don't need to know the STAC URL or collection IDs |
| **Download Tiles** | Progress bar, skip-existing, organized output | Pro's native STAC downloads are individual-tile |
| **DEM Hillshade** | Automated workflow | Search → download → mosaic → hillshade in one tool |
| **County Data Download** | Kentucky-specific convenience | Pick a county from dropdown, pick a product, download all tiles |
| **Preview (Stream)** | Same as native | Minor value — consider dropping |

The **DEM Hillshade** and **County Data Download** tools are what differentiate this from Pro's built-in STAC. No one else provides one-click "give me Pike County DEMs as a hillshade."

### County Lookup

A valuable Kentucky-specific feature: embed a county-name-to-bbox lookup table so users can say "Pike County" instead of drawing an extent.

```python
# utils/bbox.py
KY_COUNTIES = {
    "Adair": (-85.38, 37.00, -85.02, 37.21),
    "Allen": (-86.37, 36.63, -86.05, 36.87),
    # ... all 120 counties
    "Pike": (-82.73, 37.38, -82.05, 37.70),
    # ...
}
```

This is a tiny, static dataset. Ship it as package data.

---

## 7. MkDocs Configuration

```yaml
# mkdocs.yml
site_name: abovepy
site_description: KyFromAbove LiDAR, DEM, and orthoimagery access for Python
site_author: Chris Lyons
site_url: https://chrislyonsKY.github.io/abovepy/
repo_url: https://github.com/chrislyonsKY/abovepy
repo_name: chrislyonsKY/abovepy

theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: deep purple     # Tier 4 Processing — violet
      accent: deep purple
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: deep purple
      accent: deep purple
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
  features:
    - navigation.tabs
    - navigation.sections
    - content.code.copy
    - content.tabs.link

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: false
            docstring_style: numpy

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Tutorials:
    - DEM + Hillshade: tutorials/dem-hillshade.md
    - LiDAR Access: tutorials/lidar-access.md
    - Web Maps with TiTiler: tutorials/titiler-maps.md
    - ArcGIS Pro Toolbox: tutorials/arcgis-pro.md
  - Collections: stac-collections.md
  - Architecture: architecture.md
  - API Reference: api/reference.md

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - attr_list
  - md_in_html
```

---

## 8. Long-Term Maintainability Recommendations

### 1. Collection ID Discovery at Build Time

The STAC collection IDs could change if Ian Horn reorganizes the catalog. Don't hardcode them — discover them at first client initialization and cache. Include a `discover_collections()` function that users can call to refresh.

### 2. Pin pystac-client Carefully

pystac-client follows STAC API spec versions. If the KyFromAbove API upgrades (it's currently on v1.0.0-rc.1 for some conformance classes), your client version needs to match. Pin to a compatible range, not an exact version.

### 3. Integration Tests Against the Live API

Mark them with `@pytest.mark.integration` and run them on a schedule (weekly GitHub Action), not on every PR. The API could go down, change, or rate-limit — don't let that block PRs.

### 4. Version the Product Registry

When KyFromAbove adds new phases or products, you need a release. Make the product registry a data file (YAML or JSON) rather than Python code — it's easier for non-developers (including future you) to update.

### 5. CHANGELOG Discipline

GPL-3.0 projects benefit from clear changelogs. Users who can't upgrade need to know what version introduced a feature. Use Keep a Changelog format.

---

## 9. Weaknesses I Could Not Resolve

### Unknown Collection IDs

The most critical blocker: I could not fetch the `/collections` endpoint to discover actual STAC collection IDs. Every code example in this document uses placeholder IDs. **Before writing any code**, run:

```python
from pystac_client import Client
client = Client.open("https://spved5ihrl.execute-api.us-west-2.amazonaws.com/")
for c in client.get_collections():
    print(c.id, c.title)
```

The collection IDs determine the entire product registry and every query the library makes.

### API Stability

The API is on AWS API Gateway + Lambda (serverless). It could have cold starts, rate limits, or outages. The `conformsTo` list includes some `-rc.1` and `-rc.2` spec versions, suggesting the API may still be evolving. abovepy should handle this gracefully but can't prevent it.

### LiDAR Scope

Point cloud access via `pdal` is architecturally different enough that it could be a separate package. Consider shipping LiDAR support as a genuine optional feature, not a core promise, for v0.1.0. Get DEM and ortho right first.
