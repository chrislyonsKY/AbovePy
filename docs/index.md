---
hide:
  - navigation
  - toc
---

<div class="feature-grid">
  <div class="feature-card">
    <div class="card-icon">&#x1F50D;</div>
    <h3>Search &amp; Discover</h3>
    <p>Find DEM, ortho, LiDAR, and oblique tiles by county, bbox, point+buffer in feet, or custom geometry. 13 products across 3 acquisition phases.</p>
  </div>
  <div class="feature-card">
    <div class="card-icon">&#x2B07;</div>
    <h3>Download &amp; Export</h3>
    <p>Concurrent downloads with resume. Estimate size before committing. Export to GeoTIFF, GeoPackage, Shapefile, GeoParquet, or LandXML.</p>
  </div>
  <div class="feature-card">
    <div class="card-icon">&#x1F30E;</div>
    <h3>Analyze &amp; Visualize</h3>
    <p>Local terrain analysis &mdash; hillshade, slope, flood, contours, volume, profiles. Server-side TiTiler. Interactive notebook maps.</p>
  </div>
  <div class="feature-card">
    <div class="card-icon">&#x1F4CB;</div>
    <h3>Provenance &amp; QA</h3>
    <p>Source documentation for deliverables &mdash; acquisition dates, CRS, tile counts, coverage gaps, mixed-phase warnings. Built for survey-grade work.</p>
  </div>
  <div class="feature-card">
    <div class="card-icon">&#x1F5FA;</div>
    <h3>ArcGIS Pro &amp; QGIS</h3>
    <p>ArcGIS Pro toolbox with 5 tools. QGIS plugin coming in v2.1. No STAC knowledge required &mdash; county dropdown, click, go.</p>
  </div>
  <div class="feature-card">
    <div class="card-icon">&#x1F4D0;</div>
    <h3>Engineering CRS</h3>
    <p>First-class EPSG:3089 support. Buffer in feet, corridor centerline search, polygon clips. Built for Kentucky surveyors and engineers.</p>
  </div>
</div>

<div class="stats-bar">
  <div class="stat">
    <div class="stat-value">13</div>
    <div class="stat-label">Data Products</div>
  </div>
  <div class="stat">
    <div class="stat-value">3</div>
    <div class="stat-label">Acquisition Phases</div>
  </div>
  <div class="stat">
    <div class="stat-value">120</div>
    <div class="stat-label">KY Counties</div>
  </div>
  <div class="stat">
    <div class="stat-value">0</div>
    <div class="stat-label">Credentials Needed</div>
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

# Check provenance for deliverable documentation
result.provenance()
# {'product': 'dem_phase3', 'acquisition_period': '2022–2025', ...}

# Validate data quality
result.validate()
# ['3 tile(s) have no acquisition date metadata.']

# Concurrent download (4 threads, resumable)
paths = result.download("./data")

# Mosaic into a single VRT
vrt = result.mosaic(output="frankfort.vrt")
```

<div class="section-label">Engineering workflows</div>

## Feet-based search &amp; corridor buffers

```python
# Point search with 1000-foot buffer (accurate in EPSG:3089)
result = abovepy.search(
    point=(-84.85, 38.19), buffer_feet=1000, product="dem_phase3"
)

# Corridor search along a road centerline
from shapely.geometry import LineString
road = LineString([(-84.9, 38.2), (-84.8, 38.2)])
result = abovepy.search(geometry=road, buffer_feet=200, product="ortho_phase3")

# Phase comparison
phase2 = abovepy.search(county="Franklin", product="dem_phase2")
overlap = result.compare(phase2)
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

All data in **EPSG:3089** (Kentucky Single Zone, US survey feet). abovepy accepts EPSG:4326 bounding boxes by default and converts transparently. No API keys or credentials required.

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
