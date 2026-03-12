"""TiTiler URL helpers — generates tile URLs for web map integration.

This module does NOT depend on or import TiTiler. It constructs URLs
that a running TiTiler instance can serve. TiTiler itself is external.
"""

from __future__ import annotations

from urllib.parse import quote_plus

DEFAULT_TITILER_ENDPOINT = "https://titiler.xyz"


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
