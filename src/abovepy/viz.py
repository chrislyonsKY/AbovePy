"""Visualization helpers — URL builders and interactive notebook maps.

Two levels of functionality:

* **URL helpers** (no extra deps) — ``tile_url()``, ``preview_url()``
  are smart dispatchers that accept a product + bbox/county and return
  ready-to-use TiTiler tile/preview URLs.

* **Notebook display** (requires ``leafmap`` from the ``viz`` extra) —
  ``show()`` renders an interactive map in Jupyter using TiTiler tiles.
"""

from __future__ import annotations

from abovepy._constants import TITILER_PGSTAC_ENDPOINT
from abovepy.titiler import (
    DEFAULT_TILE_MATRIX_SET,
    collection_bbox_url,
    collection_tile_url,
    contour_tile_url,
    hillshade_tile_url,
    slope_tile_url,
    terrain_rgb_tile_url,
)

# Mapping from algorithm name to the terrain URL builder
_ALGORITHM_BUILDERS = {
    "hillshade": hillshade_tile_url,
    "slope": slope_tile_url,
    "contours": contour_tile_url,
    "terrainrgb": terrain_rgb_tile_url,
}


def tile_url(
    product: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    county: str | None = None,
    algorithm: str | None = None,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = TITILER_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a TileJSON URL for a product, with optional terrain algorithm.

    This is a convenience wrapper that resolves county names to bboxes and
    dispatches to the appropriate terrain helper when ``algorithm`` is set.

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
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (colormap_name, rescale, assets, etc.).

    Returns
    -------
    str
        TileJSON URL.
    """
    resolved_bbox = _resolve_bbox(bbox, county)

    if algorithm is not None:
        builder = _ALGORITHM_BUILDERS.get(algorithm)
        if builder is None:
            valid = ", ".join(sorted(_ALGORITHM_BUILDERS))
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. Valid: {valid}"
            )
        return builder(
            product,
            bbox=resolved_bbox,
            tile_matrix_set=tile_matrix_set,
            titiler_endpoint=titiler_endpoint,
            **kwargs,
        )

    return collection_tile_url(
        product,
        bbox=resolved_bbox,
        tile_matrix_set=tile_matrix_set,
        titiler_endpoint=titiler_endpoint,
        **kwargs,
    )


def preview_url(
    product: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    county: str | None = None,
    width: int = 512,
    height: int = 512,
    fmt: str = "png",
    titiler_endpoint: str = TITILER_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a rendered preview image URL for a product + bbox.

    Parameters
    ----------
    product : str
        Product key (e.g., ``"dem_phase3"``).
    bbox : tuple, optional
        Bounding box (xmin, ymin, xmax, ymax) in EPSG:4326.
        Required unless ``county`` is provided.
    county : str, optional
        Kentucky county name. Overrides ``bbox`` if provided.
    width : int
        Output width in pixels. Default 512.
    height : int
        Output height in pixels. Default 512.
    fmt : str
        Image format. Default ``"png"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (colormap_name, rescale, assets, etc.).

    Returns
    -------
    str
        Preview image URL.

    Raises
    ------
    ValueError
        If neither ``bbox`` nor ``county`` is provided.
    """
    resolved_bbox = _resolve_bbox(bbox, county)
    if resolved_bbox is None:
        raise ValueError("preview_url() requires either bbox= or county=")

    return collection_bbox_url(
        product,
        bbox=resolved_bbox,
        width=width,
        height=height,
        fmt=fmt,
        titiler_endpoint=titiler_endpoint,
        **kwargs,
    )


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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_bbox(
    bbox: tuple[float, float, float, float] | None,
    county: str | None,
) -> tuple[float, float, float, float] | None:
    """Resolve county name to bbox, or pass through bbox."""
    if county is not None:
        from abovepy.utils.bbox import get_county_bbox
        return get_county_bbox(county)
    return bbox
