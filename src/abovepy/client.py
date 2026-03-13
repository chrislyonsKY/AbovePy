"""KyFromAboveClient — main entry point for KyFromAbove data access.

Wraps STAC queries, tile downloads, cloud-native reads, and mosaicking
behind a simple, Pythonic interface. All data access goes through this class;
module-level convenience functions in __init__.py delegate here.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import geopandas as gpd
    import pandas as pd

from abovepy._constants import DEFAULT_INPUT_CRS, STAC_URL
from abovepy.products import PRODUCTS, VALID_PRODUCTS, get_product

logger = logging.getLogger(__name__)


class KyFromAboveClient:
    """Client for accessing KyFromAbove LiDAR, DEM, and orthoimagery.

    Parameters
    ----------
    cache_dir : str or Path, optional
        Local directory for caching downloaded tiles.
    stac_url : str, optional
        Override the STAC API endpoint URL.

    Examples
    --------
    >>> client = KyFromAboveClient()
    >>> tiles = client.search(county="Franklin", product="dem_phase3")
    >>> paths = client.download(tiles, output_dir="./data")
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        stac_url: str | None = None,
    ) -> None:
        self.stac_url = stac_url or STAC_URL
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._stac_client: Any = None

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        cache = f", cache_dir={self.cache_dir!r}" if self.cache_dir else ""
        connected = "connected" if self._stac_client is not None else "not connected"
        return f"KyFromAboveClient(stac_url={self.stac_url!r}{cache}, {connected})"

    def _get_stac_client(self) -> Any:
        """Lazy-initialize the pystac-client connection."""
        if self._stac_client is None:
            from abovepy.stac import create_client

            self._stac_client = create_client(self.stac_url)
        return self._stac_client

    def search(
        self,
        bbox: tuple[float, float, float, float] | None = None,
        product: str = "dem_phase3",
        county: str | None = None,
        crs: str = DEFAULT_INPUT_CRS,
        datetime: str | None = None,
        max_items: int = 500,
    ) -> gpd.GeoDataFrame:
        """Find tiles intersecting an area of interest.

        Parameters
        ----------
        bbox : tuple, optional
            Bounding box as (xmin, ymin, xmax, ymax).
        product : str
            Product key (e.g., "dem_phase3").
        county : str, optional
            Kentucky county name. Overrides bbox if provided.
        crs : str
            CRS of input bbox. Default "EPSG:4326".
        datetime : str, optional
            ISO 8601 datetime range.
        max_items : int
            Maximum tiles to return.

        Returns
        -------
        geopandas.GeoDataFrame
            Tile index with metadata and asset URLs.
        """
        from abovepy.stac import items_to_geodataframe, search_stac
        from abovepy.utils.bbox import get_county_bbox, validate_bbox
        from abovepy.utils.crs import bbox_intersects_kentucky

        # Resolve bbox from county or validate provided bbox
        if county is not None:
            bbox = get_county_bbox(county)
            logger.info("Using bbox for %s County: %s", county, bbox)
        elif bbox is not None:
            validate_bbox(bbox)
            if not bbox_intersects_kentucky(bbox, crs=crs):
                logger.warning(
                    "Bbox %s does not intersect Kentucky — search will likely return no results.",
                    bbox,
                )
        else:
            from abovepy._exceptions import BboxError

            raise BboxError("Provide either bbox= or county=")

        # Look up the product
        prod = get_product(product)

        # Query STAC API
        items = search_stac(
            client=self._get_stac_client(),
            collection_id=prod.collection_id,
            bbox=bbox,
            datetime=datetime,
            max_items=max_items,
        )

        # Convert to GeoDataFrame
        gdf = items_to_geodataframe(items, product_key=prod.key)

        if gdf.empty:
            logger.warning("No %s tiles found in the specified area.", prod.display_name)

        return gdf

    def download(
        self,
        tiles: gpd.GeoDataFrame,
        output_dir: str | Path,
        overwrite: bool = False,
    ) -> list[Path]:
        """Download tiles to a local directory.

        Parameters
        ----------
        tiles : geopandas.GeoDataFrame
            Tile index from search().
        output_dir : str or Path
            Destination directory.
        overwrite : bool
            Overwrite existing files. Default False.

        Returns
        -------
        list[Path]
            Paths to downloaded files.
        """
        from abovepy._download import download_tiles

        return download_tiles(tiles, output_dir=output_dir, overwrite=overwrite)

    def read(
        self,
        source: str | Path,
        bbox: tuple[float, float, float, float] | None = None,
        crs: str | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        """Read a raster tile, optionally windowed.

        Parameters
        ----------
        source : str or Path
            Local path, S3 URI, or HTTPS URL.
        bbox : tuple, optional
            Bounding box for windowed read.
        crs : str, optional
            CRS of the bbox.

        Returns
        -------
        tuple[numpy.ndarray, dict]
            (data, profile).
        """
        from abovepy.io.cog import read_cog

        return read_cog(source, bbox=bbox, crs=crs)

    def mosaic(
        self,
        tiles_or_paths: list[Path] | gpd.GeoDataFrame,
        bbox: tuple[float, float, float, float] | None = None,
        output: str | Path | None = None,
        crs: str | None = None,
    ) -> Any:
        """Mosaic tiles into a single raster or VRT.

        Parameters
        ----------
        tiles_or_paths : list[Path] or GeoDataFrame
            Tile paths or tile index.
        bbox : tuple, optional
            Clip to bounding box.
        output : str or Path, optional
            Output path. .vrt → VRT (default), .tif → GeoTIFF.
        crs : str, optional
            Reproject to this CRS.

        Returns
        -------
        Path or tuple[numpy.ndarray, dict]
        """
        from abovepy._mosaic import mosaic_tiles

        return mosaic_tiles(tiles_or_paths, bbox=bbox, output=output, crs=crs)

    def info(self, source: str | None = None) -> pd.DataFrame | dict[str, Any]:
        """Inspect products or a remote tile.

        Parameters
        ----------
        source : str, optional
            Product key, URL, or S3 URI. None → all products.

        Returns
        -------
        pandas.DataFrame or dict
        """
        import pandas as pd

        if source is None:
            rows = []
            for prod in PRODUCTS.values():
                rows.append(
                    {
                        "product": prod.key,
                        "display_name": prod.display_name,
                        "collection_id": prod.collection_id,
                        "format": prod.format,
                        "resolution": prod.resolution,
                        "phase": prod.phase,
                        "crs": prod.native_crs,
                    }
                )
            return pd.DataFrame(rows)

        if source in VALID_PRODUCTS:
            prod = get_product(source)
            return {
                "product": prod.key,
                "display_name": prod.display_name,
                "collection_id": prod.collection_id,
                "format": prod.format,
                "resolution": prod.resolution,
                "phase": prod.phase,
                "native_crs": prod.native_crs,
            }

        # Remote tile inspection
        from abovepy.io.cog import inspect_cog

        return inspect_cog(source)

    def get_stac_client(self) -> Any:
        """Get the underlying pystac-client Client for advanced queries.

        Returns
        -------
        pystac_client.Client
        """
        return self._get_stac_client()
