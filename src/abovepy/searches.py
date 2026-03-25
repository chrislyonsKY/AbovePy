"""pgSTAC search registration — persistent virtual mosaics via TiTiler-pgSTAC.

Register a STAC search (collection + bbox + datetime) to get a stable hash ID.
That hash can then be used to generate tile URLs without re-specifying the query.

The ``register_search()`` function is the only function here that makes an HTTP
call (POST via httpx).  All other helpers are pure URL builders.
"""

from __future__ import annotations

from urllib.parse import urlencode

from abovepy._constants import TITILER_PGSTAC_ENDPOINT
from abovepy.titiler import DEFAULT_TILE_MATRIX_SET, _resolve_collection_id

DEFAULT_PGSTAC_ENDPOINT = TITILER_PGSTAC_ENDPOINT


def register_search(
    collection: str,
    bbox: tuple[float, float, float, float] | None = None,
    datetime: str | None = None,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
) -> str:
    """Register a STAC search and return the search hash ID.

    This POSTs a CQL2-JSON filter to the ``/searches/register`` endpoint
    and returns the hash that identifies the virtual mosaic.

    Parameters
    ----------
    collection : str
        Product key (e.g., ``"dem_phase3"``) or STAC collection ID.
    bbox : tuple, optional
        Bounding box (xmin, ymin, xmax, ymax) in EPSG:4326.
    datetime : str, optional
        ISO 8601 datetime or range (e.g., ``"2022-01/2024-01"``).
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.

    Returns
    -------
    str
        The registered search hash ID.

    Raises
    ------
    httpx.HTTPStatusError
        If the registration request fails.
    """
    import httpx

    cid = _resolve_collection_id(collection)

    body: dict[str, object] = {
        "collections": [cid],
    }
    if bbox is not None:
        body["bbox"] = list(bbox)
    if datetime is not None:
        body["datetime"] = datetime

    url = f"{titiler_endpoint}/searches/register"
    resp = httpx.post(url, json=body, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    # The response contains an "id" field with the search hash
    return str(data["id"])


# ---------------------------------------------------------------------------
# URL builders for registered searches (pure — no HTTP calls)
# ---------------------------------------------------------------------------


def _search_query_string(
    assets: str | list[str] | None = None,
    colormap_name: str | None = None,
    rescale: str | None = None,
    algorithm: str | None = None,
    **extra: str,
) -> str:
    """Build a query string for search-based tile endpoints."""
    params: dict[str, str] = {}
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


def search_tile_url(
    search_id: str,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a TileJSON URL from a registered search hash.

    Parameters
    ----------
    search_id : str
        Search hash from ``register_search()``.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters (assets, colormap_name, rescale, etc.).

    Returns
    -------
    str
        TileJSON URL for the registered search mosaic.
    """
    qs = _search_query_string(**kwargs)
    base = f"{titiler_endpoint}/searches/{search_id}/{tile_matrix_set}/tilejson.json"
    return f"{base}?{qs}" if qs else base


def search_map_url(
    search_id: str,
    tile_matrix_set: str = DEFAULT_TILE_MATRIX_SET,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate an interactive map viewer URL from a registered search.

    Parameters
    ----------
    search_id : str
        Search hash from ``register_search()``.
    tile_matrix_set : str
        Tile matrix set. Default ``"WebMercatorQuad"``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.
    **kwargs
        Extra query parameters.

    Returns
    -------
    str
        HTML map viewer URL.
    """
    qs = _search_query_string(**kwargs)
    base = f"{titiler_endpoint}/searches/{search_id}/{tile_matrix_set}/map.html"
    return f"{base}?{qs}" if qs else base


def search_info_url(
    search_id: str,
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
) -> str:
    """Generate an info URL for a registered search.

    Parameters
    ----------
    search_id : str
        Search hash from ``register_search()``.
    titiler_endpoint : str
        TiTiler-pgSTAC service URL.

    Returns
    -------
    str
        JSON info URL.
    """
    return f"{titiler_endpoint}/searches/{search_id}/info"


def search_bbox_url(
    search_id: str,
    bbox: tuple[float, float, float, float],
    width: int = 512,
    height: int = 512,
    fmt: str = "png",
    titiler_endpoint: str = DEFAULT_PGSTAC_ENDPOINT,
    **kwargs: str,
) -> str:
    """Generate a rendered image URL from a registered search + bbox.

    Parameters
    ----------
    search_id : str
        Search hash from ``register_search()``.
    bbox : tuple
        Bounding box (xmin, ymin, xmax, ymax) in EPSG:4326.
    width : int
        Output width in pixels.
    height : int
        Output height in pixels.
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
    bbox_str = ",".join(str(v) for v in bbox)
    qs = _search_query_string(**kwargs)
    base = f"{titiler_endpoint}/searches/{search_id}/bbox/{bbox_str}/{width}x{height}.{fmt}"
    return f"{base}?{qs}" if qs else base
