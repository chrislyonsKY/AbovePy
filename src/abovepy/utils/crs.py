"""CRS conversion utilities — EPSG:4326 to/from EPSG:3089.

KyFromAbove uses EPSG:3089 (Kentucky Single Zone, US Survey Feet).
Users typically provide bbox in EPSG:4326 (lat/lon). This module
handles the conversion transparently.
"""

from __future__ import annotations


def transform_bbox(
    bbox: tuple[float, float, float, float],
    src_crs: str,
    dst_crs: str,
) -> tuple[float, float, float, float]:
    """Transform a bounding box between CRS.

    Parameters
    ----------
    bbox : tuple
        (xmin, ymin, xmax, ymax) in source CRS.
    src_crs : str
        Source CRS (e.g., "EPSG:4326").
    dst_crs : str
        Destination CRS (e.g., "EPSG:3089").

    Returns
    -------
    tuple
        Transformed (xmin, ymin, xmax, ymax).
    """
    from pyproj import Transformer

    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    xmin, ymin = transformer.transform(bbox[0], bbox[1])
    xmax, ymax = transformer.transform(bbox[2], bbox[3])
    return (xmin, ymin, xmax, ymax)


# Kentucky approximate extent in EPSG:4326
_KY_BBOX = (-89.6, 36.49, -81.96, 39.15)


def bbox_intersects_kentucky(
    bbox: tuple[float, float, float, float],
    crs: str = "EPSG:4326",
) -> bool:
    """Check if a bounding box intersects Kentucky's extent.

    Parameters
    ----------
    bbox : tuple
        (xmin, ymin, xmax, ymax).
    crs : str
        CRS of the bbox. Default "EPSG:4326".

    Returns
    -------
    bool
        True if the bbox overlaps Kentucky.
    """
    if crs != "EPSG:4326":
        bbox = transform_bbox(bbox, crs, "EPSG:4326")

    xmin, ymin, xmax, ymax = bbox
    ky_xmin, ky_ymin, ky_xmax, ky_ymax = _KY_BBOX

    return not (xmin > ky_xmax or xmax < ky_xmin or ymin > ky_ymax or ymax < ky_ymin)
