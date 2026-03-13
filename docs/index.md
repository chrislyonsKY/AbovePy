# abovepy

**KyFromAbove LiDAR, DEM, and orthoimagery data access for Python.**

Kentucky's statewide elevation, imagery, and point cloud data — Pythonic access, zero credentials.
No API keys, no authentication. Just `pip install` and go.

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

## Supported Products

| Product | Resolution | Format |
|---------|-----------|--------|
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

## What abovepy Is Not

abovepy is **not** a general STAC client, tile server, or point cloud processor.

If you need a general STAC client, use [pystac-client](https://pystac-client.readthedocs.io/).
If you need a tile server, use [TiTiler](https://developmentseed.org/titiler/).
If you need heavy LiDAR workflows, use [PDAL](https://pdal.io/).
abovepy is a sharp-focus library for one dataset: KyFromAbove.

---

[Get Started :material-arrow-right:](getting-started.md){ .md-button .md-button--primary }
[View on GitHub :material-github:](https://github.com/chrislyonsKY/abovepy){ .md-button }
