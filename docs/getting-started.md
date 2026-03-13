# Getting Started

Get up and running with abovepy in under 5 minutes. This guide walks you through installation, your first search, downloading tiles, and building a mosaic — with expected output at every step.

## Requirements

- Python 3.10+
- No AWS credentials needed — all KyFromAbove data is public

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

=== "from source"

    ```bash
    git clone https://github.com/chrislyonsKY/abovepy.git
    cd abovepy
    pip install -e .
    ```

### Optional extras

```bash
pip install abovepy[lidar]    # COPC/LAZ point cloud support (laspy)
pip install abovepy[viz]      # leafmap + matplotlib visualization
pip install abovepy[s3]       # Direct S3 access (boto3)
pip install abovepy[all]      # Everything
```

## Verify Installation

Confirm abovepy is installed and importable:

```python
python -c "import abovepy; print(abovepy.__version__)"
```

```text
0.1.0
```

!!! note
    Your version number will reflect whichever release you installed. If you see `ModuleNotFoundError: No module named 'abovepy'`, check that you installed it in the correct Python environment. See the [Troubleshooting Guide](tutorials/troubleshooting.md#no-module-named-abovepy) for help.

## Your First Search

### Search by county

Every query starts with `abovepy.search()`. Pass a product name and either a county or a bounding box:

```python
import abovepy

tiles = abovepy.search(county="Franklin", product="dem_phase3")
print(f"Found {len(tiles)} tiles")
print(tiles.head())
```

```text
Found 42 tiles
          tile_id                                           geometry  \
0  N1234E5678  POLYGON ((1234000 5678000, 1239000 5678000, ...
1  N1234E5679  POLYGON ((1234000 5679000, 1239000 5679000, ...
2  N1235E5678  POLYGON ((1235000 5678000, 1240000 5678000, ...
3  N1235E5679  POLYGON ((1235000 5679000, 1240000 5679000, ...
4  N1236E5678  POLYGON ((1236000 5678000, 1241000 5678000, ...

                                           asset_url  file_size
0  https://s3.us-west-2.amazonaws.com/kyfromabove...   12345678
1  https://s3.us-west-2.amazonaws.com/kyfromabove...   11234567
2  https://s3.us-west-2.amazonaws.com/kyfromabove...   13456789
3  https://s3.us-west-2.amazonaws.com/kyfromabove...   12567890
4  https://s3.us-west-2.amazonaws.com/kyfromabove...   11890123
```

The result is a **GeoDataFrame** with one row per tile. Key columns:

| Column | Description |
|---|---|
| `tile_id` | KyFromAbove tile grid identifier |
| `geometry` | Tile footprint polygon (EPSG:3089) |
| `asset_url` | Direct HTTPS URL to the COG/LAZ file |
| `file_size` | File size in bytes |

### Search by bounding box

For a specific area, pass a bounding box as `(west, south, east, north)` in **EPSG:4326** (longitude, latitude):

```python
tiles = abovepy.search(
    bbox=(-84.9, 38.15, -84.8, 38.25),
    product="dem_phase3"
)
print(f"Found {len(tiles)} tiles covering the bbox")
```

```text
Found 6 tiles covering the bbox
```

!!! tip
    Bounding boxes use **EPSG:4326** (longitude, latitude) — the standard GPS coordinate system. abovepy converts to the native KyFromAbove CRS (EPSG:3089, Kentucky Single Zone) automatically. You never need to work in EPSG:3089 directly.

### Check what products are available

Not sure which product name to use? List everything:

```python
info = abovepy.info()
print(info)
```

```text
Available KyFromAbove Products:
  dem_phase1     DEM Phase 1 (5ft)       COG    5ft resolution
  dem_phase2     DEM Phase 2 (2ft)       COG    2ft resolution
  dem_phase3     DEM Phase 3 (2ft)       COG    2ft resolution
  ortho_phase1   Ortho Phase 1 (6in)     COG    6in resolution
  ortho_phase2   Ortho Phase 2 (6in)     COG    6in resolution
  ortho_phase3   Ortho Phase 3 (3in)     COG    3in resolution
  laz_phase1     LiDAR Phase 1           LAZ    varies
  laz_phase2     LiDAR Phase 2           COPC   varies
  laz_phase3     LiDAR Phase 3           COPC   varies
```

## Download Tiles

Once you have search results, download the actual data files:

```python
paths = abovepy.download(tiles, output_dir="./data")
print(f"Downloaded {len(paths)} files")
for p in paths[:3]:
    print(f"  {p}")
```

```text
Downloading: 100%|██████████| 6/6 [00:34<00:00,  5.67s/file]
Downloaded 6 files
  data/N1234E5678.tif
  data/N1234E5679.tif
  data/N1235E5678.tif
```

!!! tip
    Existing files are **skipped by default**. It is safe to run `download()` multiple times — only missing files will be fetched. Pass `overwrite=True` to force re-download.

### Check download size before committing

For large areas, check the total size first:

```python
total_mb = tiles.file_size.sum() / 1e6
print(f"Total download size: {total_mb:.1f} MB across {len(tiles)} tiles")
```

```text
Total download size: 284.7 MB across 42 tiles
```

## Mosaic Tiles

Combine downloaded tiles into a single seamless raster:

```python
# VRT (zero-copy, instant) — the default and recommended approach
vrt = abovepy.mosaic(paths, output="frankfort.vrt")
print(f"Created mosaic: {vrt}")
```

```text
Created mosaic: frankfort.vrt
```

```python
# GeoTIFF (writes a new file to disk — slower, but standalone)
tif = abovepy.mosaic(paths, output="frankfort.tif")
print(f"Created mosaic: {tif}")
```

```text
Created mosaic: frankfort.tif
```

!!! tip "VRT vs GeoTIFF"
    **VRT** is almost always what you want. It creates a virtual mosaic file instantly without copying any pixel data — the VRT just points to the original tiles. Use **GeoTIFF** only when you need a standalone file for sharing or for software that does not support VRT.

## Stream Without Downloading

Read a window directly from the cloud — no local download required:

```python
data, profile = abovepy.read(
    tiles.iloc[0].asset_url,
    bbox=(-84.85, 38.18, -84.82, 38.21)
)
print(f"Array shape: {data.shape}")
print(f"Data type:   {data.dtype}")
print(f"CRS:         {profile['crs']}")
print(f"Value range: {data.min():.1f} to {data.max():.1f}")
```

```text
Array shape: (1, 1847, 1534)
Data type:   float32
CRS:         EPSG:3089
Value range: 682.3 to 891.7
```

!!! note
    Streaming reads use rasterio's `/vsicurl/` driver under the hood. Only the pixels within your bounding box are fetched from the server — not the entire tile. This is efficient for quick lookups and previews.

## Common Patterns

### Pattern 1: Search, download, and mosaic pipeline

The most common workflow — get a DEM mosaic for a county:

```python
import abovepy

# 1. Search
tiles = abovepy.search(county="Fayette", product="dem_phase3")
print(f"Found {len(tiles)} tiles")

# 2. Download
paths = abovepy.download(tiles, output_dir="./fayette_dem")
print(f"Downloaded {len(paths)} files")

# 3. Mosaic
vrt = abovepy.mosaic(paths, output="fayette_dem.vrt")
print(f"Mosaic ready: {vrt}")
```

```text
Found 68 tiles
Downloading: 100%|██████████| 68/68 [03:42<00:00,  3.27s/file]
Downloaded 68 files
Mosaic ready: fayette_dem.vrt
```

### Pattern 2: Streaming read (no download)

Preview a tile's elevation range without saving anything to disk:

```python
import abovepy

tiles = abovepy.search(
    bbox=(-84.5, 38.03, -84.49, 38.04),
    product="dem_phase3"
)
data, profile = abovepy.read(tiles.iloc[0].asset_url)
print(f"Elevation range: {data.min():.1f} ft to {data.max():.1f} ft")
```

```text
Elevation range: 812.4 ft to 967.2 ft
```

### Pattern 3: County search vs bbox search

Both approaches find tiles — choose whichever fits your workflow:

```python
import abovepy

# By county name (uses a built-in lookup table of all 120 KY counties)
tiles_county = abovepy.search(county="Pike", product="dem_phase3")

# By bounding box (EPSG:4326 coordinates)
tiles_bbox = abovepy.search(
    bbox=(-82.73, 37.38, -82.05, 37.70),
    product="dem_phase3"
)

print(f"County search: {len(tiles_county)} tiles")
print(f"Bbox search:   {len(tiles_bbox)} tiles")
```

```text
County search: 187 tiles
Bbox search:   187 tiles
```

!!! tip
    County search is a convenience wrapper that looks up the county's bounding box internally. Both approaches query the same STAC API and return the same GeoDataFrame format.

### Pattern 4: Download a subset of tiles

You do not have to download everything. Slice the GeoDataFrame to get just what you need:

```python
import abovepy

tiles = abovepy.search(county="Jefferson", product="ortho_phase3")
print(f"Total tiles: {len(tiles)}")

# Download only the first 10 tiles
subset = tiles.head(10)
paths = abovepy.download(subset, output_dir="./jefferson_sample")
print(f"Downloaded {len(paths)} of {len(tiles)} tiles")
```

```text
Total tiles: 312
Downloading: 100%|██████████| 10/10 [01:15<00:00,  7.50s/file]
Downloaded 10 of 312 tiles
```

## Product Reference

| Product Key | Description | Format | Resolution |
|---|---|---|---|
| `dem_phase1` | DEM Phase 1 | COG | 5 ft |
| `dem_phase2` | DEM Phase 2 | COG | 2 ft |
| `dem_phase3` | DEM Phase 3 | COG | 2 ft |
| `ortho_phase1` | Orthoimagery Phase 1 | COG | 6 in |
| `ortho_phase2` | Orthoimagery Phase 2 | COG | 6 in |
| `ortho_phase3` | Orthoimagery Phase 3 | COG | 3 in |
| `laz_phase1` | LiDAR Phase 1 | LAZ | varies |
| `laz_phase2` | LiDAR Phase 2 | COPC | varies |
| `laz_phase3` | LiDAR Phase 3 | COPC | varies |

See [KyFromAbove Collections](stac-collections.md) for full details on each collection.

## Next Steps

Now that you have the basics, dive into the tutorials:

- **[DEM + Hillshade Tutorial](tutorials/dem-hillshade.md)** — Build a hillshade visualization from 2-foot DEM tiles
- **[LiDAR Access](tutorials/lidar-access.md)** — Work with COPC point cloud data, filter by classification
- **[Web Maps with TiTiler](tutorials/titiler-maps.md)** — Visualize tiles in the browser with MapLibre and Leafmap
- **[ArcGIS Pro Toolbox](tutorials/arcgis-pro.md)** — Use abovepy inside ArcGIS Pro with the AbovePro toolbox
- **[Troubleshooting](tutorials/troubleshooting.md)** — Solutions for common issues
- **[API Reference](api/reference.md)** — Full function documentation
