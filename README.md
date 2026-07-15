
<p align="center">
  <a href="https://pypi.org/project/abovepy/"><img src="https://img.shields.io/pypi/v/abovepy?color=8B5CF6&style=flat-square" alt="PyPI version"></a>
  <a href="https://pypi.org/project/abovepy/"><img src="https://img.shields.io/pypi/pyversions/abovepy?style=flat-square" alt="Python versions"></a>
  <a href="https://github.com/chrislyonsKY/AbovePy/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/chrislyonsKY/AbovePy/ci.yml?branch=main&style=flat-square&label=CI" alt="CI"></a>
  <a href="https://github.com/chrislyonsKY/AbovePy/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square" alt="License"></a>
  <a href="https://chrislyonsKY.github.io/AbovePy/"><img src="https://img.shields.io/badge/docs-mkdocs-8B5CF6?style=flat-square" alt="Docs"></a>
  <a href="https://plugins.qgis.org/plugins/aboveqgis/"><img src="https://img.shields.io/badge/QGIS-AboveQGIS-93b023?style=flat-square&logo=qgis&logoColor=white" alt="QGIS Plugin"></a>
  <a href="https://codecov.io/gh/chrislyonsKY/AbovePy"><img src="https://img.shields.io/codecov/c/github/chrislyonsKY/AbovePy?style=flat-square&label=coverage" alt="Coverage"></a>
  <a href="https://app.codacy.com/gh/chrislyonsKY/AbovePy/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade"><img src="https://app.codacy.com/project/badge/Grade/a79be242ecde4371a7172f61f9ccf80d"/></a>

</p>

# abovepy

**KyFromAbove LiDAR, DEM, orthoimagery, and oblique imagery data access for Python.**

Kentucky's [KyFromAbove](https://kyfromabove.ky.gov/) program provides statewide 2ft DEMs, 3-inch orthoimagery, 3-inch oblique imagery, and COPC LiDAR point clouds — all publicly available on S3 with a STAC API for discovery. `abovepy` gives you Pythonic access to all of it, plus server-side terrain analysis via TiTiler. No credentials required.
## Install

```bash
pip install abovepy
```

Optional extras:

```bash
pip install abovepy[lidar]    # COPC/LAZ point cloud support
pip install abovepy[viz]      # leafmap + matplotlib visualization
pip install abovepy[all]      # Everything
```

## Quick Start

### Search by county name

```python
import abovepy

# Find DEM tiles covering Franklin County
tiles = abovepy.search(county="Franklin", product="dem_phase3")
print(tiles)
```

### Search by bounding box

```python
tiles = abovepy.search(
    bbox=(-84.9, 38.15, -84.8, 38.25),
    product="dem_phase3"
)
```

### Download tiles

```python
paths = abovepy.download(tiles, output_dir="./data")
```

### Mosaic into a single raster

```python
vrt = abovepy.mosaic(paths, output="frankfort.vrt")
```

### Search by point with feet-based buffer

```python
# 500-foot radius around a point (uses EPSG:3089 for accurate measurement)
tiles = abovepy.search(
    point=(-84.87, 38.20),
    buffer_feet=500,
    product="dem_phase3"
)
```

### Corridor search

```python
from shapely.geometry import LineString

# Search along a road centerline with 200ft buffer on each side
road = LineString([(-84.90, 38.20), (-84.85, 38.19), (-84.82, 38.21)])
tiles = abovepy.search(geometry=road, buffer_feet=200, product="ortho_phase3")
```

### Stream without downloading

```python
data, profile = abovepy.read(
    tiles.iloc[0].asset_url,
    bbox=(-84.85, 38.18, -84.82, 38.21)
)
```

### Data quality validation

```python
result = abovepy.search(county="Pike", product="dem_phase3")

# Check for data quality issues
warnings = result.validate()
for w in warnings:
    print(f"Warning: {w}")
# Warning: 3 tile(s) (12%) have no acquisition date metadata.
```

### Provenance metadata

```python
# Generate source documentation for deliverables
prov = result.provenance()
print(prov["source_program"])       # KyFromAbove
print(prov["acquisition_period"])   # 2022-2025
print(prov["native_crs"])           # EPSG:3089
print(prov["tile_count"])           # 42
print(prov["estimated_size_mb"])    # 210.0
```

### Explore available products

```python
print(abovepy.info())
#   product        display_name                format  resolution  phase  crs
#   dem_phase1     DEM Phase 1 (5ft)           COG     5ft         1      EPSG:3089
#   dem_phase2     DEM Phase 2 (2ft)           COG     2ft         2      EPSG:3089
#   dem_phase3     DEM Phase 3 (2ft)           COG     2ft         3      EPSG:3089
#   ortho_phase1   Orthoimagery Phase 1 ...    COG     6in         1      EPSG:3089
#   ...plus oblique products
```

### Terrain analysis (server-side)

Generate hillshade, slope, and contour tiles directly from the TiTiler-pgSTAC server — no downloads needed:

```python
from abovepy.titiler import hillshade_tile_url, slope_tile_url, contour_tile_url

# Hillshade TileJSON URL — use in MapLibre/Leaflet/leafmap
url = hillshade_tile_url(bbox=(-84.9, 38.15, -84.8, 38.25))

# Slope in degrees
url = slope_tile_url(bbox=(-84.9, 38.15, -84.8, 38.25))

# Contour lines every 50ft
url = contour_tile_url(bbox=(-84.9, 38.15, -84.8, 38.25), increment=50)
```

### Interactive notebook maps

```python
# Display a hillshade map in Jupyter (requires pip install abovepy[viz])
m = abovepy.show("dem_phase3", county="Franklin", algorithm="hillshade")
m  # renders interactive leafmap
```

### Persistent virtual mosaics

Register a search with TiTiler-pgSTAC to get a shareable tile URL:

```python
search_id = abovepy.register_search("dem_phase3", bbox=(-84.9, 38.15, -84.8, 38.25))
from abovepy.searches import search_tile_url
url = search_tile_url(search_id)  # stable TileJSON URL
```

### Oblique imagery

Access Phase 3 oblique imagery from 4 camera directions (backward, forward, left, right):

```python
from abovepy.obliques import list_oblique_seasons, search_obliques

seasons = list_oblique_seasons()
frames = search_obliques(direction="bwd", season=seasons[-1], max_items=10)
# Each frame has: frame_id, tif_url, json_url, season, direction
```

### Oblique spatial search & bundles

Find the oblique frames that actually cover a location — and get the best
frame from each camera direction for site inspection:

```python
import abovepy

# Frames within 500 ft of a point, nearest first (all four directions)
frames = abovepy.search_obliques(point=(-84.85, 38.19), radius_feet=500, direction=None)

# Best Backward/Forward/Left/Right frame set for a site
bundle = abovepy.oblique_bundle((-84.85, 38.19))
print(bundle["bwd"].tif_url)

# Parsed sidecar metadata (footprint, camera, timestamp) on every frame
frame = frames[0]
frame.fetch_metadata()
print(frame.footprint)   # shapely geometry
print(frame.timestamp)   # acquisition datetime
print(frame.raw)         # full sidecar payload
```

### Elevation analysis

Answer terrain questions in one line — abovepy streams just the pixels it
needs from the cloud (no downloads):

```python
import abovepy
from shapely.geometry import box

# Elevation at a point (US survey feet)
elev = abovepy.sample((-84.87, 38.20))

# Elevation profile along a transect — distances in true feet (EPSG:3089)
df = abovepy.profile([(-84.9, 38.15), (-84.8, 38.25)], n_points=200)

# Statistics within a polygon
stats = abovepy.zonal_stats(box(-84.88, 38.16, -84.82, 38.24))
print(stats["mean"], stats["min"], stats["max"])

# Phase 2 → Phase 3 elevation change (grids aligned automatically)
diff, profile = abovepy.change_detection(
    (-84.9, 38.15, -84.8, 38.25),
    product_before="dem_phase2",
    product_after="dem_phase3",
    output="change.tif",
)
```

Or from the terminal:

```bash
abovepy sample --point=-84.87,38.20
abovepy profile --line "-84.9,38.15 -84.8,38.25" --format csv
```

### Shareable web maps

Write a self-contained MapLibre GL JS viewer — open it in a browser, embed
it in a report, host it anywhere static:

```python
import abovepy

abovepy.export_map_html("franklin_hillshade.html", county="Franklin", algorithm="hillshade")
```

```bash
abovepy export-map -o map.html --county Franklin --algorithm hillshade
```

### Lazy loading with xarray

Load search results as a lazy xarray Dataset via odc-stac
(`pip install abovepy[xarray]`):

```python
result = abovepy.search(county="Franklin", product="dem_phase3")
ds = result.to_xarray(chunks={"x": 2048, "y": 2048})
```

## Examples

### DEM Phase Comparison

Compare 5ft Phase 1 vs 2ft Phase 3 resolution from the same tile in Frankfort:

![DEM Phase Comparison](examples/output/compare_dem_phases.png)

### Hillshade from Streamed DEM

Compute a hillshade directly from a cloud-hosted DEM tile — no download required:

![Hillshade](examples/output/hillshade.png)

### Streamed DEM Window

Read just the pixels you need with a bounding box:

![Stream Window](examples/output/stream_window.png)

### Ortho RGB Extract

Pull 3-inch true-color imagery of the Kentucky State Capitol:

![Ortho RGB](examples/output/ortho_rgb.png)

### Kentucky River REM

Relative Elevation Model showing height above the Kentucky River in Frankfort:

![Kentucky River REM](examples/output/kentucky_river_rem.png)

### Mine Volume Estimate

Estimate cut volume for an active mine permit in Perry County using DEM differencing:

![Mine Volume](examples/output/mine_volume.png)

### Search Results Map

Visualize tile coverage for Franklin County:

![Search Results](examples/output/search_results_map.png)

### DEM Change Detection

Compare Phase 1 vs Phase 3 DEM over a Pike County mining area to detect terrain change:

![DEM Change Detection](examples/output/dem_change_detection.png)

### Flood Inundation Simulation

Simulate rising water levels on a DEM — watch the Kentucky River floodplain fill:

![Flood Inundation](examples/output/flood_inundation.png)

![Flood Simulation GIF](examples/output/flood_simulation.gif)

### Slope & Aspect Analysis

Compute slope and aspect from DEM for terrain analysis:

![Slope & Aspect](examples/output/slope_aspect.png)

### Elevation Contours over Hillshade

Overlay 10ft/50ft contour lines on a shaded relief map:

![Contour Map](examples/output/contour_map.png)

### Elevation Profile

Extract a cross-valley transect showing the Kentucky River valley profile:

![Elevation Profile](examples/output/elevation_profile.png)

### Land Use Change

Side-by-side ortho imagery across phases showing development over time:

![Land Use Change](examples/output/land_use_change.png)

### Multi-County Tile Coverage

Map DEM tile coverage across five Central Kentucky counties:

![Multi-County Coverage](examples/output/multi_county_coverage.png)

### Multi-Product Site Assessment

Combine ortho, DEM, hillshade, and slope for a single area:

![Site Assessment](examples/output/site_assessment.png)

### Product Gallery

One tile from each product type - DEM Phase 1/2/3 and Ortho Phase 3:

![Product Gallery](examples/output/product_gallery.png)

### pgSTAC Terrain Previews

Server-side DEM elevation, hillshade, and ortho previews generated from TiTiler-pgSTAC:

![pgSTAC Terrain Previews](examples/output/pgstac_terrain_previews.png)

### Oblique Site Inspection

Four-direction oblique frame coverage summarized for rapid site inspection:

![Oblique Site Inspection](examples/output/oblique_site_inspection.png)

See [examples/scripts/](examples/scripts/) for the full source code behind each image and demo.

## Available Products

| Product | Resolution | Format | Collection ID |
|---|---|---|---|
| `dem_phase1` | 5ft | COG | `dem-phase1` |
| `dem_phase2` | 2ft | COG | `dem-phase2` |
| `dem_phase3` | 2ft | COG | `dem-phase3` |
| `ortho_phase1` | 6 inch | COG | `orthos-phase1` |
| `ortho_phase2` | 6 inch | COG | `orthos-phase2` |
| `ortho_phase3` | 3 inch | COG | `orthos-phase3` |
| `laz_phase1` | Varies | LAZ | `laz-phase1` |
| `laz_phase2` | Varies | COPC | `laz-phase2` |
| `laz_phase3` | Varies | COPC | `laz-phase3` |
| `oblique_phase3_bwd` | 3 inch | COG | `obliques-phase3`* |
| `oblique_phase3_fwd` | 3 inch | COG | `obliques-phase3`* |
| `oblique_phase3_left` | 3 inch | COG | `obliques-phase3`* |
| `oblique_phase3_right` | 3 inch | COG | `obliques-phase3`* |

\* Oblique STAC collection pending — use `search_obliques()` for S3-based discovery.

All data is natively in **EPSG:3089** (Kentucky Single Zone, US feet). abovepy accepts bounding boxes in EPSG:4326 by default.

## ArcGIS Pro Toolbox

An ArcGIS Pro Python Toolbox is included in `arcgis/AbovePro.pyt` with tools for:

- **Find KyFromAbove Tiles** — draw extent, pick product, see available tiles
- **Download Tiles** — download with progress tracking
- **Download and Load** — download + add to map in one step
- **DEM Hillshade** — automated DEM → hillshade workflow
- **County Download** — download by county name dropdown

See [ArcGIS Pro Toolbox Guide](https://chrislyonsKY.github.io/AbovePy/tutorials/arcgis-pro/) for installation and usage.

## QGIS Plugin

**AboveQGIS** is a QGIS Processing toolbox plugin with 6 tools:

- **Search KyFromAbove Tiles** — county dropdown (all 120) or map extent, outputs tile footprint layer
- **Download KyFromAbove Tiles** — concurrent downloads, auto-loads with hillshade symbology
- **Load County Ortho Mosaic** — stream a full-county 3-inch ortho directly from S3 (no download)
- **Mosaic KyFromAbove Tiles** — build VRT or GeoTIFF from downloaded tiles
- **Generate Hillshade Tile URL** — server-side hillshade via TiTiler (no download needed)
- **STL Export** — convert DEM to 3D-printable mesh via `abovepy.export.to_stl()`

Install via **Plugins > Manage and Install Plugins** or from the [QGIS Plugin Repository](https://plugins.qgis.org/plugins/aboveqgis/). The plugin auto-installs abovepy on first run.

Tools appear under **Plugins > AboveQGIS — KyFromAbove** and in the Processing Toolbox.

### County Ortho Mosaics

KyFromAbove provides pre-built 3-inch ortho mosaics for all 120 counties. Stream them directly without downloading:

```python
import abovepy

# Get the S3 URL for Franklin County's ortho mosaic
url = abovepy.county_mosaic_url("Franklin")

# Or for ArcGIS users
url = abovepy.county_mosaic_url("Franklin", fmt="tpkx")
```

In QGIS, use **Plugins > AboveQGIS > Load County Ortho Mosaic** to stream directly into your project.

## Web Visualization

abovepy generates TiTiler-compatible URLs for web map integration:

```python
from abovepy.titiler import cog_tile_url, collection_tile_url, hillshade_tile_url

# Individual COG via standalone TiTiler
url = cog_tile_url(tiles.iloc[0].asset_url)

# Entire collection via TiTiler-pgSTAC (no individual URLs needed)
url = collection_tile_url("dem_phase3", bbox=(-84.9, 38.15, -84.8, 38.25))

# Server-side hillshade
url = hillshade_tile_url(bbox=(-84.9, 38.15, -84.8, 38.25))

# Use any of these with MapLibre GL JS, Leaflet, or leafmap
```

KyFromAbove TiTiler endpoints are used by default. A `docker-compose.yml` for local TiTiler is in `examples/`.

## Kentucky Engineering Geometry

abovepy includes geometry utilities that work natively in Kentucky State Plane (EPSG:3089, Northing/Easting in US Survey Feet) — the coordinate system surveyors and engineers actually use:

```python
from abovepy import buffer_feet, corridor_buffer
from shapely.geometry import Point, LineString

# Buffer a survey point by 500 feet using State Plane coordinates
site = Point(1_600_000, 312_000)  # Easting, Northing in feet
area = buffer_feet(site, 500.0, input_crs="EPSG:3089")

# Create a corridor polygon from a road centerline (200ft each side)
road = LineString([(1_599_000, 312_000), (1_601_000, 312_500)])
corridor = corridor_buffer(road, 400.0, input_crs="EPSG:3089")

# Also works with WGS84 — reprojects to EPSG:3089 internally
site_wgs84 = Point(-84.87, 38.20)
area = buffer_feet(site_wgs84, 500.0)  # input_crs defaults to EPSG:4326
```

## Command-Line Interface

abovepy includes a full CLI for terminal workflows:

```bash
# Search with feet-based buffer
abovepy search --point=-84.87,38.20 --buffer-feet 500 -p dem_phase3

# Get provenance metadata as JSON
abovepy search --county Franklin -p dem_phase3 --format provenance

# Estimate download size
abovepy estimate --county Franklin -p ortho_phase3

# Download tiles (concurrent, resumable)
abovepy download --county Franklin -p dem_phase3 -o ./data --workers 8

# Generate a hillshade tile URL
abovepy tile-url --bbox=-84.9,38.15,-84.8,38.25 --algorithm hillshade
```

## Advanced: Direct STAC Access

For power users who need the full pystac-client:

```python
client = abovepy.KyFromAboveClient()
stac_client = client.get_stac_client()

# Full pystac-client API
results = stac_client.search(
    collections=["dem-phase3"],
    bbox=(-84.9, 38.15, -84.8, 38.25),
    datetime="2022-01-01/..",
).item_collection()
```

## Related Resources

- **[kyfromabove-on-aws-examples](https://github.com/ianhorn/kyfromabove-on-aws-examples)** — Foundational examples for accessing KyFromAbove data on AWS using tile index GeoPackages and boto3. Great reference for understanding the raw S3 data structure that abovepy wraps.
- **[kyfromabove-gisconference2025-workshop](https://github.com/ianhorn/kyfromabove-gisconference2025-workshop)** — 2025 KY GIS Conference workshop covering STAC API access from Python, ArcGIS Pro, and QGIS. Includes building height estimation from COPC LiDAR, DEM change detection, and MosaicJSON workflows.
- **[KyFromAbove](https://kyfromabove.ky.gov/)** — Official program site from the Kentucky Division of Geographic Information.
- **[STAC Browser](https://kygeonet.ky.gov/stac/)** — Browse the KyFromAbove STAC catalog interactively.

### Cloud-Native Geospatial Standards

- **[Cloud-Optimized Geospatial Formats Guide](https://guide.cloudnativegeo.org/)** — Comprehensive reference for COG, COPC, GeoParquet, and other cloud-native formats from the Cloud-Native Geospatial Foundation.
- **[STAC Best Practices](https://github.com/radiantearth/stac-best-practices/)** — Community conventions for SpatioTemporal Asset Catalogs.
- **[rio-cogeo](https://cogeotiff.github.io/rio-cogeo/)** — Validate and create Cloud-Optimized GeoTIFFs. Use `rio cogeo validate` to check internal tiling, overviews, and compression.
- **[COPC Specification](https://copc.io/)** — Cloud-Optimized Point Cloud format spec. Phase 2 and 3 LiDAR in KyFromAbove use this format.
- **[Distributing GeoParquet](https://github.com/opengeospatial/geoparquet/blob/main/format-specs/distributing-geoparquet.md)** — OGC guidance on partitioning and distributing large geospatial datasets as GeoParquet.

## Data Source

- **STAC API:** `https://spved5ihrl.execute-api.us-west-2.amazonaws.com/`
- **S3 Bucket:** `s3://kyfromabove/` (public, us-west-2)
- **AWS Open Data Registry:** [KyFromAbove](https://registry.opendata.aws/kyfromabove/)

## License

GPL-3.0 — see [LICENSE](LICENSE).

---
