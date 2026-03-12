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
