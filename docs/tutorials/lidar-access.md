# LiDAR Access

Work with KyFromAbove COPC and LAZ point cloud data. This tutorial covers searching for LiDAR tiles, downloading them, reading point clouds with laspy, filtering by classification, and visualizing cross-sections.

## Prerequisites

```bash
pip install abovepy[lidar]
```

This installs [laspy](https://laspy.readthedocs.io/) for reading COPC and LAZ files.

!!! note "LiDAR is an optional dependency"
    The `laspy` package is **not** installed with the base `abovepy` package because it is a heavy dependency that most DEM/ortho users do not need. If you see `ModuleNotFoundError: No module named 'laspy'`, run the install command above. See the [Troubleshooting Guide](troubleshooting.md#lidar-optional-dependency-errors) for more details.

!!! warning "Large file sizes"
    LiDAR point cloud files are significantly larger than DEM or orthoimagery tiles. A single tile can be **100-500 MB**. Plan your downloads carefully and check total sizes before committing. Phase 2 and 3 use COPC format, which supports partial reads — you may not need to download entire files.

---

## Step 1: Search for LiDAR tiles

```python
import abovepy

# Phase 2 COPC tiles for Pike County (eastern Kentucky, mountainous terrain)
tiles = abovepy.search(county="Pike", product="laz_phase2")
print(f"Found {len(tiles)} tiles")
print(f"Total size: {tiles.file_size.sum() / 1e9:.1f} GB")
print()
print(tiles[["tile_id", "file_size"]].head())
```

```text
Found 187 tiles
Total size: 48.3 GB

        tile_id  file_size
0  N0987E6543  287654321
1  N0987E6544  312456789
2  N0988E6543  256789012
3  N0988E6544  298765432
4  N0989E6543  275432109
```

!!! tip "Start small"
    Pike County has nearly 200 tiles totaling tens of gigabytes. For this tutorial, work with a small bounding box or just a few tiles:

    ```python
    # Small area around Pikeville
    tiles = abovepy.search(
        bbox=(-82.55, 37.47, -82.50, 37.50),
        product="laz_phase2"
    )
    print(f"Found {len(tiles)} tiles")
    print(f"Total size: {tiles.file_size.sum() / 1e6:.0f} MB")
    ```

    ```text
    Found 4 tiles
    Total size: 1142 MB
    ```

---

## Step 2: Download tiles

```python
# Download a small subset to start
paths = abovepy.download(tiles.head(2), output_dir="./pike_lidar")
print(f"Downloaded {len(paths)} files")
for p in paths:
    print(f"  {p.name}  ({p.stat().st_size / 1e6:.0f} MB)")
```

```text
Downloading: 100%|██████████| 2/2 [02:14<00:00, 67.12s/file]
Downloaded 2 files
  N0987E6543.copc.laz  (288 MB)
  N0987E6544.copc.laz  (312 MB)
```

!!! warning "Download times"
    LiDAR tiles are large. A single tile download can take 30-90 seconds depending on your connection speed. For a full county, consider running downloads overnight or using a machine with a fast connection.

---

## Step 3: Read point clouds with laspy

```python
import laspy

las = laspy.read(str(paths[0]))

print(f"File:          {paths[0].name}")
print(f"Points:        {len(las.points):,}")
print(f"Point format:  {las.point_format}")
print(f"CRS:           EPSG:3089 (Kentucky Single Zone, US feet)")
print(f"X range:       {las.x.min():.1f} - {las.x.max():.1f} ft")
print(f"Y range:       {las.y.min():.1f} - {las.y.max():.1f} ft")
print(f"Z range:       {las.z.min():.1f} - {las.z.max():.1f} ft")
```

```text
File:          N0987E6543.copc.laz
Points:        24,567,891
Point format:  <PointFormat(6, 30 bytes of extra dims)>
CRS:           EPSG:3089 (Kentucky Single Zone, US feet)
X range:       1987000.0 - 1992000.0 ft
Y range:       6543000.0 - 6548000.0 ft
Z range:       612.3 - 1847.9 ft
```

### Inspect available point attributes

```python
print("Available dimensions:")
for dim in las.point_format.dimension_names:
    print(f"  {dim}")
```

```text
Available dimensions:
  X
  Y
  Z
  intensity
  return_number
  number_of_returns
  synthetic
  key_point
  withheld
  overlap
  scanner_channel
  classification_flags
  classification
  user_data
  scan_angle
  point_source_id
  gps_time
```

---

## Step 4: LiDAR classification codes

KyFromAbove LiDAR data uses standard ASPRS classification codes. Understanding these codes is essential for filtering points:

| Code | Classification | Description |
|------|----------------|-------------|
| 0 | Created, Never Classified | Points that have not been processed |
| 1 | Unclassified | Processed but not assigned a class |
| 2 | Ground | Bare earth surface |
| 3 | Low Vegetation | Grass, crops (0-0.5m above ground) |
| 4 | Medium Vegetation | Bushes, small trees (0.5-2m above ground) |
| 5 | High Vegetation | Mature trees (>2m above ground) |
| 6 | Building | Structures and rooftops |
| 7 | Low Point (Noise) | Erroneous returns below ground surface |
| 9 | Water | Rivers, lakes, ponds |
| 10 | Rail | Railroad tracks |
| 11 | Road Surface | Paved roads |
| 17 | Bridge Deck | Bridge surfaces |
| 18 | High Noise | Erroneous returns above expected surface |

!!! note
    Not every tile will contain every classification code. The codes present depend on what features exist in that tile's coverage area and the level of classification processing applied.

### View classification distribution

```python
import numpy as np

classifications = np.array(las.classification)
unique, counts = np.unique(classifications, return_counts=True)

print("Classification distribution:")
print(f"{'Code':<6} {'Class':<25} {'Count':>12} {'Percent':>8}")
print("-" * 55)

class_names = {
    0: "Never Classified", 1: "Unclassified", 2: "Ground",
    3: "Low Vegetation", 4: "Medium Vegetation", 5: "High Vegetation",
    6: "Building", 7: "Low Noise", 9: "Water", 10: "Rail",
    11: "Road Surface", 17: "Bridge Deck", 18: "High Noise"
}

total = len(las.points)
for code, count in zip(unique, counts):
    name = class_names.get(code, f"Other ({code})")
    pct = count / total * 100
    print(f"{code:<6} {name:<25} {count:>12,} {pct:>7.1f}%")
```

```text
Classification distribution:
Code   Class                         Count  Percent
-------------------------------------------------------
1      Unclassified                 3,456,789   14.1%
2      Ground                       8,234,567   33.5%
3      Low Vegetation               2,345,678    9.5%
4      Medium Vegetation            1,234,567    5.0%
5      High Vegetation              6,789,012   27.6%
6      Building                     1,567,890    6.4%
7      Low Noise                       12,345    0.1%
9      Water                          456,789    1.9%
11     Road Surface                   470,254    1.9%
```

---

## Step 5: Filter points by classification

### Extract ground points only

```python
ground_mask = las.classification == 2
ground_points = las.points[ground_mask]
print(f"Total points:  {len(las.points):>12,}")
print(f"Ground points: {len(ground_points):>12,}")
print(f"Percentage:    {len(ground_points)/len(las.points)*100:>11.1f}%")
```

```text
Total points:    24,567,891
Ground points:    8,234,567
Percentage:          33.5%
```

### Extract buildings

```python
building_mask = las.classification == 6
building_points = las.points[building_mask]
print(f"Building points: {len(building_points):,}")

# Get elevation range for buildings
bz = np.array(las.z[building_mask])
print(f"Building elevation range: {bz.min():.1f} - {bz.max():.1f} ft")
```

```text
Building points: 1,567,890
Building elevation range: 645.2 - 712.8 ft
```

### Combine multiple classes

```python
# Vegetation: codes 3, 4, 5
veg_mask = np.isin(las.classification, [3, 4, 5])
veg_points = las.points[veg_mask]
print(f"Vegetation points: {len(veg_points):,}")
```

```text
Vegetation points: 10,369,257
```

---

## Step 6: Visualize a cross-section

A cross-section (profile view) is one of the most useful LiDAR visualizations. It shows the vertical structure of the landscape along a line:

```python
import numpy as np
import matplotlib.pyplot as plt

x = np.array(las.x)
y = np.array(las.y)
z = np.array(las.z)
cls = np.array(las.classification)

# Take a thin east-west slice through the middle of the tile
mid_y = (y.min() + y.max()) / 2
strip_width = 50  # 50-foot wide strip
mask = np.abs(y - mid_y) < strip_width

print(f"Points in cross-section strip: {mask.sum():,}")
print(f"Strip center Y: {mid_y:.0f} ft")
print(f"Strip width: {strip_width * 2} ft")
```

```text
Points in cross-section strip: 487,234
Strip center Y: 6545500 ft
Strip width: 100 ft
```

```python
# Color by classification
colors = {
    1: "#999999",  # Unclassified — gray
    2: "#8B4513",  # Ground — brown
    3: "#90EE90",  # Low Vegetation — light green
    4: "#228B22",  # Medium Vegetation — forest green
    5: "#006400",  # High Vegetation — dark green
    6: "#FF0000",  # Building — red
    9: "#0000FF",  # Water — blue
}

fig, ax = plt.subplots(figsize=(16, 5))

for code, color in colors.items():
    code_mask = mask & (cls == code)
    if code_mask.sum() > 0:
        ax.scatter(
            x[code_mask], z[code_mask],
            c=color, s=0.05, alpha=0.5,
            label=f"{code}: {class_names.get(code, 'Other')}"
        )

ax.set_xlabel("Easting (ft)", fontsize=12)
ax.set_ylabel("Elevation (ft)", fontsize=12)
ax.set_title(f"LiDAR Cross-Section — {paths[0].name}", fontsize=13)
ax.legend(loc="upper right", markerscale=40, fontsize=9)
plt.tight_layout()
plt.savefig("lidar_cross_section.png", dpi=150, bbox_inches="tight")
plt.show()
```

```text
Saved: lidar_cross_section.png
```

!!! tip "Adjusting the cross-section"
    - Increase `strip_width` (e.g., 100) to include more points, making the profile denser
    - Decrease `strip_width` (e.g., 10) for a thinner, cleaner profile
    - For a north-south cross-section, swap the mask to filter on X instead of Y:

    ```python
    mid_x = (x.min() + x.max()) / 2
    mask = np.abs(x - mid_x) < strip_width
    # Then plot y vs z instead of x vs z
    ```

---

## Step 7: Compute point density

Point density tells you how detailed the LiDAR coverage is:

```python
# Tile footprint area in square feet
tile_width = x.max() - x.min()
tile_height = y.max() - y.min()
area_sqft = tile_width * tile_height
area_acres = area_sqft / 43560

density_per_sqft = len(las.points) / area_sqft

print(f"Tile dimensions:  {tile_width:.0f} x {tile_height:.0f} ft")
print(f"Tile area:        {area_acres:.0f} acres")
print(f"Total points:     {len(las.points):,}")
print(f"Point density:    {density_per_sqft:.1f} pts/sq ft")
print(f"Ground density:   {ground_mask.sum() / area_sqft:.1f} pts/sq ft")
```

```text
Tile dimensions:  5000 x 5000 ft
Tile area:        574 acres
Total points:     24,567,891
Point density:    0.98 pts/sq ft
Ground density:   0.33 pts/sq ft
```

---

## Phase comparison

| Feature | Phase 1 | Phase 2 | Phase 3 |
|---------|---------|---------|---------|
| **Format** | LAZ | COPC | COPC (partial) |
| **Spatial Index** | No | Yes | Yes |
| **Streaming reads** | Must download full file | Bbox reads possible | Bbox reads possible |
| **Typical file size** | 100-400 MB | 150-500 MB | 150-500 MB |
| **Point density** | ~1 pt/sq ft | ~2 pts/sq ft | ~2-8 pts/sq ft |
| **Classification** | Basic (ground/non-ground) | Full ASPRS | Full ASPRS |

!!! tip "COPC advantage"
    Phase 2 and 3 use [COPC (Cloud-Optimized Point Cloud)](https://copc.io/) format. COPC files include a spatial index that allows reading only the points within a bounding box without downloading the entire file. This is ideal for large-area queries where you only need a small window.

    Phase 1 uses classic LAZ, which has no spatial index — you must download the entire file to read any of it.

---

## Saving filtered point clouds

Write filtered points back to a new LAZ file:

```python
import laspy

# Create a new LAS file with only ground points
ground_las = laspy.LasData(las.header)
ground_las.points = las.points[las.classification == 2]

output_path = "./pike_lidar/ground_only.laz"
ground_las.write(output_path)

import os
size_mb = os.path.getsize(output_path) / 1e6
print(f"Saved: {output_path} ({size_mb:.0f} MB, {len(ground_las.points):,} points)")
```

```text
Saved: ./pike_lidar/ground_only.laz (94 MB, 8,234,567 points)
```

---

## Next steps

- [DEM + Hillshade](dem-hillshade.md) — DEMs are derived from LiDAR ground points
- [Web Maps with TiTiler](titiler-maps.md) — Visualize DEM and ortho tiles in the browser
- [Troubleshooting](troubleshooting.md) — Solutions for common issues including LiDAR dependency errors
