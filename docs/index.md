---
hide:
  - navigation
  - toc
---

<div class="mdx-hero" markdown>

# Kentucky's geospatial data, one import away

<div class="hero-sub">
The fastest way for GIS analysts to find, inspect, compare, and operationalize KyFromAbove elevation, imagery, and LiDAR data.
</div>

<div class="install-pill">pip install abovepy</div>

<div class="hero-buttons">
<a href="getting-started/" class="btn-primary">Get Started</a>
<a href="api/reference/" class="btn-secondary">API Reference</a>
<a href="https://github.com/chrislyonsKY/AbovePy" class="btn-secondary">GitHub</a>
</div>

</div>

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
<div class="card-icon">&#x1F50D;</div>

### Search & Discover

Find DEM, ortho, LiDAR, and oblique tiles by county, bbox, point+buffer, or custom geometry. 13 products across 3 phases. Returns a chainable `SearchResult` object.
</div>

<div class="feature-card" markdown>
<div class="card-icon">&#x2B07;</div>

### Download & Export

Concurrent downloads with resume support. Estimate size before committing. Export to GeoTIFF, GeoPackage, Shapefile, or GeoParquet.
</div>

<div class="feature-card" markdown>
<div class="card-icon">&#x1F30E;</div>

### Analyze & Visualize

Local terrain analysis — hillshade, slope, flood, contours, volume. Server-side TiTiler algorithms. Interactive notebook maps via leafmap.
</div>

<div class="feature-card" markdown>
<div class="card-icon">&#x1F5FA;</div>

### ArcGIS Pro Ready

Python Toolbox with 5 tools — find tiles, download, hillshade workflows. County dropdown, concurrent downloads, no STAC knowledge required.
</div>

</div>

---

<div class="section-label">Quick Start</div>

## Search, estimate, download

```python
import abovepy

# Search by county — returns a SearchResult workflow object
result = abovepy.search(county="Franklin", product="dem_phase3")
print(result)  # SearchResult('dem_phase3', 342 tiles, ~1710.0 MB)

# Estimate before downloading
result.estimate_size()

# Concurrent download (4 threads, resumable)
paths = result.download("./data")

# Mosaic into a single VRT
vrt = result.mosaic(output="frankfort.vrt")
```

<div class="section-label">Advanced</div>

## Cloud-native reads & phase comparison

```python
# Stream a window without downloading
data, profile = abovepy.read(
    result.tiles.iloc[0].asset_url,
    bbox=(-84.85, 38.18, -84.82, 38.21)
)

# Compare Phase 2 vs Phase 3 coverage
phase2 = abovepy.search(county="Franklin", product="dem_phase2")
overlap = result.compare(phase2)

# Point-based search with buffer
nearby = abovepy.search(point=(-84.85, 38.19), buffer_miles=2, product="ortho_phase3")
```

---

<div class="section-label">Data catalog</div>

## Supported Products

| Product | Resolution | Format | Phases |
|---------|-----------|--------|--------|
| **DEM** | 5 ft / 2 ft | Cloud-Optimized GeoTIFF | 1, 2, 3 |
| **Orthoimagery** | 6 in / 3 in | Cloud-Optimized GeoTIFF | 1, 2, 3 |
| **LiDAR Point Cloud** | varies | LAZ / COPC | 1, 2, 3 |
| **Oblique Imagery** | 3 in | Cloud-Optimized GeoTIFF | 3 |

All data in **EPSG:3089** (Kentucky Single Zone, US feet). abovepy accepts EPSG:4326 bounding boxes by default and converts transparently. No API keys or credentials required.

---

<div class="section-label">Philosophy</div>

## What abovepy is not

abovepy is **not** a general STAC client, tile server, or point cloud processor.
It is a sharp-focus library for one dataset: **KyFromAbove**.

Use [pystac-client](https://pystac-client.readthedocs.io/) for general STAC.
Use [TiTiler](https://developmentseed.org/titiler/) for tile serving.
Use [PDAL](https://pdal.io/) for heavy LiDAR workflows.

---

<div class="cta-row" markdown>

[Get Started](getting-started.md){ .md-button .md-button--primary }
[API Reference](api/reference.md){ .md-button }
[View on GitHub](https://github.com/chrislyonsKY/AbovePy){ .md-button }

</div>
