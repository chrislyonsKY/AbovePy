"""abovepy — KyFromAbove LiDAR, DEM, and orthoimagery data access for Python.

All data is publicly available. No credentials required.

Quick start:
    import abovepy

    # Find DEM tiles covering Frankfort
    tiles = abovepy.search(bbox=(-84.9, 38.15, -84.8, 38.25), product="dem_phase3")

    # Or search by county name
    tiles = abovepy.search(county="Franklin", product="dem_phase3")

    # Download
    paths = abovepy.download(tiles, output_dir="./data")

    # Mosaic into a single VRT
    vrt = abovepy.mosaic(paths, output="frankfort.vrt")

    # Stream a window without downloading
    data, profile = abovepy.read(tiles.iloc[0].asset_url, bbox=(-84.85, 38.18, -84.82, 38.21))
"""

from abovepy._version import __version__
from abovepy.client import KyFromAboveClient
from abovepy.products import Product, ProductType, list_products
from abovepy.stac import clear_cache

_default_client: KyFromAboveClient | None = None


def _get_client() -> KyFromAboveClient:
    """Get or create the default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = KyFromAboveClient()
    return _default_client


def search(
    bbox: tuple[float, float, float, float] | None = None,
    product: str = "dem_phase3",
    county: str | None = None,
    crs: str = "EPSG:4326",
    datetime: str | None = None,
    max_items: int = 500,
):
    """Find KyFromAbove tiles intersecting an area of interest.

    Provide either ``bbox`` or ``county``, not both.

    Parameters
    ----------
    bbox : tuple, optional
        Bounding box as (xmin, ymin, xmax, ymax).
    product : str
        Product key: "dem_phase1", "dem_phase2", "dem_phase3",
        "ortho_phase1", "ortho_phase2", "ortho_phase3",
        "laz_phase1", "laz_phase2", "laz_phase3".
    county : str, optional
        Kentucky county name (e.g., "Pike", "Franklin"). Case-insensitive.
    crs : str
        CRS of the input bbox. Default "EPSG:4326". Ignored if county is used.
    datetime : str, optional
        ISO 8601 datetime range (e.g., "2022-01/2024-01").
    max_items : int
        Maximum tiles to return. Default 500.

    Returns
    -------
    geopandas.GeoDataFrame
        Tile index with columns: tile_id, product, geometry,
        asset_url, file_size, datetime, collection_id.
    """
    return _get_client().search(
        bbox=bbox, product=product, county=county,
        crs=crs, datetime=datetime, max_items=max_items,
    )


def download(tiles, output_dir, overwrite=False):
    """Download tiles to a local directory.

    Parameters
    ----------
    tiles : geopandas.GeoDataFrame
        Tile index from search().
    output_dir : str or Path
        Directory to save downloaded files.
    overwrite : bool
        Overwrite existing files. Default False.

    Returns
    -------
    list[Path]
        Paths to downloaded files.
    """
    return _get_client().download(tiles=tiles, output_dir=output_dir, overwrite=overwrite)


def read(source, bbox=None, crs=None):
    """Read a tile or remote source, optionally windowed to a bbox.

    Parameters
    ----------
    source : str or Path
        Local path, S3 URI, or HTTPS URL to a raster tile.
    bbox : tuple, optional
        Bounding box for windowed read (xmin, ymin, xmax, ymax).
    crs : str, optional
        CRS of the bbox. Default matches source CRS.

    Returns
    -------
    tuple[numpy.ndarray, dict]
        (data, profile) — raster array and rasterio profile.
    """
    return _get_client().read(source=source, bbox=bbox, crs=crs)


def mosaic(tiles_or_paths, bbox=None, output=None, crs=None):
    """Mosaic tiles into a single raster or VRT.

    Defaults to VRT (zero-copy) unless output has a .tif extension.

    Parameters
    ----------
    tiles_or_paths : list[Path] or GeoDataFrame
        Tile file paths or tile index GeoDataFrame.
    bbox : tuple, optional
        Clip output to this bounding box.
    output : str or Path, optional
        Output path. .vrt → VRT, .tif → GeoTIFF. None → in-memory.
    crs : str, optional
        Reproject output to this CRS.

    Returns
    -------
    Path or tuple[numpy.ndarray, dict]
    """
    return _get_client().mosaic(
        tiles_or_paths=tiles_or_paths, bbox=bbox, output=output, crs=crs,
    )


def info(source=None):
    """Inspect products or a specific remote tile.

    Parameters
    ----------
    source : str, optional
        Product key, URL, or S3 URI. None returns all products.

    Returns
    -------
    pandas.DataFrame or dict
    """
    return _get_client().info(source=source)


__all__ = [
    "__version__",
    "KyFromAboveClient",
    "Product",
    "ProductType",
    "clear_cache",
    "download",
    "info",
    "list_products",
    "mosaic",
    "read",
    "search",
]
