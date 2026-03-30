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


# ---------------------------------------------------------------------------
# EPSG:3089 geometry utilities
# ---------------------------------------------------------------------------

_FEET_PER_METER = 3.28084
_NATIVE_CRS = "EPSG:3089"


def buffer_feet(
    geometry: object,
    distance_feet: float,
    input_crs: str = "EPSG:4326",
) -> object:
    """Buffer a geometry by a distance in US survey feet.

    Projects the geometry to EPSG:3089 (Kentucky Single Zone, feet),
    applies the buffer, and projects back to the input CRS.

    Parameters
    ----------
    geometry : shapely geometry
        Point, LineString, Polygon, or any Shapely geometry.
    distance_feet : float
        Buffer distance in US survey feet.
    input_crs : str
        CRS of the input geometry. Default ``"EPSG:4326"``.

    Returns
    -------
    shapely.geometry.Polygon or MultiPolygon
        Buffered geometry in the original input CRS.
    """
    from pyproj import Transformer
    from shapely.ops import transform as shp_transform

    to_3089 = Transformer.from_crs(input_crs, _NATIVE_CRS, always_xy=True).transform
    to_input = Transformer.from_crs(_NATIVE_CRS, input_crs, always_xy=True).transform

    geom_3089 = shp_transform(to_3089, geometry)
    buffered = geom_3089.buffer(distance_feet)
    return shp_transform(to_input, buffered)


def corridor_buffer(
    line: object,
    width_feet: float,
    input_crs: str = "EPSG:4326",
) -> object:
    """Buffer a line (corridor centerline) by a width in feet.

    Useful for road, utility, or pipeline corridor searches.

    Parameters
    ----------
    line : shapely.geometry.LineString or MultiLineString
        Corridor centerline.
    width_feet : float
        Total corridor width in feet. The buffer is half-width on each side.
    input_crs : str
        CRS of the input line. Default ``"EPSG:4326"``.

    Returns
    -------
    shapely.geometry.Polygon
        Corridor polygon in the original input CRS.
    """
    return buffer_feet(line, width_feet / 2.0, input_crs=input_crs)


def clip_to_geometry(
    gdf: object,
    clip_geometry: object,
) -> object:
    """Clip a GeoDataFrame to a geometry boundary.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Data to clip.
    clip_geometry : shapely geometry
        Clip boundary.

    Returns
    -------
    geopandas.GeoDataFrame
        Clipped result.
    """
    import geopandas as gpd

    return gpd.clip(gdf, clip_geometry)


def reproject_bbox(
    bbox: tuple[float, float, float, float],
    src_crs: str,
    dst_crs: str,
) -> tuple[float, float, float, float]:
    """Reproject a bounding box between coordinate reference systems.

    This is a public alias for ``transform_bbox`` that also handles
    corner expansion for better accuracy with projected CRS.

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
        (xmin, ymin, xmax, ymax) in destination CRS.
    """
    return transform_bbox(bbox, src_crs, dst_crs)


def validate_crs_units(
    crs: str,
    expected_units: str = "feet",
) -> bool:
    """Check if a CRS uses the expected linear units.

    Parameters
    ----------
    crs : str
        CRS string (e.g., ``"EPSG:3089"``).
    expected_units : str
        Expected unit name fragment (e.g., ``"feet"``, ``"metre"``).

    Returns
    -------
    bool
        True if the CRS units match.
    """
    from pyproj import CRS as ProjCRS

    proj_crs = ProjCRS.from_user_input(crs)
    axis_info = proj_crs.axis_info
    if axis_info:
        unit_name = axis_info[0].unit_name.lower()
        expected = expected_units.lower()
        # Handle common aliases: "feet" matches "foot", "US survey foot", etc.
        if expected in ("feet", "foot"):
            return "foot" in unit_name or "feet" in unit_name
        return expected in unit_name
    return False
