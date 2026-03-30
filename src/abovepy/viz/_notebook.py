"""Notebook display — interactive maps via leafmap."""

from __future__ import annotations

from abovepy._constants import TITILER_PGSTAC_ENDPOINT
from abovepy.viz._urls import _resolve_bbox, tile_url


def show(
    product: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    county: str | None = None,
    algorithm: str | None = None,
    zoom: int | None = None,
    height: str = "600px",
    titiler_endpoint: str = TITILER_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> object:
    """Display an interactive tile map in a Jupyter notebook.

    Requires the ``viz`` extra: ``pip install abovepy[viz]``.

    Parameters
    ----------
    product : str
        Product key (e.g., ``"dem_phase3"``, ``"ortho_phase3"``).
    bbox : tuple, optional
        Bounding box (xmin, ymin, xmax, ymax) in EPSG:4326.
    county : str, optional
        Kentucky county name. Overrides ``bbox`` if provided.
    algorithm : str, optional
        Terrain algorithm: ``"hillshade"``, ``"slope"``, ``"contours"``,
        or ``"terrainrgb"``.
    zoom : int, optional
        Initial zoom level. Auto-detected if not set.
    height : str
        Map widget height. Default ``"600px"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters passed to the tile URL builder.

    Returns
    -------
    leafmap.Map
        An interactive map widget. Displays automatically in Jupyter.

    Raises
    ------
    ImportError
        If leafmap is not installed.
    """
    try:
        import leafmap  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "leafmap is required for show(). "
            "Install it with: pip install abovepy[viz]"
        ) from None

    resolved_bbox = _resolve_bbox(bbox, county)

    tilejson = tile_url(
        product,
        bbox=resolved_bbox,
        algorithm=algorithm,
        titiler_endpoint=titiler_endpoint,
        **kwargs,
    )

    # Build the map
    center_lat = 37.85
    center_lon = -85.75
    default_zoom = 7

    if resolved_bbox is not None:
        center_lon = (resolved_bbox[0] + resolved_bbox[2]) / 2
        center_lat = (resolved_bbox[1] + resolved_bbox[3]) / 2
        # Rough zoom from bbox span
        span = max(
            resolved_bbox[2] - resolved_bbox[0],
            resolved_bbox[3] - resolved_bbox[1],
        )
        if span > 0:
            import math
            default_zoom = int(math.log2(360 / span))
            default_zoom = max(5, min(default_zoom, 18))

    m = leafmap.Map(
        center=(center_lat, center_lon),
        zoom=zoom or default_zoom,
        height=height,
    )
    label = product
    if algorithm:
        label = f"{product} ({algorithm})"
    m.add_tile_layer(url=tilejson, name=label, attribution="KyFromAbove")

    return m
