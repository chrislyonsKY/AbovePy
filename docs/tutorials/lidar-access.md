# LiDAR Access

Work with KyFromAbove COPC and LAZ point cloud data.

## Prerequisites

```bash
pip install abovepy[lidar]
```

This installs [laspy](https://laspy.readthedocs.io/) for reading COPC and LAZ files.

!!! note
    LiDAR files are large. Phase 2 and 3 use [COPC](https://copc.io/) (Cloud-Optimized Point Cloud), which supports spatial indexing for efficient partial reads. Phase 1 uses classic LAZ.

## Search for LiDAR tiles

```python
import abovepy

# Phase 2 COPC tiles for Pike County
tiles = abovepy.search(county="Pike", product="laz_phase2")
print(f"Found {len(tiles)} tiles")
```

## Download tiles

```python
# Download all tiles (can be large!)
paths = abovepy.download(tiles, output_dir="./pike_lidar")

# Or download a subset
paths = abovepy.download(tiles.head(5), output_dir="./pike_lidar")
```

!!! warning
    LiDAR tiles can be hundreds of megabytes each. Start with a small area or a few tiles to estimate total download size. Check `tiles.file_size.sum()` before downloading.

## Read point clouds with laspy

```python
import laspy

las = laspy.read(str(paths[0]))

print(f"Points: {len(las.points):,}")
print(f"CRS: EPSG:3089")
print(f"Point format: {las.point_format}")
print(f"X range: {las.x.min():.1f} - {las.x.max():.1f}")
print(f"Y range: {las.y.min():.1f} - {las.y.max():.1f}")
print(f"Z range: {las.z.min():.1f} - {las.z.max():.1f}")
```

## Classify and filter points

LiDAR point clouds include classification codes:

| Code | Class |
|---|---|
| 1 | Unclassified |
| 2 | Ground |
| 3 | Low Vegetation |
| 4 | Medium Vegetation |
| 5 | High Vegetation |
| 6 | Building |
| 9 | Water |

```python
# Extract ground points only
ground_mask = las.classification == 2
ground_points = las.points[ground_mask]
print(f"Ground points: {len(ground_points):,}")
```

## Visualize a cross-section

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.array(las.x)
y = np.array(las.y)
z = np.array(las.z)

# Take a thin slice along the X axis
mid_y = (y.min() + y.max()) / 2
mask = np.abs(y - mid_y) < 50  # 50-foot wide strip

plt.figure(figsize=(14, 4))
plt.scatter(x[mask], z[mask], c=z[mask], s=0.1, cmap="terrain")
plt.xlabel("Easting (ft)")
plt.ylabel("Elevation (ft)")
plt.title("LiDAR Cross-Section")
plt.colorbar(label="Elevation (ft)")
plt.tight_layout()
plt.show()
```

## Phase comparison

| Phase | Format | Spatial Index | Streaming |
|---|---|---|---|
| Phase 1 | LAZ | No | Must download full file |
| Phase 2 | COPC | Yes | Bbox reads possible |
| Phase 3 | COPC (partial) | Yes | Bbox reads possible |

Phase 2 and 3 COPC files support reading only the points within a bounding box without downloading the entire file — ideal for large-area queries where you only need a small window.
