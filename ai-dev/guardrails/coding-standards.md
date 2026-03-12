# Coding Standards — abovepy (GPL-3.0)

These rules apply to ALL code in this project.

## Python
- Target: Python 3.10+
- NumPy docstring format on all public functions
- Type hints on all public functions
- pathlib.Path for all file paths
- httpx for HTTP, rasterio for rasters, geopandas for GeoDataFrames
- logging module (no bare print in library code)
- Specific exceptions (no bare except)

## Architecture
- Product is a parameter to search(), NOT a separate module
- Optional deps (pdal, laspy, boto3) lazy-imported inside functions
- VRT is default mosaic output — only write GeoTIFF if user requests .tif
- Never hardcode STAC collection IDs without discovery fallback
- County lookup is first-class — search(county="Pike") must work

## Data Handling
- Never require AWS credentials — the bucket is public
- All CRS conversion through pyproj
- Bbox validation at public API boundary
- Accept EPSG:4326 input, convert to EPSG:3089 internally

## ArcGIS Toolbox
- Lazy import abovepy in execute(), not at module level
- Use format() not f-strings for Pro 3.2 compatibility
- All errors via arcpy.AddError(), progress via arcpy.SetProgressor()
