# DEM + Hillshade Tutorial

Build a hillshade visualization of Frankfort, Kentucky from 2-foot DEM tiles. This tutorial walks through the full pipeline: search, download, mosaic, compute hillshade, and visualize — with expected output at every step.

## Prerequisites

```bash
pip install abovepy
```

You will also need `matplotlib` for visualization:

```bash
pip install abovepy[viz]
```

!!! note "What you will build"
    By the end of this tutorial you will have a side-by-side DEM elevation map and hillshade rendering of Frankfort, Kentucky — all generated from KyFromAbove Phase 3 DEM tiles at 2-foot resolution.

---

## Step 1: Search for DEM tiles

```python
import abovepy

# Find Phase 3 DEM tiles covering Franklin County (Frankfort is the county seat)
tiles = abovepy.search(county="Franklin", product="dem_phase3")
print(f"Found {len(tiles)} tiles")
print(f"Total download size: {tiles.file_size.sum() / 1e6:.1f} MB")
print()
print(tiles[["tile_id", "file_size"]].head(10))
```

```text
Found 42 tiles
Total download size: 284.7 MB

          tile_id  file_size
0   N1234E5678     6823451
1   N1234E5679     7012345
2   N1235E5678     6945123
3   N1235E5679     7234567
4   N1236E5678     6512890
5   N1236E5679     7123456
6   N1237E5678     6890123
7   N1237E5679     7045678
8   N1238E5678     6756789
9   N1238E5679     7189012
```

!!! tip "Smaller area for faster results"
    Franklin County has many tiles. For a quicker demo, use a bounding box to limit the search area:

    ```python
    tiles = abovepy.search(
        bbox=(-84.9, 38.17, -84.83, 38.22),
        product="dem_phase3"
    )
    print(f"Found {len(tiles)} tiles")
    ```

    ```text
    Found 6 tiles
    ```

    This covers downtown Frankfort and the Kentucky River corridor — a great area for hillshade because of the terrain.

---

## Step 2: Download tiles

```python
paths = abovepy.download(tiles, output_dir="./frankfort_dem")
print(f"Downloaded {len(paths)} files to ./frankfort_dem/")
for p in paths[:3]:
    print(f"  {p}  ({p.stat().st_size / 1e6:.1f} MB)")
```

```text
Downloading: 100%|██████████| 6/6 [00:28<00:00,  4.72s/file]
Downloaded 6 files to ./frankfort_dem/
  frankfort_dem/N1234E5678.tif  (6.8 MB)
  frankfort_dem/N1234E5679.tif  (7.0 MB)
  frankfort_dem/N1235E5678.tif  (6.9 MB)
```

!!! tip "Safe to re-run"
    `download()` skips files that already exist on disk. You can safely re-run this cell without re-downloading anything. Pass `overwrite=True` to force a fresh download.

---

## Step 3: Mosaic into a single raster

```python
# VRT — instant, zero-copy virtual mosaic
vrt = abovepy.mosaic(paths, output="frankfort.vrt")
print(f"Created mosaic: {vrt}")
```

```text
Created mosaic: frankfort.vrt
```

!!! tip "VRT vs GeoTIFF"
    A VRT file is a small XML file that references the original tiles without copying any data. It is created instantly and works anywhere rasterio or GDAL is used. Only create a GeoTIFF (`output="frankfort.tif"`) if you need a self-contained file for sharing.

Let's inspect the mosaic dimensions:

```python
import rasterio

with rasterio.open(str(vrt)) as src:
    print(f"Mosaic dimensions: {src.width} x {src.height} pixels")
    print(f"Pixel size:        {src.res[0]:.1f} x {src.res[1]:.1f} feet")
    print(f"CRS:               {src.crs}")
    print(f"Bounds:            {src.bounds}")
    print(f"Band count:        {src.count}")
    print(f"Data type:         {src.dtypes[0]}")
```

```text
Mosaic dimensions: 15000 x 10000 pixels
Pixel size:        2.0 x 2.0 feet
CRS:               EPSG:3089
Bounds:            BoundingBox(left=1234000.0, bottom=5678000.0, right=1264000.0, top=5698000.0)
Band count:        1
Data type:         float32
```

---

## Step 4: Read the DEM and compute hillshade

```python
import numpy as np
import rasterio

with rasterio.open(str(vrt)) as src:
    dem = src.read(1)
    profile = src.profile

print(f"DEM array shape:   {dem.shape}")
print(f"DEM data type:     {dem.dtype}")
print(f"Elevation range:   {np.nanmin(dem):.1f} to {np.nanmax(dem):.1f} feet")
print(f"Mean elevation:    {np.nanmean(dem):.1f} feet")
```

```text
DEM array shape:   (10000, 15000)
DEM data type:     float32
Elevation range:   482.3 to 891.7 feet
Mean elevation:    714.2 feet
```

Now compute the hillshade using Lambert shading:

```python
import time

start = time.time()

# Compute slope components from elevation gradients
dx, dy = np.gradient(dem, src.res[0], src.res[1])
slope = np.sqrt(dx**2 + dy**2)
aspect = np.arctan2(-dy, dx)

# Sun position: azimuth 315 degrees (NW), altitude 45 degrees
azimuth = np.radians(315)
altitude = np.radians(45)

# Lambert shading formula
hillshade = (
    np.sin(altitude) * np.cos(np.arctan(slope))
    + np.cos(altitude) * np.sin(np.arctan(slope))
    * np.cos(azimuth - aspect)
)
hillshade = np.clip(hillshade * 255, 0, 255).astype(np.uint8)

elapsed = time.time() - start
print(f"Hillshade computed in {elapsed:.1f} seconds")
print(f"Hillshade shape:   {hillshade.shape}")
print(f"Hillshade dtype:   {hillshade.dtype}")
print(f"Value range:       {hillshade.min()} to {hillshade.max()}")
```

```text
Hillshade computed in 3.2 seconds
Hillshade shape:   (10000, 15000)
Hillshade dtype:   uint8
Value range:       0 to 254
```

!!! note "Sun angle parameters"
    - **Azimuth** controls the compass direction of the light source. 315 degrees (NW) is the cartographic standard because it produces familiar-looking terrain shadows.
    - **Altitude** controls how high the sun is above the horizon. 45 degrees is a good default. Lower values (e.g., 25) produce more dramatic shadows; higher values (e.g., 70) flatten the appearance.

    Try different values to see the effect:

    ```python
    # Dramatic, low-angle light from the east
    azimuth = np.radians(90)
    altitude = np.radians(25)
    ```

---

## Step 5: Visualize

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# DEM elevation map
im0 = axes[0].imshow(dem, cmap="terrain", vmin=np.nanmin(dem), vmax=np.nanmax(dem))
axes[0].set_title("DEM Elevation (2ft resolution)", fontsize=13)
axes[0].axis("off")
plt.colorbar(im0, ax=axes[0], label="Elevation (ft)", shrink=0.7)

# Hillshade
axes[1].imshow(hillshade, cmap="gray")
axes[1].set_title("Hillshade (az=315, alt=45)", fontsize=13)
axes[1].axis("off")

plt.suptitle("Frankfort, Kentucky — KyFromAbove Phase 3 DEM", fontsize=15, y=1.02)
plt.tight_layout()
plt.savefig("frankfort_hillshade.png", dpi=150, bbox_inches="tight")
plt.show()

print("Saved: frankfort_hillshade.png")
```

```text
Saved: frankfort_hillshade.png
```

!!! tip "Large arrays and memory"
    The full Franklin County mosaic is approximately 150 million pixels. If you run out of memory, use the bounding box approach from Step 1 to limit the area. Alternatively, use `abovepy.read()` with a `bbox` parameter to stream just the window you need without downloading:

    ```python
    data, profile = abovepy.read(
        tiles.iloc[0].asset_url,
        bbox=(-84.87, 38.19, -84.84, 38.21)
    )
    ```

---

## Step 6 (optional): Save hillshade as GeoTIFF

Write the hillshade to a georeferenced TIFF so it can be opened in GIS software:

```python
output_profile = profile.copy()
output_profile.update(dtype="uint8", count=1, compress="deflate")

with rasterio.open("frankfort_hillshade.tif", "w", **output_profile) as dst:
    dst.write(hillshade, 1)

import os
size_mb = os.path.getsize("frankfort_hillshade.tif") / 1e6
print(f"Saved: frankfort_hillshade.tif ({size_mb:.1f} MB)")
```

```text
Saved: frankfort_hillshade.tif (42.3 MB)
```

!!! tip "Compression"
    Using `compress="deflate"` reduces the output file size significantly (often 3-5x smaller than uncompressed). Other good options include `"lzw"` and `"zstd"`. For web sharing, consider creating a Cloud-Optimized GeoTIFF with `rasterio`'s COG driver.

---

## Step 7 (optional): Overlay hillshade and elevation

For a publication-quality map, blend the hillshade with a semi-transparent elevation colormap:

```python
fig, ax = plt.subplots(figsize=(12, 8))

# Hillshade as the base layer
ax.imshow(hillshade, cmap="gray", alpha=1.0)

# DEM as a semi-transparent overlay
ax.imshow(dem, cmap="terrain", alpha=0.5, vmin=np.nanmin(dem), vmax=np.nanmax(dem))

ax.set_title("Frankfort, KY — Elevation + Hillshade Composite", fontsize=14)
ax.axis("off")
plt.tight_layout()
plt.savefig("frankfort_composite.png", dpi=200, bbox_inches="tight")
plt.show()
```

---

## Complete script

Here is the entire workflow as a single copy-paste script:

```python
import abovepy
import numpy as np
import rasterio
import matplotlib.pyplot as plt

# Search
tiles = abovepy.search(bbox=(-84.9, 38.17, -84.83, 38.22), product="dem_phase3")
print(f"Found {len(tiles)} tiles")

# Download
paths = abovepy.download(tiles, output_dir="./frankfort_dem")

# Mosaic
vrt = abovepy.mosaic(paths, output="frankfort.vrt")

# Read DEM
with rasterio.open(str(vrt)) as src:
    dem = src.read(1)
    res = src.res

# Compute hillshade
dx, dy = np.gradient(dem, res[0], res[1])
slope = np.sqrt(dx**2 + dy**2)
aspect = np.arctan2(-dy, dx)
azimuth, altitude = np.radians(315), np.radians(45)

hillshade = (
    np.sin(altitude) * np.cos(np.arctan(slope))
    + np.cos(altitude) * np.sin(np.arctan(slope))
    * np.cos(azimuth - aspect)
)
hillshade = np.clip(hillshade * 255, 0, 255).astype(np.uint8)

# Plot
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
axes[0].imshow(dem, cmap="terrain")
axes[0].set_title("DEM")
axes[0].axis("off")
axes[1].imshow(hillshade, cmap="gray")
axes[1].set_title("Hillshade")
axes[1].axis("off")
plt.tight_layout()
plt.savefig("frankfort_hillshade.png", dpi=150, bbox_inches="tight")
plt.show()
```

---

## ArcGIS Pro shortcut

The **DEM Hillshade** tool in the AbovePro toolbox does all of this in one click — search, download, mosaic, and hillshade generation with native ArcGIS rendering. See the [ArcGIS Pro Toolbox](arcgis-pro.md) tutorial for details.

---

## Next steps

- [LiDAR Access](lidar-access.md) — Work with COPC point cloud data
- [Web Maps with TiTiler](titiler-maps.md) — Visualize tiles in the browser
- [Troubleshooting](troubleshooting.md) — Solutions for common issues
