# Getting Started

Get up and running with abovepy in under 2 minutes.

## Requirements

- Python 3.10+
- No AWS credentials needed — all data is public

## Installation

=== "pip"

    ```bash
    pip install abovepy
    ```

=== "conda + pip"

    ```bash
    conda create -n abovepy python=3.12
    conda activate abovepy
    pip install abovepy
    ```

### Optional extras

```bash
pip install abovepy[lidar]    # COPC/LAZ point cloud support (laspy)
pip install abovepy[viz]      # leafmap + matplotlib visualization
pip install abovepy[s3]       # Direct S3 access (boto3)
pip install abovepy[all]      # Everything
```

## Your first query

### Search by county

```python
import abovepy

tiles = abovepy.search(county="Franklin", product="dem_phase3")
print(tiles)
```

This returns a `GeoDataFrame` with tile metadata: IDs, geometry, asset URLs, and file sizes.

### Search by bounding box

```python
tiles = abovepy.search(
    bbox=(-84.9, 38.15, -84.8, 38.25),
    product="dem_phase3"
)
```

Bounding boxes are in **EPSG:4326** (longitude, latitude) by default. abovepy converts to the native EPSG:3089 automatically.

## Download tiles

```python
paths = abovepy.download(tiles, output_dir="./data")
# Returns: [Path('data/N123E456.tif'), Path('data/N123E457.tif'), ...]
```

Existing files are skipped by default. Pass `overwrite=True` to re-download.

## Mosaic tiles

```python
# VRT (zero-copy, instant) — the default
vrt = abovepy.mosaic(paths, output="frankfort.vrt")

# GeoTIFF (writes to disk)
tif = abovepy.mosaic(paths, output="frankfort.tif")
```

!!! tip
    VRT is almost always what you want. It creates a virtual mosaic instantly without copying any data. Use GeoTIFF only when you need a standalone file for sharing.

## Stream without downloading

Read a window directly from the cloud — no local download required:

```python
data, profile = abovepy.read(
    tiles.iloc[0].asset_url,
    bbox=(-84.85, 38.18, -84.82, 38.21)
)
```

Returns a NumPy array and a rasterio profile dict.

## Explore available products

```python
print(abovepy.info())
```

See [KyFromAbove Collections](stac-collections.md) for the full product reference.

## Next steps

- [DEM + Hillshade Tutorial](tutorials/dem-hillshade.md) — build a hillshade from scratch
- [LiDAR Access](tutorials/lidar-access.md) — work with COPC point clouds
- [Web Maps with TiTiler](tutorials/titiler-maps.md) — visualize tiles in the browser
- [ArcGIS Pro Toolbox](tutorials/arcgis-pro.md) — use abovepy inside ArcGIS Pro
- [API Reference](api/reference.md) — full function documentation
