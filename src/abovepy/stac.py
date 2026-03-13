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
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    STAC_URL,
)
from abovepy.utils.cache import TTLCache, make_cache_key

logger = logging.getLogger(__name__)

# Module-level cache shared across all client instances
_stac_cache = TTLCache()


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


def search_stac(
    client: Client,
    collection_id: str,
    bbox: tuple[float, float, float, float],
    datetime: str | None = None,
    max_items: int = 500,
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
    bbox : tuple
        Bounding box in EPSG:4326 (xmin, ymin, xmax, ymax).
    datetime : str, optional
        ISO 8601 datetime range.
    max_items : int
        Maximum items to return.

    Returns
    -------
    list[pystac.Item]
        Matching STAC items.
    """
    cache_key = make_cache_key(collection_id, bbox, datetime, max_items)
    cached = _stac_cache.get(cache_key)
    if cached is not None:
        logger.debug("STAC cache hit for %s (%d items)", collection_id, len(cached))
        return list(cached)

    items = _search_with_retry(
        client, collection_id, bbox, datetime, max_items
    )

    _stac_cache.set(cache_key, items)
    logger.info("STAC search returned %d items from %s", len(items), collection_id)
    return items


def _search_with_retry(
    client: Client,
    collection_id: str,
    bbox: tuple[float, float, float, float],
    datetime: str | None,
    max_items: int,
) -> list[Any]:
    """Execute a STAC search with retry on transient failures.

    Parameters
    ----------
    client : pystac_client.Client
        STAC client instance.
    collection_id : str
        STAC collection ID.
    bbox : tuple
        Bounding box in EPSG:4326.
    datetime : str, optional
        ISO 8601 datetime range.
    max_items : int
        Maximum items to return.

    Returns
    -------
    list[pystac.Item]

    Raises
    ------
    SearchError
        If all retry attempts fail.
    """
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            search = client.search(
                collections=[collection_id],
                bbox=bbox,
                datetime=datetime,
                max_items=max_items,
            )
            return list(search.items())
        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_FACTOR * (2 ** attempt)
                logger.warning(
                    "STAC search attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1, MAX_RETRIES, exc, wait,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "STAC search failed after %d attempts: %s",
                    MAX_RETRIES, exc,
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
        collection_id.
    """
    import geopandas as gpd
    from shapely.geometry import shape

    if not items:
        return gpd.GeoDataFrame(
            columns=["tile_id", "product", "datetime", "geometry",
                      "asset_url", "collection_id"],
            geometry="geometry",
            crs="EPSG:4326",
        )

    rows = []
    for item in items:
        asset_url = _extract_primary_asset_url(item)

        rows.append({
            "tile_id": item.id,
            "product": product_key,
            "datetime": item.datetime,
            "geometry": shape(item.geometry),
            "asset_url": asset_url,
            "collection_id": item.collection_id,
        })

    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


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
