"""TiTiler URL helpers — generates tile URLs for web map integration.

This module does NOT depend on or import TiTiler. It constructs URLs
that a running TiTiler instance can serve. TiTiler itself is external.

Two types of helpers are provided:

* **COG / Mosaic** — for standalone TiTiler (``/cog/...``, ``/mosaic/...``).
  These require individual COG URLs as parameters.
* **pgSTAC** — for TiTiler-pgSTAC (``/collections/...``, ``/searches/...``).
  These work against the STAC database directly so you only need a
  collection ID and optional bbox — no individual asset URLs required.
"""

from __future__ import annotations

from urllib.parse import quote_plus, urlencode

from abovepy._constants import TITILER_ENDPOINT, TITILER_PGSTAC_ENDPOINT
from abovepy.products import PRODUCTS

DEFAULT_TITILER_ENDPOINT = TITILER_ENDPOINT
DEFAULT_PGSTAC_ENDPOINT = TITILER_PGSTAC_ENDPOINT
DEFAULT_TILE_MATRIX_SET = "WebMercatorQuad"


def cog_tile_url(
    cog_url: str,
    titiler_endpoint: str = DEFAULT_TITILER_ENDPOINT,
) -> str:
    """Generate a TiTiler tile URL for a COG.

    Parameters
    ----------
    cog_url : str
        URL to the Cloud-Optimized GeoTIFF.
    titiler_endpoint : str
        TiTiler service URL.

    Returns
    -------
    str
        TileJSON URL for use with MapLibre/Leaflet.
    """
    encoded = quote_plus(cog_url)
    return f"{titiler_endpoint}/cog/tilejson.json?url={encoded}"


def cog_preview_url(
    cog_url: str,
    titiler_endpoint: str = DEFAULT_TITILER_ENDPOINT,
    max_size: int = 1024,
) -> str:
    """Generate a TiTiler preview image URL.

    Parameters
    ----------
    cog_url : str
        URL to the COG.
    titiler_endpoint : str
        TiTiler service URL.
    max_size : int
        Maximum dimension in pixels.

    Returns
    -------
    str
        Preview PNG URL.
    """
    encoded = quote_plus(cog_url)
    return f"{titiler_endpoint}/cog/preview.png?url={encoded}&max_size={max_size}"


def cog_stats_url(
    cog_url: str,
    titiler_endpoint: str = DEFAULT_TITILER_ENDPOINT,
) -> str:
    """Generate a TiTiler statistics URL for a COG.

    Parameters
    ----------
    cog_url : str
        URL to the COG.
    titiler_endpoint : str
        TiTiler service URL.

    Returns
    -------
    str
        Statistics JSON URL.
    """
    encoded = quote_plus(cog_url)
    return f"{titiler_endpoint}/cog/statistics?url={encoded}"


def cog_info_url(
    cog_url: str,
    titiler_endpoint: str = DEFAULT_TITILER_ENDPOINT,
) -> str:
    """Generate a TiTiler info URL for a COG.

    Parameters
    ----------
    cog_url : str
        URL to the COG.
    titiler_endpoint : str
        TiTiler service URL.

    Returns
    -------
    str
        Info JSON URL (bounds, CRS, band info).
    """
    encoded = quote_plus(cog_url)
    return f"{titiler_endpoint}/cog/info?url={encoded}"


def cog_bounds_url(
    cog_url: str,
    titiler_endpoint: str = DEFAULT_TITILER_ENDPOINT,
) -> str:
    """Generate a TiTiler bounds URL for a COG.

    Parameters
    ----------
    cog_url : str
        URL to the COG.
    titiler_endpoint : str
        TiTiler service URL.

    Returns
    -------
    str
        Bounds JSON URL.
    """
    encoded = quote_plus(cog_url)
    return f"{titiler_endpoint}/cog/bounds?url={encoded}"


def mosaic_tile_url(
    cog_urls: list[str],
    titiler_endpoint: str = DEFAULT_TITILER_ENDPOINT,
) -> str:
    """Generate a TiTiler mosaic TileJSON URL from multiple COGs.

    This is the programmatic equivalent of the MosaicJSON approach used
    in KyFromAbove GIS workshop materials — but constructed as a URL
    rather than requiring a separate mosaic JSON file.

    Parameters
    ----------
    cog_urls : list[str]
        URLs to Cloud-Optimized GeoTIFFs.
    titiler_endpoint : str
        TiTiler service URL.

    Returns
    -------
    str
        TileJSON URL for the mosaic, usable with MapLibre/Leaflet.
    """
    params = "&".join(f"url={quote_plus(u)}" for u in cog_urls)
    return f"{titiler_endpoint}/mosaic/tilejson.json?{params}"


# ---------------------------------------------------------------------------
# pgSTAC helpers — collection-based (no individual COG URLs needed)
# ---------------------------------------------------------------------------


def _resolve_collection_id(product_or_collection: str) -> str:
    """Accept a product key (``dem_phase3``) or raw collection ID (``dem-phase3``)."""
    if product_or_collection in PRODUCTS:
        return PRODUCTS[product_or_collection].collection_id
    return product_or_collection


def _pgstac_query_string(
    bbox: tuple[float, float, float, float] | None = None,
    datetime: str | None = None,
    assets: str | list[str] | None = None,
    colormap_name: str | None = None,
    rescale: str | None = None,
    algorithm: str | None = None,
    **extra: str,
) -> str:
    """Build a query string for pgSTAC tile endpoints."""
    params: dict[str, str] = {}
    if bbox is not None:
        params["bbox"] = ",".join(str(v) for v in bbox)
    if datetime is not None:
        params["datetime"] = datetime
    if assets is not None:
        params["assets"] = ",".join(assets) if isinstance(assets, list) else assets
    if colormap_name is not None:
        params["colormap_name"] = colormap_name
    if rescale is not None:
        params["rescale"] = rescale
    if algorithm is not None:
        params["algorithm"] = algorithm
    params.update(extra)
    return urlencode(params) if params else ""


def collection_tile_url(
    collection: str,
    bbox: tuple[float, float, float, float] | None = None,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a TileJSON URL for a STAC collection via TiTiler-pgSTAC.

    This is the simplest way to get dynamic tiles for KyFromAbove data —
    just provide a product name and optional bbox.

    Parameters
    ----------
    collection : str
        Product key (e.g., ``"dem_phase3"``) or STAC collection ID
        (e.g., ``"dem-phase3"``).
    bbox : tuple, optional
        Bounding box filter as (xmin, ymin, xmax, ymax) in EPSG:4326.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (assets, colormap_name, rescale, etc.).

    Returns
    -------
    str
        TileJSON URL for use with MapLibre / Leaflet.

    Examples
    --------
    >>> collection_tile_url("dem_phase3", bbox=(-84.9, 38.15, -84.8, 38.25))
    'https://.../{tileMatrixSetId}/tilejson.json?bbox=...'
    """
    cid = _resolve_collection_id(collection)
    qs = _pgstac_query_string(bbox=bbox, **kwargs)
    base = f"{titiler_endpoint}/collections/{cid}/{tile_matrix_set}/tilejson.json"
    return f"{base}?{qs}" if qs else base


def collection_map_url(
    collection: str,
    bbox: tuple[float, float, float, float] | None = None,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate an interactive map viewer URL for a STAC collection.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    bbox : tuple, optional
        Bounding box filter as (xmin, ymin, xmax, ymax) in EPSG:4326.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters.

    Returns
    -------
    str
        HTML map viewer URL (opens in a browser).
    """
    cid = _resolve_collection_id(collection)
    qs = _pgstac_query_string(bbox=bbox, **kwargs)
    base = f"{titiler_endpoint}/collections/{cid}/{tile_matrix_set}/map.html"
    return f"{base}?{qs}" if qs else base


def collection_info_url(
    collection: str,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
) -> str:
    """Generate an info URL for a STAC collection.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.

    Returns
    -------
    str
        JSON info URL (available assets, bands, etc.).
    """
    cid = _resolve_collection_id(collection)
    return f"{titiler_endpoint}/collections/{cid}/info"


def collection_bbox_url(
    collection: str,
    bbox: tuple[float, float, float, float],
    width: int = 512,
    height: int = 512,
    fmt: str = "png",
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a rendered image URL for a bbox from a STAC collection.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    bbox : tuple
        Bounding box as (xmin, ymin, xmax, ymax) in EPSG:4326.
    width : int
        Output image width in pixels.
    height : int
        Output image height in pixels.
    fmt : str
        Image format (``"png"``, ``"jpeg"``, ``"tif"``).
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (assets, colormap_name, rescale, etc.).

    Returns
    -------
    str
        Image URL.
    """
    cid = _resolve_collection_id(collection)
    bbox_str = ",".join(str(v) for v in bbox)
    qs = _pgstac_query_string(**kwargs)
    base = f"{titiler_endpoint}/collections/{cid}/bbox/{bbox_str}/{width}x{height}.{fmt}"
    return f"{base}?{qs}" if qs else base


def collection_point_url(
    collection: str,
    lon: float,
    lat: float,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a point query URL for a STAC collection.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    lon : float
        Longitude.
    lat : float
        Latitude.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (assets, etc.).

    Returns
    -------
    str
        JSON URL returning pixel values at the given point.
    """
    cid = _resolve_collection_id(collection)
    qs = _pgstac_query_string(**kwargs)
    base = f"{titiler_endpoint}/collections/{cid}/point/{lon},{lat}"
    return f"{base}?{qs}" if qs else base


# ---------------------------------------------------------------------------
# pgSTAC helpers — item-based (single STAC item)
# ---------------------------------------------------------------------------


def item_tile_url(
    collection: str,
    item_id: str,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a TileJSON URL for a single STAC item.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    item_id : str
        STAC item ID (tile ID).
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (assets, colormap_name, rescale, etc.).

    Returns
    -------
    str
        TileJSON URL for the item.
    """
    cid = _resolve_collection_id(collection)
    qs = _pgstac_query_string(**kwargs)
    base = f"{titiler_endpoint}/collections/{cid}/items/{item_id}/{tile_matrix_set}/tilejson.json"
    return f"{base}?{qs}" if qs else base


def item_preview_url(
    collection: str,
    item_id: str,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    max_size: int = 1024,
    **kwargs: str,
) -> str:
    """Generate a preview image URL for a single STAC item.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    item_id : str
        STAC item ID (tile ID).
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    max_size : int
        Maximum dimension in pixels.
    **kwargs
        Extra query parameters (assets, colormap_name, rescale, etc.).

    Returns
    -------
    str
        Preview PNG URL.
    """
    cid = _resolve_collection_id(collection)
    qs = _pgstac_query_string(**kwargs)
    size_param = f"max_size={max_size}"
    full_qs = f"{size_param}&{qs}" if qs else size_param
    return f"{titiler_endpoint}/collections/{cid}/items/{item_id}/preview?{full_qs}"


def item_info_url(
    collection: str,
    item_id: str,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
) -> str:
    """Generate an info URL for a single STAC item.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    item_id : str
        STAC item ID (tile ID).
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.

    Returns
    -------
    str
        JSON info URL (bounds, CRS, band info, assets).
    """
    cid = _resolve_collection_id(collection)
    return f"{titiler_endpoint}/collections/{cid}/items/{item_id}/info"


def item_statistics_url(
    collection: str,
    item_id: str,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a statistics URL for a single STAC item.

    Parameters
    ----------
    collection : str
        Product key or STAC collection ID.
    item_id : str
        STAC item ID (tile ID).
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (assets, etc.).

    Returns
    -------
    str
        Statistics JSON URL.
    """
    cid = _resolve_collection_id(collection)
    qs = _pgstac_query_string(**kwargs)
    base = f"{titiler_endpoint}/collections/{cid}/items/{item_id}/statistics"
    return f"{base}?{qs}" if qs else base


# ---------------------------------------------------------------------------
# Terrain analysis — server-side algorithms via TiTiler-pgSTAC
# ---------------------------------------------------------------------------


def hillshade_tile_url(
    collection: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    azimuth: float = 315,
    altitude: float = 45,
    buffer: int = 3,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a hillshade TileJSON URL using server-side DEM processing.

    Parameters
    ----------
    collection : str
        DEM product key or collection ID. Default ``"dem_phase3"``.
    bbox : tuple, optional
        Bounding box filter (xmin, ymin, xmax, ymax) in EPSG:4326.
    azimuth : float
        Light source azimuth in degrees (0–360). Default 315 (NW).
    altitude : float
        Light source altitude in degrees (0–90). Default 45.
    buffer : int
        Edge buffer in pixels to reduce tile-edge artifacts. Default 3.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (assets, colormap_name, rescale, etc.).

    Returns
    -------
    str
        TileJSON URL rendering hillshade tiles.
    """
    extra = dict(kwargs)
    extra["algorithm"] = "hillshade"
    extra["algorithm_params"] = f'{{"azimuth":{azimuth},"altitude":{altitude},"buffer":{buffer}}}'
    return collection_tile_url(
        collection,
        bbox=bbox,
        tile_matrix_set=tile_matrix_set,
        titiler_endpoint=titiler_endpoint,
        **extra,
    )


def slope_tile_url(
    collection: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    buffer: int = 3,
    z_exaggeration: float = 1.0,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a slope TileJSON URL using server-side DEM processing.

    Slope values are in degrees (0–90).

    Parameters
    ----------
    collection : str
        DEM product key or collection ID. Default ``"dem_phase3"``.
    bbox : tuple, optional
        Bounding box filter (xmin, ymin, xmax, ymax) in EPSG:4326.
    buffer : int
        Edge buffer in pixels. Default 3.
    z_exaggeration : float
        Vertical exaggeration factor. Default 1.0.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (colormap_name, rescale, etc.).

    Returns
    -------
    str
        TileJSON URL rendering slope tiles.
    """
    extra = dict(kwargs)
    extra["algorithm"] = "slope"
    extra["algorithm_params"] = f'{{"buffer":{buffer},"z_exaggeration":{z_exaggeration}}}'
    return collection_tile_url(
        collection,
        bbox=bbox,
        tile_matrix_set=tile_matrix_set,
        titiler_endpoint=titiler_endpoint,
        **extra,
    )


def contour_tile_url(
    collection: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    increment: int = 35,
    thickness: int = 1,
    minz: int = -12000,
    maxz: int = 8000,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a contour-line TileJSON URL using server-side DEM processing.

    Parameters
    ----------
    collection : str
        DEM product key or collection ID. Default ``"dem_phase3"``.
    bbox : tuple, optional
        Bounding box filter (xmin, ymin, xmax, ymax) in EPSG:4326.
    increment : int
        Contour interval in elevation units. Default 35.
    thickness : int
        Line thickness in pixels (0–10). Default 1.
    minz : int
        Minimum elevation to contour. Default -12000.
    maxz : int
        Maximum elevation to contour. Default 8000.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters.

    Returns
    -------
    str
        TileJSON URL rendering contour tiles.
    """
    extra = dict(kwargs)
    extra["algorithm"] = "contours"
    extra["algorithm_params"] = (
        f'{{"increment":{increment},"thickness":{thickness},"minz":{minz},"maxz":{maxz}}}'
    )
    return collection_tile_url(
        collection,
        bbox=bbox,
        tile_matrix_set=tile_matrix_set,
        titiler_endpoint=titiler_endpoint,
        **extra,
    )


def terrain_rgb_tile_url(
    collection: str = "dem_phase3",
    bbox: tuple[float, float, float, float] | None = None,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a Mapbox Terrain-RGB encoded TileJSON URL.

    Encodes elevation into RGB channels for use with MapLibre GL JS
    terrain and 3D hillshade rendering.

    Parameters
    ----------
    collection : str
        DEM product key or collection ID. Default ``"dem_phase3"``.
    bbox : tuple, optional
        Bounding box filter (xmin, ymin, xmax, ymax) in EPSG:4326.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters.

    Returns
    -------
    str
        TileJSON URL with Terrain-RGB encoded elevation tiles.
    """
    extra = dict(kwargs)
    extra["algorithm"] = "terrainrgb"
    return collection_tile_url(
        collection,
        bbox=bbox,
        tile_matrix_set=tile_matrix_set,
        titiler_endpoint=titiler_endpoint,
        **extra,
    )
