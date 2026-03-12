# DEM + Hillshade Tutorial

Build a hillshade visualization of Frankfort, Kentucky from 2-foot DEM tiles.

## Prerequisites

```bash
pip install abovepy
```

You'll also need `matplotlib` for visualization:

```bash
pip install abovepy[viz]
```

## Step 1: Search for DEM tiles

```python
import abovepy

# Find Phase 3 DEM tiles covering Franklin County (Frankfort)
tiles = abovepy.search(county="Franklin", product="dem_phase3")
print(f"Found {len(tiles)} tiles")
print(tiles[["tile_id", "file_size"]].head())
```

Or search by bounding box for a smaller area:

```python
tiles = abovepy.search(
    bbox=(-84.9, 38.17, -84.83, 38.22),
    product="dem_phase3"
)
```

## Step 2: Download tiles

```python
paths = abovepy.download(tiles, output_dir="./frankfort_dem")
print(f"Downloaded {len(paths)} files")
```

!!! tip
    Re-running `download()` skips files that already exist. Safe to run repeatedly.

## Step 3: Mosaic into a single raster

```python
# VRT — instant, zero-copy
vrt = abovepy.mosaic(paths, output="frankfort.vrt")

# Or GeoTIFF if you need a standalone file
# tif = abovepy.mosaic(paths, output="frankfort.tif")
```

## Step 4: Generate a hillshade

```python
import numpy as np
import rasterio

with rasterio.open(str(vrt)) as src:
    dem = src.read(1)
    profile = src.profile

# Compute hillshade (simple Lambert shading)
dx, dy = np.gradient(dem, src.res[0], src.res[1])
slope = np.sqrt(dx**2 + dy**2)
aspect = np.arctan2(-dy, dx)

# Sun angle: azimuth 315, altitude 45 degrees
azimuth = np.radians(315)
altitude = np.radians(45)

hillshade = (
    np.sin(altitude) * np.cos(np.arctan(slope))
    + np.cos(altitude) * np.sin(np.arctan(slope))
    * np.cos(azimuth - aspect)
)
hillshade = np.clip(hillshade * 255, 0, 255).astype(np.uint8)
```

## Step 5: Visualize

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

axes[0].imshow(dem, cmap="terrain")
axes[0].set_title("DEM (2ft)")
axes[0].axis("off")

axes[1].imshow(hillshade, cmap="gray")
axes[1].set_title("Hillshade")
axes[1].axis("off")

plt.tight_layout()
plt.savefig("frankfort_hillshade.png", dpi=150, bbox_inches="tight")
plt.show()
```

## Step 6 (optional): Save hillshade as GeoTIFF

```python
profile.update(dtype="uint8", count=1, compress="deflate")

with rasterio.open("frankfort_hillshade.tif", "w", **profile) as dst:
    dst.write(hillshade, 1)
```

## ArcGIS Pro shortcut

The **DEM Hillshade** tool in the AbovePro toolbox does all of this in one click — search, download, mosaic, and hillshade generation with native ArcGIS rendering.
