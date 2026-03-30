"""Local terrain analysis — numpy-based DEM computation.

These functions operate on arrays returned by ``abovepy.read()`` and complement
the server-side TiTiler algorithms in ``abovepy.titiler``.  Server-side functions
are for tile serving/visualization; these local functions are for computation
and export.

Core functions use only numpy (implicit via rasterio).  Functions marked with
``Requires scipy`` need the ``analysis`` extra: ``pip install abovepy[analysis]``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import geopandas as gpd

from abovepy._exceptions import AnalysisError


def hillshade(
    dem: np.ndarray,
    resolution: float,
    azimuth: float = 315.0,
    altitude: float = 45.0,
) -> np.ndarray:
    """Compute hillshade from a DEM array.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    resolution : float
        Cell size in the DEM's native units (e.g., feet).
    azimuth : float
        Sun azimuth in degrees clockwise from north. Default 315 (NW).
    altitude : float
        Sun altitude in degrees above horizon. Default 45.

    Returns
    -------
    numpy.ndarray
        2D uint8 array (0-255) of shaded relief values.
    """
    dem = np.asarray(dem, dtype=np.float64)
    if dem.ndim != 2:
        raise AnalysisError(f"Expected 2D array, got {dem.ndim}D")

    az_rad = np.radians(360 - azimuth + 90)
    alt_rad = np.radians(altitude)

    dy, dx = np.gradient(dem, resolution)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect_rad = np.arctan2(-dy, dx)

    shade = np.sin(alt_rad) * np.cos(slope_rad) + np.cos(alt_rad) * np.sin(slope_rad) * np.cos(
        az_rad - aspect_rad
    )
    shade = np.clip(shade, 0, 1)
    return (shade * 255).astype(np.uint8)


def slope(
    dem: np.ndarray,
    resolution: float,
    units: str = "degrees",
) -> np.ndarray:
    """Compute slope from a DEM array.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    resolution : float
        Cell size in the DEM's native units.
    units : str
        ``"degrees"`` (0-90) or ``"percent"`` (0-inf). Default ``"degrees"``.

    Returns
    -------
    numpy.ndarray
        2D float array of slope values.
    """
    dem = np.asarray(dem, dtype=np.float64)
    if dem.ndim != 2:
        raise AnalysisError(f"Expected 2D array, got {dem.ndim}D")

    dy, dx = np.gradient(dem, resolution)
    rise = np.sqrt(dx**2 + dy**2)

    if units == "degrees":
        return np.degrees(np.arctan(rise))
    if units == "percent":
        return rise * 100
    raise AnalysisError(f"Invalid units '{units}'. Use 'degrees' or 'percent'.")


def aspect(
    dem: np.ndarray,
    resolution: float,
) -> np.ndarray:
    """Compute aspect (compass bearing) from a DEM array.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    resolution : float
        Cell size in the DEM's native units.

    Returns
    -------
    numpy.ndarray
        2D float array of aspect values in degrees (0=N, 90=E, 180=S, 270=W).
        Flat areas are -1.
    """
    dem = np.asarray(dem, dtype=np.float64)
    if dem.ndim != 2:
        raise AnalysisError(f"Expected 2D array, got {dem.ndim}D")

    dy, dx = np.gradient(dem, resolution)
    asp = np.degrees(np.arctan2(-dy, dx))
    # Convert from math convention to compass
    asp = (90 - asp) % 360

    # Mark flat areas
    flat = (dx == 0) & (dy == 0)
    asp[flat] = -1
    return asp  # type: ignore[return-value]


def flood_inundation(
    dem: np.ndarray,
    water_level: float,
    nodata: float | None = None,
) -> np.ndarray:
    """Compute flood inundation mask at a given water level.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    water_level : float
        Absolute water surface elevation in DEM units.
    nodata : float, optional
        Nodata value to exclude from flooding.

    Returns
    -------
    numpy.ndarray
        2D boolean array. True = flooded.
    """
    dem = np.asarray(dem, dtype=np.float64)
    mask = dem <= water_level
    if nodata is not None:
        mask &= dem != nodata
    return mask


def flood_depth(
    dem: np.ndarray,
    water_level: float,
    nodata: float | None = None,
) -> np.ndarray:
    """Compute flood depth at a given water level.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    water_level : float
        Absolute water surface elevation in DEM units.
    nodata : float, optional
        Nodata value to exclude.

    Returns
    -------
    numpy.ndarray
        2D float array of water depth. 0 where not flooded, positive
        where flooded. Nodata cells are NaN.
    """
    dem = np.asarray(dem, dtype=np.float64)
    depth = np.maximum(water_level - dem, 0.0)
    if nodata is not None:
        depth[dem == nodata] = np.nan
    return depth


def dem_diff(
    dem_before: np.ndarray,
    dem_after: np.ndarray,
) -> np.ndarray:
    """Compute elevation change between two DEMs.

    Both arrays must have the same shape.

    Parameters
    ----------
    dem_before : numpy.ndarray
        2D elevation array (earlier epoch).
    dem_after : numpy.ndarray
        2D elevation array (later epoch).

    Returns
    -------
    numpy.ndarray
        2D float array of change (after - before).
        Positive = fill/accretion, negative = cut/erosion.

    Raises
    ------
    AnalysisError
        If shapes do not match.
    """
    dem_before = np.asarray(dem_before, dtype=np.float64)
    dem_after = np.asarray(dem_after, dtype=np.float64)
    if dem_before.shape != dem_after.shape:
        raise AnalysisError(f"Shape mismatch: {dem_before.shape} vs {dem_after.shape}")
    return dem_after - dem_before  # type: ignore[return-value]


def elevation_profile(
    dem: np.ndarray,
    start: tuple[int, int],
    end: tuple[int, int],
    resolution: float,
    num_points: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract an elevation profile along a transect line.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    start : tuple[int, int]
        (row, col) start pixel coordinate.
    end : tuple[int, int]
        (row, col) end pixel coordinate.
    resolution : float
        Cell size for converting to ground distance.
    num_points : int, optional
        Number of sample points. Default: length of transect in pixels.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        (distances, elevations) -- 1D arrays of ground distance
        and elevation along the transect.
    """
    dem = np.asarray(dem, dtype=np.float64)
    r0, c0 = start
    r1, c1 = end

    pixel_length = np.sqrt((r1 - r0) ** 2 + (c1 - c0) ** 2)
    if num_points is None:
        num_points = max(int(pixel_length), 2)

    rows = np.linspace(r0, r1, num_points).astype(int)
    cols = np.linspace(c0, c1, num_points).astype(int)

    # Clamp to valid indices
    rows = np.clip(rows, 0, dem.shape[0] - 1)
    cols = np.clip(cols, 0, dem.shape[1] - 1)

    elevations = dem[rows, cols]
    pixel_dists = np.sqrt((rows - r0) ** 2 + (cols - c0) ** 2)
    distances = pixel_dists * resolution

    return distances, elevations


def contour_lines(
    dem: np.ndarray,
    transform: tuple[float, ...] | object,
    interval: float = 10.0,
    crs: str | None = None,
) -> gpd.GeoDataFrame:
    """Generate contour lines from a DEM as vector features.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    transform : tuple or affine.Affine
        Rasterio-style affine transform for georeferencing.
    interval : float
        Contour interval in elevation units. Default 10.
    crs : str, optional
        CRS string for the output GeoDataFrame.

    Returns
    -------
    geopandas.GeoDataFrame
        Contour lines with columns: ``elevation``, ``geometry`` (LineString).
    """
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from shapely.geometry import LineString

    dem = np.asarray(dem, dtype=np.float64)
    vmin, vmax = np.nanmin(dem), np.nanmax(dem)
    levels = np.arange(
        np.floor(vmin / interval) * interval,
        np.ceil(vmax / interval) * interval + interval,
        interval,
    )

    # Generate contours using matplotlib (no display)
    fig, ax = plt.subplots()
    cs = ax.contour(dem, levels=levels)
    plt.close(fig)

    # Extract affine transform parameters
    if hasattr(transform, "a"):
        # Affine object
        a, b, c, d, e, f = (
            transform.a,  # type: ignore[union-attr]
            transform.b,  # type: ignore[union-attr]
            transform.c,  # type: ignore[union-attr]
            transform.d,  # type: ignore[union-attr]
            transform.e,  # type: ignore[union-attr]
            transform.f,  # type: ignore[union-attr]
        )
    else:
        # Tuple (a, b, c, d, e, f, ...)
        t: tuple[float, ...] = tuple(transform)  # type: ignore[arg-type]
        a, b, c, d, e, f = t[0], t[1], t[2], t[3], t[4], t[5]

    rows = []
    for level_val, collection in zip(cs.levels, cs.allsegs, strict=True):
        for seg in collection:
            if len(seg) < 2:
                continue
            # Transform pixel coords to georeferenced coords
            geo_coords = [(a * x + b * y + c, d * x + e * y + f) for x, y in seg]
            rows.append(
                {
                    "elevation": float(level_val),
                    "geometry": LineString(geo_coords),
                }
            )

    return gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)


def zonal_stats(
    dem: np.ndarray,
    mask: np.ndarray,
    resolution: float,
) -> dict[str, float]:
    """Compute zonal statistics for a masked region.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    mask : numpy.ndarray
        2D boolean array. Statistics are computed where True.
    resolution : float
        Cell size in the DEM's native units.

    Returns
    -------
    dict[str, float]
        Keys: ``min``, ``max``, ``mean``, ``median``, ``std``,
        ``area``, ``cell_count``.
    """
    dem = np.asarray(dem, dtype=np.float64)
    mask = np.asarray(mask, dtype=bool)
    values = dem[mask]

    if values.size == 0:
        raise AnalysisError("No cells selected by mask.")

    cell_area = resolution**2
    return {
        "min": float(np.nanmin(values)),
        "max": float(np.nanmax(values)),
        "mean": float(np.nanmean(values)),
        "median": float(np.nanmedian(values)),
        "std": float(np.nanstd(values)),
        "area": float(values.size * cell_area),
        "cell_count": int(values.size),
    }


# ---------------------------------------------------------------------------
# Functions requiring scipy (analysis extra)
# ---------------------------------------------------------------------------


def _require_scipy() -> None:
    """Raise ImportError with install instructions if scipy is missing."""
    try:
        import scipy  # noqa: F401
    except ImportError:
        raise ImportError(
            "scipy is required for this function. Install it with: pip install abovepy[analysis]"
        ) from None


def volume(
    dem: np.ndarray,
    reference_elevation: float,
    mask: np.ndarray | None = None,
    resolution: float = 1.0,
) -> dict[str, float]:
    """Compute cut and fill volumes relative to a reference plane.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    reference_elevation : float
        Reference surface elevation.
    mask : numpy.ndarray, optional
        2D boolean array. If provided, only compute volume within
        True cells.
    resolution : float
        Cell size in the DEM's native units. Default 1.0.

    Returns
    -------
    dict[str, float]
        Keys: ``cut_volume``, ``fill_volume``, ``net_volume``,
        ``cut_area``, ``fill_area``. Volumes in cubic units,
        areas in square units.
    """
    dem = np.asarray(dem, dtype=np.float64)
    diff = dem - reference_elevation

    if mask is not None:
        diff = diff[np.asarray(mask, dtype=bool)]

    cell_area = resolution**2

    cut = diff[diff < 0]
    fill = diff[diff > 0]

    return {
        "cut_volume": float(np.abs(cut).sum() * cell_area),
        "fill_volume": float(fill.sum() * cell_area),
        "net_volume": float(diff.sum() * cell_area),
        "cut_area": float(cut.size * cell_area),
        "fill_area": float(fill.size * cell_area),
    }


def volume_from_surface(
    dem: np.ndarray,
    reference_surface: np.ndarray,
    mask: np.ndarray | None = None,
    resolution: float = 1.0,
) -> dict[str, float]:
    """Compute cut/fill volumes relative to a reference surface.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array (current surface).
    reference_surface : numpy.ndarray
        2D elevation array (original/reference surface).
    mask : numpy.ndarray, optional
        2D boolean mask for the area of interest.
    resolution : float
        Cell size.

    Returns
    -------
    dict[str, float]
        Same keys as ``volume()``.

    Raises
    ------
    AnalysisError
        If shapes do not match.
    """
    dem = np.asarray(dem, dtype=np.float64)
    reference_surface = np.asarray(reference_surface, dtype=np.float64)
    if dem.shape != reference_surface.shape:
        raise AnalysisError(f"Shape mismatch: {dem.shape} vs {reference_surface.shape}")

    diff = dem - reference_surface
    if mask is not None:
        diff = diff[np.asarray(mask, dtype=bool)]

    cell_area = resolution**2
    cut = diff[diff < 0]
    fill = diff[diff > 0]

    return {
        "cut_volume": float(np.abs(cut).sum() * cell_area),
        "fill_volume": float(fill.sum() * cell_area),
        "net_volume": float(diff.sum() * cell_area),
        "cut_area": float(cut.size * cell_area),
        "fill_area": float(fill.size * cell_area),
    }


def interpolate_reference_surface(
    dem: np.ndarray,
    mask: np.ndarray,
    method: str = "linear",
) -> np.ndarray:
    """Interpolate a reference surface from the edges of a masked region.

    Extracts elevation values at the boundary of the mask and
    interpolates across the interior. Useful for estimating the
    "original" surface before mining/excavation.

    Requires scipy.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    mask : numpy.ndarray
        2D boolean array of the area of interest.
    method : str
        Interpolation method: ``"linear"`` or ``"cubic"``. Default ``"linear"``.

    Returns
    -------
    numpy.ndarray
        2D elevation array of the interpolated reference surface.

    Raises
    ------
    ImportError
        If scipy is not installed.
    """
    _require_scipy()
    from scipy.interpolate import griddata
    from scipy.ndimage import binary_erosion

    dem = np.asarray(dem, dtype=np.float64)
    mask = np.asarray(mask, dtype=bool)

    # Find boundary cells (mask edges)
    interior = binary_erosion(mask)
    boundary = mask & ~interior

    boundary_rows, boundary_cols = np.where(boundary)
    boundary_elevations = dem[boundary_rows, boundary_cols]

    # Build interpolation grid over full array
    rows_grid, cols_grid = np.mgrid[0 : dem.shape[0], 0 : dem.shape[1]]

    surface = griddata(
        points=np.column_stack([boundary_rows, boundary_cols]),
        values=boundary_elevations,
        xi=(rows_grid, cols_grid),
        method=method,
        fill_value=np.nanmean(boundary_elevations),
    )

    return surface.astype(np.float64)  # type: ignore[return-value]


def relative_elevation_model(
    dem: np.ndarray,
    channel_points: np.ndarray,
    channel_elevations: np.ndarray,
    method: str = "linear",
) -> np.ndarray:
    """Compute a Relative Elevation Model (height above channel).

    Requires scipy.

    Parameters
    ----------
    dem : numpy.ndarray
        2D elevation array.
    channel_points : numpy.ndarray
        Nx2 array of (col, row) pixel coordinates along the channel.
    channel_elevations : numpy.ndarray
        1D array of elevation values at each channel point.
    method : str
        Interpolation method: ``"linear"`` or ``"nearest"``. Default ``"linear"``.

    Returns
    -------
    numpy.ndarray
        2D float array of height above the interpolated channel surface.
        Clipped to >= 0.

    Raises
    ------
    ImportError
        If scipy is not installed.
    """
    _require_scipy()
    from scipy.interpolate import griddata

    dem = np.asarray(dem, dtype=np.float64)
    channel_points = np.asarray(channel_points)
    channel_elevations = np.asarray(channel_elevations, dtype=np.float64)

    rows_grid, cols_grid = np.mgrid[0 : dem.shape[0], 0 : dem.shape[1]]

    # channel_points is (col, row), griddata expects (row, col) for consistency
    points = np.column_stack([channel_points[:, 1], channel_points[:, 0]])

    channel_surface = griddata(
        points=points,
        values=channel_elevations,
        xi=(rows_grid, cols_grid),
        method=method,
        fill_value=np.nanmean(channel_elevations),
    )

    rem = dem - channel_surface
    return np.maximum(rem, 0.0)  # type: ignore[return-value]
