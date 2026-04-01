# Validating Cloud-Native Formats

KyFromAbove data uses [Cloud-Optimized GeoTIFF (COG)](https://guide.cloudnativegeo.org/cloud-optimized-geotiffs/intro.html) for raster products and [Cloud-Optimized Point Cloud (COPC)](https://copc.io/) for LiDAR. These formats enable efficient HTTP range-request access — but only if the files are structured correctly.

abovepy provides built-in validation to confirm files meet cloud-native requirements, with optional deep validation via [rio-cogeo](https://cogeotiff.github.io/rio-cogeo/).

## Quick check

```python
import abovepy

result = abovepy.validate("data/dem_tile.tif")
print(result)
# COG VALID — 5/5 checks passed: data/dem_tile.tif
```

## What gets checked

### COG (GeoTIFF) — built-in checks

| Check | Requirement |
|---|---|
| `geotiff_format` | File is a valid GeoTIFF |
| `has_crs` | Coordinate reference system is defined |
| `internal_tiling` | Data is stored in tiles, not strips |
| `has_overviews` | Internal overview pyramids exist |
| `compression` | Data is compressed (LZW, Deflate, etc.) |

A file that passes all four required checks (`geotiff_format`, `has_crs`, `internal_tiling`, `has_overviews`) is classified as **COG**. Otherwise it's reported as **GeoTIFF**.

### COG — deep validation (rio-cogeo)

```python
result = abovepy.validate("data/dem_tile.tif", deep=True)
```

When `deep=True`, abovepy uses [rio-cogeo](https://cogeotiff.github.io/rio-cogeo/) for thorough validation including IFD ordering, ghost overview detection, and block alignment. Install with:

```bash
pip install rio-cogeo
```

If rio-cogeo is not installed, `deep=True` falls back to built-in checks with a warning.

### COPC (Point Cloud)

| Check | Requirement |
|---|---|
| `copc_format` | COPC VLR and spatial index present |
| `has_crs` | CRS defined in VLR records |
| `point_format` | Standard COPC point format (6, 7, or 8) |
| `point_count` | File contains points |

```python
result = abovepy.validate("data/lidar_tile.copc.laz")
print(result.checks)
```

## Inspecting results

The `ValidationResult` provides structured access to individual checks:

```python
result = abovepy.validate("data/dem_tile.tif")

# Overall status
print(result.is_valid)   # True
print(result.format)     # "COG"

# Individual checks
for check in result.checks:
    status = "✓" if check.passed else "✗"
    print(f"  {status} {check.name}: {check.message}")

# Access specific check details
tiling = next(c for c in result.checks if c.name == "internal_tiling")
print(tiling.detail)  # {"blockxsize": 512, "blockysize": 512}
```

## Validating search results

After a search, validate a sample of tiles directly from their remote URLs:

```python
tiles = abovepy.search(county="Franklin", product="dem_phase3")

# Spot-check 5 tiles (default)
results = tiles.validate_format()
for r in results:
    print(r)

# Validate all tiles
results = tiles.validate_format(sample=0)

# Deep validation
results = tiles.validate_format(deep=True)
```

## Validating remote files

abovepy validates remote COGs and COPC files via HTTP range requests — no download needed:

```python
# HTTPS URL
result = abovepy.validate("https://kyfromabove.s3.us-west-2.amazonaws.com/dem-phase3/N079E278.tif")

# S3 URI
result = abovepy.validate("s3://kyfromabove/dem-phase3/N079E278.tif")
```

## Command-line validation

You can also use standard tools directly:

```bash
# COG validation with rio-cogeo
rio cogeo validate data/dem_tile.tif

# COPC metadata with pdal
pdal info data/lidar_tile.copc.laz --metadata
```

## Further reading

- [Cloud-Optimized Geospatial Formats Guide](https://guide.cloudnativegeo.org/)
- [STAC Best Practices](https://github.com/radiantearth/stac-best-practices/)
- [rio-cogeo documentation](https://cogeotiff.github.io/rio-cogeo/)
- [COPC specification](https://copc.io/)
