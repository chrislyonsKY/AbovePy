# SearchResult

The `SearchResult` class is the primary return type from `abovepy.search()`. It wraps a GeoDataFrame with workflow methods for download, preview, export, and comparison.

## Quick Reference

```python
import abovepy

result = abovepy.search(county="Franklin", product="dem_phase3")

# Inspect
result.count          # number of tiles
result.estimate_size() # {'tile_count': 42, 'avg_tile_mb': 5.0, 'total_mb': 210.0}
result.bbox           # bounding box of all tiles

# Workflow
paths = result.download("./data")        # concurrent download
url = result.preview()                    # preview image URL
m = result.map()                          # interactive notebook map
vrt = result.mosaic(output="out.vrt")     # mosaic tiles

# Export
gdf = result.to_geodataframe()            # raw GeoDataFrame
result.to_geoparquet("tiles.parquet")     # GeoParquet
geojson = result.to_geojson()             # GeoJSON string

# Compare
phase2 = abovepy.search(county="Franklin", product="dem_phase2")
overlap = result.compare(phase2)          # spatial overlap

# Subset
filtered = result.filter_by_bbox((-84.9, 38.15, -84.8, 38.25))
first_5 = result.head(5)
```

## API Reference

::: abovepy.result.SearchResult
