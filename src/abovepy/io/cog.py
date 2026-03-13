"""COG read operations via rasterio with /vsicurl/ and /vsis3/ support.

Supports windowed reads by bounding box with automatic CRS reprojection
so users can pass EPSG:4326 bboxes against EPSG:3089 data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def read_cog(
    source: str | Path,
    bbox: tuple[float, float, float, float] | None = None,
    crs: str | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Read a COG, optionally windowed to a bbox.

    Parameters
    ----------
    source : str or Path
        Local path, S3 URI, or HTTPS URL to a Cloud-Optimized GeoTIFF.
    bbox : tuple, optional
        Bounding box (xmin, ymin, xmax, ymax) for windowed read.
    crs : str, optional
        CRS of the bbox. Defaults to EPSG:4326 per project convention.
        If different from the source CRS, the bbox is reprojected.

    Returns
    -------
    tuple[numpy.ndarray, dict]
        (data, profile) — raster array and rasterio profile dict.
    """
    import rasterio
    from rasterio.windows import from_bounds

    vsi_path = _to_vsi_path(str(source))

    with rasterio.open(vsi_path) as src:
        if bbox is not None:
            read_bbox = bbox
            # Default to EPSG:4326 per project convention
            bbox_crs = crs or "EPSG:4326"
            if str(src.crs) != bbox_crs:
                read_bbox = _reproject_bbox(
                    bbox, bbox_crs, str(src.crs)
                )

            window = from_bounds(*read_bbox, transform=src.transform)
            # Clamp window to dataset bounds
            window = window.intersection(
                rasterio.windows.Window(0, 0, src.width, src.height)
            )
            data = src.read(window=window)
            win_transform = rasterio.windows.transform(window, src.transform)
            profile = src.profile.copy()
            profile.update(
                width=int(window.width),
                height=int(window.height),
                transform=win_transform,
            )
        else:
            data = src.read()
            profile = src.profile.copy()

    return data, profile


def inspect_cog(source: str | Path) -> dict[str, Any]:
    """Inspect a COG without reading pixel data.

    Parameters
    ----------
    source : str or Path
        Local path, S3 URI, or HTTPS URL.

    Returns
    -------
    dict
        Metadata dict with keys: path, width, height, crs, bounds,
        dtype, band_count, driver, nodata, transform.
    """
    import rasterio

    vsi_path = _to_vsi_path(str(source))

    with rasterio.open(vsi_path) as src:
        return {
            "path": str(source),
            "width": src.width,
            "height": src.height,
            "crs": str(src.crs),
            "bounds": tuple(src.bounds),
            "dtype": str(src.dtypes[0]),
            "band_count": src.count,
            "driver": src.driver,
            "nodata": src.nodata,
            "transform": tuple(src.transform),
        }


def _to_vsi_path(path: str) -> str:
    """Convert a path/URI to a GDAL VSI path for cloud-native access.

    Parameters
    ----------
    path : str
        Local path, s3:// URI, or https:// URL.

    Returns
    -------
    str
        GDAL-compatible VSI path.
    """
    if path.startswith("s3://"):
        return path.replace("s3://", "/vsis3/")
    if path.startswith(("https://", "http://")):
        return "/vsicurl/" + path
    return path


def _reproject_bbox(
    bbox: tuple[float, float, float, float],
    src_crs: str,
    dst_crs: str,
) -> tuple[float, float, float, float]:
    """Reproject a bbox between coordinate reference systems.

    Parameters
    ----------
    bbox : tuple
        (xmin, ymin, xmax, ymax) in source CRS.
    src_crs : str
        Source CRS string.
    dst_crs : str
        Destination CRS string.

    Returns
    -------
    tuple
        Reprojected (xmin, ymin, xmax, ymax).
    """
    from pyproj import Transformer

    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    x1, y1 = transformer.transform(bbox[0], bbox[1])
    x2, y2 = transformer.transform(bbox[2], bbox[3])
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
