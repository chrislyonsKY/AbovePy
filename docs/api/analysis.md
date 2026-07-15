# Analysis

High-level elevation analysis — search + streamed windowed reads, no
downloads. All functions accept EPSG:4326 coordinates by default and
return values in the product's native units (US survey feet).

## Quick Reference

```python
import abovepy
from shapely.geometry import box

# Elevation at one or more points
elev = abovepy.sample((-84.87, 38.20))
elevs = abovepy.sample([(-84.87, 38.20), (-84.86, 38.21)])

# Elevation profile along a transect (distances in true feet)
df = abovepy.profile([(-84.9, 38.15), (-84.8, 38.25)], n_points=200)
df.plot(x="distance_ft", y="elevation")

# Statistics within a polygon
stats = abovepy.zonal_stats(box(-84.88, 38.16, -84.82, 38.24))

# Cross-phase elevation change
diff, profile = abovepy.change_detection(
    (-84.9, 38.15, -84.8, 38.25),
    product_before="dem_phase2",
    product_after="dem_phase3",
)
```

AOIs spanning more than 24 tiles are rejected with a pointer to
`download()` + `mosaic()` — streaming that many remote reads is slower
than downloading.

## API Reference

::: abovepy.analysis.sample

::: abovepy.analysis.profile

::: abovepy.analysis.zonal_stats

::: abovepy.analysis.change_detection
