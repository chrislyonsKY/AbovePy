---
hide:
  - navigation
---

<div class="hero" markdown>

# abovepy

**The fastest way for Kentucky GIS analysts to find, inspect, compare, and operationalize KyFromAbove data.**

No API keys. No authentication. Just `pip install` and go.

</div>

<div class="install-cmd">
pip install abovepy
</div>

---

<div class="grid" markdown>

<div class="card" markdown>

### Search & Discover

Find DEM, ortho, LiDAR, and oblique tiles by county, bbox, point+buffer, or custom geometry. 13 products across 3 acquisition phases.

</div>

<div class="card" markdown>

### Download & Export

Concurrent downloads with resume support. Export to GeoTIFF, GeoPackage, Shapefile, or GeoParquet.

</div>

<div class="card" markdown>

### Analyze & Visualize

Local terrain analysis (hillshade, slope, flood, contours). Server-side TiTiler algorithms. Interactive notebook maps.

</div>

<div class="card" markdown>

### ArcGIS Pro Ready

Python Toolbox with 5 tools — find tiles, download, hillshade workflows. County dropdown, no STAC URLs required.

</div>

</div>

---

## Quick Start

```python
import abovepy

# Search by county name — returns a SearchResult workflow object
result = abovepy.search(county="Franklin", product="dem_phase3")
print(result)  # SearchResult('dem_phase3', 342 tiles, ~1710.0 MB)

# Estimate before downloading
result.estimate_size()  # {'tile_count': 342, 'avg_tile_mb': 5.0, 'total_mb': 1710.0}

# Concurrent download (4 threads, resumable)
paths = result.download("./data")

# Mosaic into a single VRT (zero-copy, instant)
vrt = result.mosaic(output="frankfort.vrt")

# Or stream a window without downloading anything
data, profile = abovepy.read(
    result.tiles.iloc[0].asset_url,
    bbox=(-84.85, 38.18, -84.82, 38.21)
)

# Phase comparison
phase2 = abovepy.search(county="Franklin", product="dem_phase2")
overlap = result.compare(phase2)
```

---

## Supported Products

| Product | Resolution | Format | Phases |
|---------|-----------|--------|--------|
| DEM | 5 ft / 2 ft | Cloud-Optimized GeoTIFF | 1, 2, 3 |
| Orthoimagery | 6 in / 3 in | Cloud-Optimized GeoTIFF | 1, 2, 3 |
| LiDAR Point Cloud | varies | LAZ / COPC | 1, 2, 3 |
| Oblique Imagery | 3 in | Cloud-Optimized GeoTIFF | 3 |

All data is natively in **EPSG:3089** (Kentucky Single Zone, US feet). abovepy accepts bounding boxes in EPSG:4326 by default and converts transparently.

---

## What abovepy Is Not

abovepy is **not** a general STAC client, tile server, or point cloud processor.
It is a sharp-focus library for one dataset: **KyFromAbove**.

Use [pystac-client](https://pystac-client.readthedocs.io/) for general STAC.
Use [TiTiler](https://developmentseed.org/titiler/) for tile serving.
Use [PDAL](https://pdal.io/) for heavy LiDAR workflows.

---

[Get Started](getting-started.md){ .md-button .md-button--primary }
[API Reference](api/reference.md){ .md-button }
[View on GitHub](https://github.com/chrislyonsKY/AbovePy){ .md-button }
