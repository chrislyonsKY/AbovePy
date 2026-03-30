# I/O — Raster & Point Cloud

## COG (Cloud-Optimized GeoTIFF)

Read raster tiles locally or stream windows directly from S3/HTTPS
using GDAL virtual filesystems (`/vsicurl/`, `/vsis3/`).

::: abovepy.io.cog
    options:
      members:
        - read_cog
        - inspect_cog

## Point Cloud (COPC / LAZ)

!!! note "Optional dependency"
    Requires `pip install abovepy[lidar]` (laspy).

::: abovepy.io.pointcloud
    options:
      members:
        - read_pointcloud
        - inspect_pointcloud
