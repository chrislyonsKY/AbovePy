"""SearchResult — workflow object wrapping STAC search results.

The centerpiece of abovepy v2.0. Replaces bare GeoDataFrame returns from
``search()`` with a chainable object that supports download, preview,
export, comparison, and size estimation.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import geopandas as gpd

from abovepy.products import Product


class SearchResult:
    """Result of an abovepy search, wrapping tile metadata with workflow methods.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Tile index with columns: tile_id, product, datetime, geometry,
        asset_url, collection_id.
    product : Product
        The product definition used for this search.
    query_params : dict
        Original search parameters (for regenerating URLs and repr).

    Examples
    --------
    >>> result = abovepy.search(county="Franklin", product="dem_phase3")
    >>> result.count
    42
    >>> result.estimate_size()
    {'tile_count': 42, 'avg_tile_mb': 5.0, 'total_mb': 210.0}
    >>> paths = result.download("./data")
    >>> result.preview()
    'https://...'
    """

    __slots__ = ("_gdf", "_product", "_query_params")

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        product: Product,
        query_params: dict[str, Any],
    ) -> None:
        self._gdf = gdf
        self._product = product
        self._query_params = query_params

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def tiles(self) -> gpd.GeoDataFrame:
        """The raw tile index as a GeoDataFrame."""
        return self._gdf

    @property
    def product(self) -> Product:
        """The product definition for this search."""
        return self._product

    @property
    def query_params(self) -> dict[str, Any]:
        """The original search parameters."""
        return dict(self._query_params)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        """Bounding box (xmin, ymin, xmax, ymax) of all result tiles."""
        if self._gdf.empty:
            return (0.0, 0.0, 0.0, 0.0)
        bounds = self._gdf.total_bounds
        return (float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))

    @property
    def count(self) -> int:
        """Number of tiles in the result."""
        return len(self._gdf)

    @property
    def empty(self) -> bool:
        """Whether the result contains no tiles."""
        return self._gdf.empty

    # ------------------------------------------------------------------
    # Size estimation
    # ------------------------------------------------------------------

    def estimate_size(self) -> dict[str, Any]:
        """Estimate the total download size of the result set.

        Returns
        -------
        dict
            Keys: tile_count, avg_tile_mb, total_mb.
        """
        avg = self._product.avg_tile_size_mb
        count = len(self._gdf)
        return {
            "tile_count": count,
            "avg_tile_mb": avg,
            "total_mb": round(avg * count, 1),
        }

    # ------------------------------------------------------------------
    # Workflow methods
    # ------------------------------------------------------------------

    def download(
        self,
        output_dir: str | Path = ".",
        overwrite: bool = False,
        max_workers: int = 4,
    ) -> list[Path]:
        """Download all tiles in this result.

        Parameters
        ----------
        output_dir : str or Path
            Destination directory. Default current directory.
        overwrite : bool
            Overwrite existing files. Default False.
        max_workers : int
            Number of concurrent download threads. Default 4.

        Returns
        -------
        list[Path]
            Paths to downloaded files.
        """
        from abovepy._download import download_tiles

        return download_tiles(
            self._gdf,
            output_dir=output_dir,
            overwrite=overwrite,
            max_workers=max_workers,
        )

    def preview(self, **kwargs: Any) -> str:
        """Generate a preview image URL for this result's area.

        Parameters
        ----------
        **kwargs
            Extra parameters passed to ``viz.preview_url()``.

        Returns
        -------
        str
            Preview image URL.
        """
        from abovepy.viz import preview_url

        return preview_url(
            product=self._product.key,
            bbox=self.bbox,
            **kwargs,
        )

    def map(self, **kwargs: Any) -> Any:
        """Display an interactive map of this result in a notebook.

        Parameters
        ----------
        **kwargs
            Extra parameters passed to ``viz.show()``.

        Returns
        -------
        leafmap.Map
        """
        from abovepy.viz import show

        return show(
            product=self._product.key,
            bbox=self.bbox,
            **kwargs,
        )

    def mosaic(
        self,
        output: str | Path | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        crs: str | None = None,
    ) -> Any:
        """Mosaic downloaded tiles into a single raster.

        Parameters
        ----------
        output : str or Path, optional
            Output path. ``.vrt`` for VRT, ``.tif`` for GeoTIFF.
        bbox : tuple, optional
            Clip to bounding box.
        crs : str, optional
            Reproject to this CRS.

        Returns
        -------
        Path or tuple[numpy.ndarray, dict]
        """
        from abovepy._mosaic import mosaic_tiles

        return mosaic_tiles(self._gdf, bbox=bbox, output=output, crs=crs)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_geodataframe(self) -> gpd.GeoDataFrame:
        """Return the raw GeoDataFrame.

        Returns
        -------
        geopandas.GeoDataFrame
        """
        return self._gdf.copy()

    def to_geoparquet(self, output: str | Path) -> Path:
        """Export tiles to GeoParquet.

        Parameters
        ----------
        output : str or Path
            Output file path.

        Returns
        -------
        Path
        """
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        self._gdf.to_parquet(output)
        return output

    def to_geojson(self) -> str:
        """Serialize tiles to GeoJSON string.

        Returns
        -------
        str
            GeoJSON FeatureCollection.
        """
        return self._gdf.to_json(indent=2)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def compare(self, other: SearchResult) -> gpd.GeoDataFrame:
        """Compare spatial overlap between two search results.

        Useful for phase comparison workflows (e.g., Phase 2 vs Phase 3
        coverage for the same area).

        Parameters
        ----------
        other : SearchResult
            Another search result to compare against.

        Returns
        -------
        geopandas.GeoDataFrame
            Spatial join showing overlapping tiles from both results,
            with columns suffixed ``_left`` and ``_right``.
        """
        import geopandas as gpd

        left = self._gdf[["tile_id", "product", "geometry"]].copy()
        right = other._gdf[["tile_id", "product", "geometry"]].copy()
        return gpd.sjoin(left, right, how="inner", predicate="intersects")

    # ------------------------------------------------------------------
    # Subsetting
    # ------------------------------------------------------------------

    def filter_by_bbox(
        self, bbox: tuple[float, float, float, float]
    ) -> SearchResult:
        """Filter tiles to those intersecting a bounding box.

        Parameters
        ----------
        bbox : tuple
            (xmin, ymin, xmax, ymax) in EPSG:4326.

        Returns
        -------
        SearchResult
            Filtered result.
        """
        from shapely.geometry import box

        clip = box(*bbox)
        mask = self._gdf.intersects(clip)
        return SearchResult(self._gdf[mask].copy(), self._product, self._query_params)

    def head(self, n: int = 5) -> SearchResult:
        """Return the first *n* tiles.

        Parameters
        ----------
        n : int
            Number of tiles. Default 5.

        Returns
        -------
        SearchResult
        """
        return SearchResult(self._gdf.head(n).copy(), self._product, self._query_params)

    # ------------------------------------------------------------------
    # Container protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._gdf)

    def __bool__(self) -> bool:
        return not self._gdf.empty

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate over tiles as dicts (excludes geometry)."""
        for _, row in self._gdf.iterrows():
            yield row.to_dict()

    def __repr__(self) -> str:
        est = self.estimate_size()
        return (
            f"SearchResult({self._product.key!r}, "
            f"{self.count} tile(s), ~{est['total_mb']} MB)"
        )

    def _repr_html_(self) -> str:
        """Rich display for Jupyter notebooks."""
        est = self.estimate_size()
        header = (
            f"<strong>SearchResult</strong>: {self._product.display_name} "
            f"&mdash; {self.count} tile(s), ~{est['total_mb']} MB estimated"
        )
        if self._gdf.empty:
            return f"<div>{header}<br><em>No tiles found.</em></div>"
        table = self._gdf.drop(columns="geometry", errors="ignore").head(10).to_html(index=False)
        more = ""
        if self.count > 10:
            more = f"<em>... and {self.count - 10} more tile(s)</em>"
        return f"<div>{header}{table}{more}</div>"
