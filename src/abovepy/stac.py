"""STAC API wrapper — pystac-client with retry logic and response caching.

Wraps pystac-client for querying the KyFromAbove STAC endpoint.
Handles pagination, error retry, and conversion to GeoDataFrame.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import geopandas as gpd
    from pystac_client import Client

from abovepy._constants import (
    CQL2_CONFORMANCE_FALLBACK,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    STAC_URL,
)
from abovepy.utils.cache import TTLCache, make_cache_key

logger = logging.getLogger(__name__)

# Module-level cache shared across all client instances
_stac_cache = TTLCache()

# Cached conformance documents, keyed by API root URL (1-hour TTL)
_conformance_cache = TTLCache(maxsize=8, ttl=3600)

# Conformance URI markers that advertise CQL2 filter support
_CQL2_CONFORMANCE_MARKERS = ("#filter", "/conf/filter", "cql2")


def create_client(stac_url: str = STAC_URL) -> Client:
    """Create a pystac-client Client with retry configuration.

    Parameters
    ----------
    stac_url : str
        STAC API endpoint URL.

    Returns
    -------
    pystac_client.Client
    """
    from pystac_client import Client

    return Client.open(stac_url)


def get_conformance(client: Client) -> tuple[str, ...]:
    """Fetch (and cache) the conformance classes advertised by a STAC API.

    Parameters
    ----------
    client : pystac_client.Client
        STAC client instance.

    Returns
    -------
    tuple[str, ...]
        Conformance class URIs. Empty when the document can't be read.
    """
    key = str(getattr(client, "self_href", None) or id(client))
    cached = _conformance_cache.get(key)
    if cached is not None:
        return tuple(cached)

    try:
        conforms = tuple(str(uri) for uri in client.get_conforms_to())
    except Exception as exc:  # pystac-client raises library-specific errors
        logger.warning("Could not fetch STAC conformance document: %s", exc)
        return ()

    _conformance_cache.set(key, conforms)
    return conforms


def supports_cql2(client: Client) -> bool:
    """Check whether a STAC API advertises CQL2 filter support.

    Reads the endpoint's conformance document (cached per endpoint,
    1-hour TTL). When the document cannot be fetched — offline test
    runs, transient API failures — falls back to
    ``CQL2_CONFORMANCE_FALLBACK`` so a working endpoint is never
    blocked by a conformance hiccup.

    Parameters
    ----------
    client : pystac_client.Client
        STAC client instance.

    Returns
    -------
    bool
    """
    conforms = get_conformance(client)
    if not conforms:
        logger.debug(
            "No conformance document available; assuming CQL2 support = %s",
            CQL2_CONFORMANCE_FALLBACK,
        )
        return CQL2_CONFORMANCE_FALLBACK
    return any(marker in uri.lower() for uri in conforms for marker in _CQL2_CONFORMANCE_MARKERS)


def search_stac(
    client: Client,
    collection_id: str,
    bbox: tuple[float, float, float, float] | None = None,
    datetime: str | None = None,
    max_items: int = 500,
    intersects: dict[str, Any] | None = None,
    filter: dict[str, Any] | str | None = None,
    sortby: list[str] | str | None = None,
    ids: list[str] | None = None,
    fields: list[str] | None = None,
) -> list[Any]:
    """Query the KyFromAbove STAC API for matching items.

    Includes automatic retry with exponential backoff for transient
    failures (common with serverless APIs) and in-memory response
    caching to avoid duplicate queries.

    Parameters
    ----------
    client : pystac_client.Client
        STAC client instance.
    collection_id : str
        STAC collection ID (e.g., "dem-phase3").
    bbox : tuple, optional
        Bounding box in EPSG:4326 (xmin, ymin, xmax, ymax).
    datetime : str, optional
        ISO 8601 datetime range.
    max_items : int
        Maximum items to return.
    intersects : dict, optional
        GeoJSON geometry for spatial intersection (alternative to bbox).
    filter : dict or str, optional
        CQL2 filter expression.
    sortby : list[str] or str, optional
        Sort fields (e.g., ``["+datetime"]``).
    ids : list[str], optional
        Specific STAC item IDs to fetch.
    fields : list[str], optional
        Fields to include/exclude from response.

    Returns
    -------
    list[pystac.Item]
        Matching STAC items.

    Raises
    ------
    SearchError
        If a CQL2 ``filter`` is requested but the endpoint does not
        advertise CQL2 support, or all retry attempts fail.
    """
    if filter is not None and not supports_cql2(client):
        from abovepy._exceptions import SearchError

        raise SearchError(
            "The STAC endpoint does not advertise CQL2 filter support in its "
            "conformance document. Remove filter= or filter the returned "
            "GeoDataFrame client-side, e.g. result.tiles[result.tiles.datetime > ...]."
        )

    cache_key = make_cache_key(
        collection_id,
        bbox,
        datetime,
        max_items,
        intersects=intersects,
        filter=filter,
        sortby=sortby,
        ids=ids,
        fields=fields,
    )
    cached = _stac_cache.get(cache_key)
    if cached is not None:
        logger.debug("STAC cache hit for %s (%d items)", collection_id, len(cached))
        return list(cached)

    items = _search_with_retry(
        client,
        collection_id,
        bbox,
        datetime,
        max_items,
        intersects=intersects,
        filter=filter,
        sortby=sortby,
        ids=ids,
        fields=fields,
    )

    _stac_cache.set(cache_key, items)
    logger.info("STAC search returned %d items from %s", len(items), collection_id)
    return items


def _search_with_retry(
    client: Client,
    collection_id: str,
    bbox: tuple[float, float, float, float] | None,
    datetime: str | None,
    max_items: int,
    intersects: dict[str, Any] | None = None,
    filter: dict[str, Any] | str | None = None,
    sortby: list[str] | str | None = None,
    ids: list[str] | None = None,
    fields: list[str] | None = None,
) -> list[Any]:
    """Execute a STAC search with retry on transient failures.

    Parameters
    ----------
    client : pystac_client.Client
        STAC client instance.
    collection_id : str
        STAC collection ID.
    bbox : tuple, optional
        Bounding box in EPSG:4326.
    datetime : str, optional
        ISO 8601 datetime range.
    max_items : int
        Maximum items to return.
    intersects : dict, optional
        GeoJSON geometry for spatial intersection.
    filter : dict or str, optional
        CQL2 filter expression.
    sortby : list[str] or str, optional
        Sort fields.
    ids : list[str], optional
        Specific STAC item IDs.
    fields : list[str], optional
        Fields to include/exclude.

    Returns
    -------
    list[pystac.Item]

    Raises
    ------
    SearchError
        If all retry attempts fail.
    """
    last_error: Exception | None = None

    # Build kwargs dynamically — only pass non-None params
    search_kwargs: dict[str, Any] = {
        "collections": [collection_id],
        "max_items": max_items,
    }
    if bbox is not None:
        search_kwargs["bbox"] = bbox
    if datetime is not None:
        search_kwargs["datetime"] = datetime
    if intersects is not None:
        search_kwargs["intersects"] = intersects
    if filter is not None:
        search_kwargs["filter"] = filter
    if sortby is not None:
        search_kwargs["sortby"] = sortby if isinstance(sortby, list) else [sortby]
    if ids is not None:
        search_kwargs["ids"] = ids
    if fields is not None:
        search_kwargs["fields"] = fields

    for attempt in range(MAX_RETRIES):
        try:
            search = client.search(**search_kwargs)
            return list(search.items())
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_FACTOR * (2**attempt)
                logger.warning(
                    "STAC search attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "STAC search failed after %d attempts: %s",
                    MAX_RETRIES,
                    exc,
                )

    from abovepy._exceptions import SearchError

    raise SearchError(
        f"STAC search failed after {MAX_RETRIES} attempts: {last_error}"
    ) from last_error


def items_to_geodataframe(
    items: list[Any],
    product_key: str,
) -> gpd.GeoDataFrame:
    """Convert STAC items to a GeoDataFrame with asset URLs.

    Parameters
    ----------
    items : list[pystac.Item]
        STAC items from search_stac().
    product_key : str
        The abovepy product key for labeling.

    Returns
    -------
    geopandas.GeoDataFrame
        Columns: tile_id, product, datetime, geometry, asset_url,
        collection_id, assets. ``asset_url`` is the primary data asset;
        ``assets`` maps every asset key on the item to its href
        (thumbnails, metadata, alternate formats).
    """
    import geopandas as gpd
    from shapely.geometry import shape

    if not items:
        return gpd.GeoDataFrame(
            columns=[
                "tile_id",
                "product",
                "datetime",
                "geometry",
                "asset_url",
                "collection_id",
                "assets",
            ],
            geometry="geometry",
            crs="EPSG:4326",
        )

    rows = []
    for item in items:
        asset_url = _extract_primary_asset_url(item)

        rows.append(
            {
                "tile_id": item.id,
                "product": product_key,
                "datetime": item.datetime,
                "geometry": shape(item.geometry),
                "asset_url": asset_url,
                "collection_id": item.collection_id,
                "assets": _extract_assets(item),
            }
        )

    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def _extract_assets(item: Any) -> dict[str, str]:
    """Map every asset key on a STAC item to its href.

    Parameters
    ----------
    item : pystac.Item

    Returns
    -------
    dict[str, str]
        ``{asset_key: href}`` for all assets, including thumbnails and
        alternate formats.
    """
    if not item.assets:
        return {}
    return {key: str(asset.href) for key, asset in item.assets.items()}


def _extract_primary_asset_url(item: Any) -> str | None:
    """Extract the primary data asset URL from a STAC item.

    Looks for common asset keys in priority order:
    data > default > visual > the first non-thumbnail asset.

    Parameters
    ----------
    item : pystac.Item

    Returns
    -------
    str or None
        Asset URL, or None if no data asset found.
    """
    if not item.assets:
        return None

    priority_keys = ["data", "default", "visual", "image"]
    for key in priority_keys:
        if key in item.assets:
            return str(item.assets[key].href)

    for key, asset in item.assets.items():
        if "thumbnail" not in key.lower():
            return str(asset.href)

    return str(next(iter(item.assets.values())).href)


def clear_cache() -> None:
    """Clear the STAC response cache."""
    _stac_cache.clear()
    logger.debug("STAC cache cleared")
