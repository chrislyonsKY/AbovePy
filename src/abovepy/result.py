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
        asset_url, collection_id, assets.
    product : Product
        The product definition used for this search.
    query_params : dict
        Original search parameters (for regenerating URLs and repr).
    items : list[pystac.Item], optional
        The raw STAC items behind the tile index. Enables
        :meth:`to_xarray`. Results built from a bare GeoDataFrame
        (``items=None``) work everywhere else.

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

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        product: Product,
        query_params: dict[str, Any],
        items: list[Any] | None = None,
    ) -> None:
        self._gdf = gdf
        self._product = product
        self._query_params = query_params
        self._items = items

    @property
    def items(self) -> list[Any] | None:
        """The raw STAC items behind this result (None if not carried)."""
        return self._items

    def _subset_items(self, gdf: gpd.GeoDataFrame) -> list[Any] | None:
        """Filter carried STAC items down to the tiles remaining in gdf."""
        if self._items is None or "tile_id" not in gdf.columns:
            return None
        keep = set(gdf["tile_id"])
        return [item for item in self._items if getattr(item, "id", None) in keep]

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
        return bool(self._gdf.empty)

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
        from abovepy.export import _stringify_object_columns

        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        _stringify_object_columns(self._gdf).to_parquet(output)
        return output

    def to_geojson(self) -> str:
        """Serialize tiles to GeoJSON string.

        Returns
        -------
        str
            GeoJSON FeatureCollection.
        """
        return str(self._gdf.to_json(indent=2))

    def to_xarray(self, **kwargs: Any) -> Any:
        """Load this result lazily as an xarray Dataset via odc-stac.

        Requires the ``xarray`` extra (``pip install abovepy[xarray]``)
        and a result that carries STAC items (any result returned by
        ``abovepy.search()`` does).

        Parameters
        ----------
        **kwargs
            Passed through to ``odc.stac.load()`` — e.g.
            ``chunks={"x": 2048, "y": 2048}``, ``resolution=2.0``,
            ``bands=...``. ``crs`` defaults to the product's native
            CRS (EPSG:3089).

        Returns
        -------
        xarray.Dataset

        Raises
        ------
        ImportError
            If odc-stac is not installed.
        AnalysisError
            If this result carries no STAC items.
        """
        try:
            from odc import stac as odc_stac
        except ImportError:
            raise ImportError(
                "xarray support requires odc-stac. Install with: pip install abovepy[xarray]"
            ) from None

        if not self._items:
            from abovepy._exceptions import AnalysisError

            raise AnalysisError(
                "This SearchResult carries no STAC items (it was built from a "
                "bare GeoDataFrame). Re-run abovepy.search() to enable to_xarray()."
            )

        kwargs.setdefault("crs", self._product.native_crs)
        return odc_stac.load(self._items, **kwargs)

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
    # Provenance & validation
    # ------------------------------------------------------------------

    def provenance(self) -> dict[str, Any]:
        """Generate provenance metadata for this search result.

        Useful for survey/engineering deliverables that require source
        documentation, acquisition dates, and data lineage.

        Returns
        -------
        dict
            Keys: product, collection_id, source_program, acquisition_period,
            native_crs, tile_count, estimated_size_mb, bbox, query_params,
            asset_urls, phases.
        """
        urls = self._gdf["asset_url"].dropna().tolist() if "asset_url" in self._gdf.columns else []
        phases = set()
        if "product" in self._gdf.columns:
            phases = set(self._gdf["product"].unique())

        return {
            "product": self._product.key,
            "display_name": self._product.display_name,
            "collection_id": self._product.collection_id,
            "source_program": self._product.source_program,
            "acquisition_period": (
                f"{self._product.acquisition_start}–{self._product.acquisition_end}"
                if self._product.acquisition_start
                else "unknown"
            ),
            "native_crs": self._product.native_crs,
            "resolution": self._product.resolution,
            "format": self._product.format,
            "tile_count": len(self._gdf),
            "estimated_size_mb": round(self._product.avg_tile_size_mb * len(self._gdf), 1),
            "bbox": self.bbox,
            "query_params": self._query_params,
            "asset_urls": urls,
            "phases": sorted(phases),
        }

    def validate(self) -> list[str]:
        """Check for data quality issues in this search result.

        Returns a list of human-readable warning strings. An empty list
        means no issues were detected.

        Returns
        -------
        list[str]
            Warning messages. Empty if no issues found.
        """
        warnings: list[str] = []

        if self._gdf.empty:
            warnings.append("No tiles found — the search returned empty results.")
            return warnings

        # Mixed products
        if "product" in self._gdf.columns:
            products = self._gdf["product"].unique()
            if len(products) > 1:
                warnings.append(
                    f"Mixed products in result: {', '.join(sorted(products))}. "
                    "Consider filtering to a single product."
                )

        # Mixed collection IDs (could indicate mixed phases)
        if "collection_id" in self._gdf.columns:
            collections = self._gdf["collection_id"].unique()
            if len(collections) > 1:
                warnings.append(
                    f"Mixed collections: {', '.join(sorted(collections))}. "
                    "Tiles may come from different acquisition phases."
                )

        # Missing asset URLs
        if "asset_url" in self._gdf.columns:
            missing = self._gdf["asset_url"].isna().sum()
            if missing > 0:
                warnings.append(f"{missing} tile(s) have no asset URL and cannot be downloaded.")

        # Coverage gap detection (simple: check if total bounds has large
        # areas without tiles, based on tile count vs expected density)
        if len(self._gdf) > 0:
            bounds = self._gdf.total_bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            area_deg = width * height
            # Very rough: if area is large but tile count is low, warn
            if area_deg > 0.1 and len(self._gdf) < 5:
                warnings.append(
                    "Low tile density for the covered area — there may be coverage gaps."
                )

        # Missing datetime metadata
        if "datetime" in self._gdf.columns:
            null_dates = self._gdf["datetime"].isna().sum()
            if null_dates > 0:
                pct = null_dates / len(self._gdf) * 100
                warnings.append(
                    f"{null_dates} tile(s) ({pct:.0f}%) have no acquisition date metadata."
                )

        return warnings

    # ------------------------------------------------------------------
    # Subsetting
    # ------------------------------------------------------------------

    def filter_by_bbox(self, bbox: tuple[float, float, float, float]) -> SearchResult:
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
        subset = self._gdf[mask].copy()
        return SearchResult(subset, self._product, self._query_params, self._subset_items(subset))

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
        subset = self._gdf.head(n).copy()
        return SearchResult(subset, self._product, self._query_params, self._subset_items(subset))

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

    def validate_format(self, sample: int = 5, deep: bool = False) -> list[Any]:
        """Validate tiles for cloud-native format compliance.

        Spot-checks a sample of tiles from the result set using remote
        range-request reads. Checks COGs for internal tiling, overviews,
        CRS, and compression. Checks COPC for spatial index and CRS.

        Parameters
        ----------
        sample : int
            Maximum number of tiles to validate. Default 5.
            Set to 0 to validate all tiles.
        deep : bool
            If True, use rio-cogeo for thorough COG validation.

        Returns
        -------
        list[ValidationResult]
            One result per tile checked.
        """
        from abovepy.validate import validate as _validate

        urls = self._gdf["asset_url"].tolist()
        if sample > 0:
            urls = urls[:sample]
        return [_validate(url, deep=deep) for url in urls]

    def __repr__(self) -> str:
        est = self.estimate_size()
        return f"SearchResult({self._product.key!r}, {self.count} tile(s), ~{est['total_mb']} MB)"

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
