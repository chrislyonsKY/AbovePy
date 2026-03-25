"""TiTiler COG and mosaic URL helpers.

These work with standalone TiTiler instances (``/cog/...``, ``/mosaic/...``)
and require individual COG URLs as parameters.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from abovepy._constants import TITILER_ENDPOINT

DEFAULT_TITILER_ENDPOINT = TITILER_ENDPOINT


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
