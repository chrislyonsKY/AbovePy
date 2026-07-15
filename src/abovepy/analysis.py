"""High-level elevation analysis — search + streamed-read orchestration.

Wraps the existing search and windowed-read machinery so common terrain
questions become one-liners::

    import abovepy

    elev = abovepy.sample((-84.87, 38.20))
    df = abovepy.profile([(-84.9, 38.15), (-84.8, 38.25)])
    stats = abovepy.zonal_stats(polygon)
    diff, profile = abovepy.change_detection(bbox)

All functions stream only the pixels they need from the KyFromAbove COGs
(no downloads) and raise :class:`~abovepy._exceptions.AnalysisError` when
no tiles cover the area of interest.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from abovepy._exceptions import AnalysisError

if TYPE_CHECKING:
    import pandas as pd
    from shapely.geometry import LineString, Polygon
    from shapely.geometry.base import BaseGeometry

logger = logging.getLogger(__name__)

# AOIs needing more tiles than this should be downloaded and mosaicked
# explicitly — streaming that many remote reads is slower than downloading.
MAX_ANALYSIS_TILES = 24

_POINT_PAD_DEG = 1e-4  # ~30 ft padding around point AOIs


def _squeeze_band(data: np.ndarray) -> np.ndarray:
    """Reduce (bands, h, w) to the first band as 2D."""
    arr = np.asarray(data)
    if arr.ndim == 3:
        arr = arr[0]
    return arr


def _guard_result(result: Any, product: str, where: str) -> None:
    """Raise AnalysisError for empty or oversized search results."""
    if result.empty:
        raise AnalysisError(f"No {product} tiles cover {where}.")
    if result.count > MAX_ANALYSIS_TILES:
        raise AnalysisError(
            f"The area of interest spans {result.count} {product} tiles "
            f"(limit {MAX_ANALYSIS_TILES} for streamed analysis). Download and "
            f"mosaic instead: result.download(...) then abovepy.mosaic(...)."
        )


def _read_aoi(
    result: Any,
    bbox: tuple[float, float, float, float],
    crs: str = "EPSG:4326",
) -> tuple[np.ndarray, dict[str, Any]]:
    """Stream the AOI window from one or more result tiles.

    Single tile: direct windowed read. Multiple tiles: in-memory
    rasterio merge over ``/vsicurl/`` sources bounded to the AOI.

    Returns a 2D array (first band) and its rasterio profile.
    """
    from abovepy.io.cog import read_cog

    urls = [u for u in result.tiles["asset_url"].tolist() if u]
    if not urls:
        raise AnalysisError("Result tiles have no asset URLs to read.")

    if len(urls) == 1:
        data, profile = read_cog(urls[0], bbox=bbox, crs=crs)
        return _squeeze_band(data), dict(profile)

    import rasterio
    from rasterio.merge import merge

    from abovepy.io.cog import _to_vsi_path
    from abovepy.utils.crs import reproject_bbox

    datasets = [rasterio.open(_to_vsi_path(u)) for u in urls]
    try:
        target_crs = str(datasets[0].crs)
        bounds = bbox if target_crs == crs else reproject_bbox(bbox, crs, target_crs)
        data, transform = merge(datasets, bounds=bounds)
        profile = dict(datasets[0].profile)
        profile.update(
            height=data.shape[1],
            width=data.shape[2],
            count=data.shape[0],
            transform=transform,
        )
    finally:
        for ds in datasets:
            ds.close()
    return _squeeze_band(data), profile


def _nodata_to_nan(dem: np.ndarray, profile: dict[str, Any]) -> np.ndarray:
    """Return a float array with the profile's nodata replaced by NaN."""
    arr = np.asarray(dem, dtype=np.float64)
    nodata = profile.get("nodata")
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    return arr


def _project_points(
    points: list[tuple[float, float]],
    src_crs: str,
    dst_crs: str,
) -> list[tuple[float, float]]:
    """Reproject (x, y) pairs between CRSs."""
    if src_crs == dst_crs:
        return points
    from pyproj import Transformer

    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    xs, ys = transformer.transform([p[0] for p in points], [p[1] for p in points])
    return list(zip(xs, ys, strict=True))


def _sample_dem(
    dem: np.ndarray,
    profile: dict[str, Any],
    points: list[tuple[float, float]],
    crs: str,
) -> list[float]:
    """Sample DEM values at (x, y) points given in ``crs``."""
    from rasterio.transform import rowcol

    dem = _nodata_to_nan(dem, profile)
    native = _project_points(points, crs, str(profile.get("crs")))

    values: list[float] = []
    for x, y in native:
        row, col = rowcol(profile["transform"], x, y)
        if 0 <= row < dem.shape[0] and 0 <= col < dem.shape[1]:
            values.append(float(dem[row, col]))
        else:
            logger.warning("Point (%.6f, %.6f) falls outside the read window.", x, y)
            values.append(float("nan"))
    return values


def sample(
    point: tuple[float, float] | list[tuple[float, float]],
    product: str = "dem_phase3",
    *,
    crs: str = "EPSG:4326",
) -> float | list[float]:
    """Elevation at one or more points.

    Parameters
    ----------
    point : tuple or list of tuples
        (longitude, latitude) — or a list of such points. Coordinates
        are interpreted in ``crs``.
    product : str
        DEM product key. Default ``"dem_phase3"``.
    crs : str
        CRS of the input coordinates. Default EPSG:4326.

    Returns
    -------
    float or list[float]
        Elevation in the product's native units (US survey feet).
        ``nan`` where the point has no data.

    Raises
    ------
    AnalysisError
        If no tiles cover the point(s).
    """
    import abovepy

    single = (
        isinstance(point, tuple)
        and len(point) == 2
        and all(isinstance(v, int | float) for v in point)
    )
    if single:
        points = [cast("tuple[float, float]", point)]
    else:
        multi = cast("list[tuple[float, float]]", point)
        points = [(float(p[0]), float(p[1])) for p in multi]
    if not points:
        raise AnalysisError("No points provided.")

    lonlat = _project_points(points, crs, "EPSG:4326")
    xs = [p[0] for p in lonlat]
    ys = [p[1] for p in lonlat]
    bbox = (
        min(xs) - _POINT_PAD_DEG,
        min(ys) - _POINT_PAD_DEG,
        max(xs) + _POINT_PAD_DEG,
        max(ys) + _POINT_PAD_DEG,
    )

    result = abovepy.search(bbox=bbox, product=product)
    where = f"point {points[0]}" if single else f"{len(points)} points"
    _guard_result(result, product, where)

    dem, raster_profile = _read_aoi(result, bbox)
    values = _sample_dem(dem, raster_profile, lonlat, "EPSG:4326")
    return values[0] if single else values


def profile(
    line: LineString | list[tuple[float, float]],
    product: str = "dem_phase3",
    n_points: int = 100,
    *,
    crs: str = "EPSG:4326",
) -> pd.DataFrame:
    """Elevation profile along a transect line.

    Distances are measured in US survey feet along the line (computed
    in EPSG:3089).

    Parameters
    ----------
    line : LineString or list of (x, y) tuples
        The transect, in ``crs`` coordinates.
    product : str
        DEM product key. Default ``"dem_phase3"``.
    n_points : int
        Number of evenly spaced sample points. Default 100.
    crs : str
        CRS of the input line. Default EPSG:4326.

    Returns
    -------
    pandas.DataFrame
        Columns: ``distance_ft``, ``elevation``, ``lon``, ``lat``.

    Raises
    ------
    AnalysisError
        If no tiles cover the line.
    """
    import pandas as pd
    from pyproj import Transformer
    from shapely.geometry import LineString as ShapelyLineString
    from shapely.ops import transform as shapely_transform

    import abovepy

    if n_points < 2:
        raise AnalysisError("profile() needs n_points >= 2.")

    geom = line if hasattr(line, "coords") else ShapelyLineString(line)

    # Work in EPSG:3089 so distances are true feet
    to_native = Transformer.from_crs(crs, "EPSG:3089", always_xy=True)
    to_lonlat = Transformer.from_crs("EPSG:3089", "EPSG:4326", always_xy=True)
    line_ft = shapely_transform(to_native.transform, geom)

    distances = np.linspace(0.0, line_ft.length, n_points)
    points_ft = [line_ft.interpolate(d) for d in distances]
    lonlat = [to_lonlat.transform(p.x, p.y) for p in points_ft]

    xs = [p[0] for p in lonlat]
    ys = [p[1] for p in lonlat]
    bbox = (
        min(xs) - _POINT_PAD_DEG,
        min(ys) - _POINT_PAD_DEG,
        max(xs) + _POINT_PAD_DEG,
        max(ys) + _POINT_PAD_DEG,
    )

    result = abovepy.search(bbox=bbox, product=product)
    _guard_result(result, product, "the transect line")

    dem, raster_profile = _read_aoi(result, bbox)
    elevations = _sample_dem(dem, raster_profile, lonlat, "EPSG:4326")

    return pd.DataFrame(
        {
            "distance_ft": distances,
            "elevation": elevations,
            "lon": xs,
            "lat": ys,
        }
    )


def zonal_stats(
    polygon: Polygon | BaseGeometry,
    product: str = "dem_phase3",
    *,
    crs: str = "EPSG:4326",
) -> dict[str, float]:
    """Elevation statistics within a polygon.

    Parameters
    ----------
    polygon : shapely geometry
        Area of interest, in ``crs`` coordinates.
    product : str
        DEM product key. Default ``"dem_phase3"``.
    crs : str
        CRS of the input polygon. Default EPSG:4326.

    Returns
    -------
    dict[str, float]
        Keys: ``min``, ``max``, ``mean``, ``median``, ``std``,
        ``area``, ``cell_count``. Area is in squared native units
        (square feet for KyFromAbove DEMs).

    Raises
    ------
    AnalysisError
        If no tiles cover the polygon or it selects no cells.
    """
    from pyproj import Transformer
    from rasterio.features import geometry_mask
    from shapely.ops import transform as shapely_transform

    import abovepy
    from abovepy import terrain

    to_lonlat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    polygon_lonlat = (
        polygon if crs == "EPSG:4326" else shapely_transform(to_lonlat.transform, polygon)
    )

    result = abovepy.search(geometry=polygon_lonlat, product=product)
    _guard_result(result, product, "the polygon")

    dem, raster_profile = _read_aoi(result, polygon_lonlat.bounds)
    dem = _nodata_to_nan(dem, raster_profile)

    native_crs = str(raster_profile.get("crs"))
    to_native = Transformer.from_crs("EPSG:4326", native_crs, always_xy=True)
    polygon_native = shapely_transform(to_native.transform, polygon_lonlat)

    mask = ~geometry_mask(
        [polygon_native.__geo_interface__],
        out_shape=dem.shape,
        transform=raster_profile["transform"],
    )
    # Exclude nodata cells from the statistics
    mask &= ~np.isnan(dem)
    if not mask.any():
        raise AnalysisError("The polygon selects no valid DEM cells.")

    resolution = abs(raster_profile["transform"].a)
    return terrain.zonal_stats(dem, mask, resolution)


def change_detection(
    bbox: tuple[float, float, float, float],
    product_before: str = "dem_phase2",
    product_after: str = "dem_phase3",
    *,
    crs: str = "EPSG:4326",
    output: str | Any | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Elevation-change map between two DEM products over a bbox.

    The later product is resampled onto the earlier product's grid
    (bilinear) before differencing, so mixed-resolution phases compare
    cleanly.

    Parameters
    ----------
    bbox : tuple
        (xmin, ymin, xmax, ymax) in ``crs``.
    product_before : str
        Earlier DEM product key. Default ``"dem_phase2"``.
    product_after : str
        Later DEM product key. Default ``"dem_phase3"``.
    crs : str
        CRS of the bbox. Default EPSG:4326.
    output : str or Path, optional
        Write the difference raster to this GeoTIFF path.

    Returns
    -------
    tuple[numpy.ndarray, dict]
        (difference, profile). Positive values = elevation gain
        (fill/accretion), negative = loss (cut/erosion). NaN where
        either epoch has no data.

    Raises
    ------
    AnalysisError
        If either product has no tiles over the bbox.
    """
    import abovepy
    from abovepy import terrain

    result_before = abovepy.search(bbox=bbox, product=product_before, crs=crs)
    _guard_result(result_before, product_before, "the bbox")
    result_after = abovepy.search(bbox=bbox, product=product_after, crs=crs)
    _guard_result(result_after, product_after, "the bbox")

    dem_before, profile_before = _read_aoi(result_before, bbox, crs=crs)
    dem_after, profile_after = _read_aoi(result_after, bbox, crs=crs)

    dem_before = _nodata_to_nan(dem_before, profile_before)
    dem_after = _nodata_to_nan(dem_after, profile_after)

    if dem_before.shape != dem_after.shape or profile_before.get("transform") != profile_after.get(
        "transform"
    ):
        dem_after = _resample_onto(dem_after, profile_after, dem_before.shape, profile_before)

    diff = terrain.dem_diff(dem_before, dem_after)

    out_profile = dict(profile_before)
    out_profile.update(count=1, dtype="float32", nodata=None)

    if output is not None:
        from abovepy.export import to_geotiff

        to_geotiff(diff.astype(np.float32), out_profile, output)

    return diff, out_profile


def _resample_onto(
    data: np.ndarray,
    src_profile: dict[str, Any],
    dst_shape: tuple[int, ...],
    dst_profile: dict[str, Any],
) -> np.ndarray:
    """Reproject/resample ``data`` onto the destination grid (bilinear)."""
    from rasterio.warp import Resampling, reproject

    destination = np.full(dst_shape, np.nan, dtype=np.float64)
    reproject(
        source=np.asarray(data, dtype=np.float64),
        destination=destination,
        src_transform=src_profile["transform"],
        src_crs=src_profile.get("crs"),
        dst_transform=dst_profile["transform"],
        dst_crs=dst_profile.get("crs"),
        resampling=Resampling.bilinear,
        src_nodata=np.nan,
        dst_nodata=np.nan,
    )
    return destination
