---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# abovepy

**KyFromAbove LiDAR, DEM, and orthoimagery data access for Python.**

Kentucky's statewide elevation, imagery, and point cloud data — Pythonic access, zero credentials.

</div>

<div class="badges" markdown>

[![PyPI](https://img.shields.io/pypi/v/abovepy?color=8B5CF6&style=flat-square)](https://pypi.org/project/abovepy/)
[![Python](https://img.shields.io/pypi/pyversions/abovepy?style=flat-square)](https://pypi.org/project/abovepy/)
[![CI](https://img.shields.io/github/actions/workflow/status/chrislyonsKY/abovepy/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/chrislyonsKY/abovepy/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square)](https://github.com/chrislyonsKY/abovepy/blob/main/LICENSE)

</div>

---

## Install

=== "pip"

    ```bash
    pip install abovepy
    ```

=== "With LiDAR support"

    ```bash
    pip install abovepy[lidar]
    ```

=== "With visualization"

    ```bash
    pip install abovepy[viz]
    ```

=== "Everything"

    ```bash
    pip install abovepy[all]
    ```

---

## Quick Start

```python
import abovepy

# Search by county name
tiles = abovepy.search(county="Franklin", product="dem_phase3")

# Download matching tiles
paths = abovepy.download(tiles, output_dir="./data")

# Mosaic into a single VRT (zero-copy, instant)
vrt = abovepy.mosaic(paths, output="frankfort.vrt")

# Or stream a window without downloading anything
data, profile = abovepy.read(
    tiles.iloc[0].asset_url,
    bbox=(-84.85, 38.18, -84.82, 38.21)
)
```

---

## Features

<div class="grid" markdown>

<div class="card" markdown>

### County-Based Search

Search by any of Kentucky's 120 counties. No bounding box required.

```python
abovepy.search(county="Pike", product="dem_phase3")
```

</div>

<div class="card" markdown>

### Cloud-Native Reads

Stream COGs directly from S3 — read only the pixels you need.

```python
abovepy.read(url, bbox=extent)
```

</div>

<div class="card" markdown>

### 9 Data Products

DEMs, orthoimagery, and LiDAR point clouds across three acquisition phases.

```python
abovepy.info()  # list all products
```

</div>

<div class="card" markdown>

### ArcGIS Pro Toolbox

Native geoprocessing tools for domain-specific workflows — hillshade, county download, and more.

</div>

</div>

---

## Supported Products

| Product | Resolution | Format |
|---|---|---|
| DEM Phase 1 | 5 ft | Cloud-Optimized GeoTIFF |
| DEM Phase 2 | 2 ft | Cloud-Optimized GeoTIFF |
| DEM Phase 3 | 2 ft | Cloud-Optimized GeoTIFF |
| Ortho Phase 1 | 6 in | Cloud-Optimized GeoTIFF |
| Ortho Phase 2 | 6 in | Cloud-Optimized GeoTIFF |
| Ortho Phase 3 | 3 in | Cloud-Optimized GeoTIFF |
| LiDAR Phase 1 | varies | LAZ |
| LiDAR Phase 2 | varies | COPC |
| LiDAR Phase 3 | varies | COPC (partial) |

All data is natively in **EPSG:3089** (Kentucky Single Zone, US feet). abovepy accepts bounding boxes in EPSG:4326 by default and converts transparently.

---

## What abovepy is NOT

- **Not a general STAC client** — use [pystac-client](https://pystac-client.readthedocs.io/) for that
- **Not a tile server** — use [TiTiler](https://developmentseed.org/titiler/) for web map tiles
- **Not a point cloud processor** — use [PDAL](https://pdal.io/) for heavy LiDAR workflows

abovepy is a sharp-focus library for one dataset: KyFromAbove.

---

<div class="cta" markdown>

[Get Started :material-arrow-right:](getting-started.md){ .md-button .md-button--primary }
[View on GitHub :material-github:](https://github.com/chrislyonsKY/abovepy){ .md-button }

</div>

---

<p style="text-align: center; opacity: 0.6;">
Data provided by <a href="https://kyfromabove.ky.gov/">KyFromAbove</a>, managed by the Kentucky Division of Geographic Information.
</p>
