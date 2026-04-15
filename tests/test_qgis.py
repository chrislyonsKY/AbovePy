"""Tests for QGIS interoperability."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box


class TestFootprintsGpkg:
    def _make_gdf(self):
        """Create a minimal test GeoDataFrame like search results."""
        return gpd.GeoDataFrame(
            {
                "tile_id": ["N123", "N124"],
                "product": ["dem_phase3", "dem_phase3"],
                "datetime": ["2023-01-01", "2023-01-02"],
                "asset_url": [
                    "https://example.com/N123.tif",
                    "https://example.com/N124.tif",
                ],
            },
            geometry=[
                box(-85.0, 38.0, -84.9, 38.1),
                box(-84.9, 38.0, -84.8, 38.1),
            ],
            crs="EPSG:4326",
        )

    def test_builds_gpkg_file(self, tmp_path):
        from abovepy.qgis import _build_footprints_gpkg

        gdf = self._make_gdf()
        out = tmp_path / "footprints.gpkg"
        result = _build_footprints_gpkg(gdf, out)

        assert result.exists()
        assert result.suffix == ".gpkg"

    def test_gpkg_crs_is_3089(self, tmp_path):
        from abovepy.qgis import _build_footprints_gpkg

        gdf = self._make_gdf()
        out = tmp_path / "footprints.gpkg"
        _build_footprints_gpkg(gdf, out)

        loaded = gpd.read_file(out)
        assert loaded.crs is not None
        assert loaded.crs.to_epsg() == 3089

    def test_gpkg_columns(self, tmp_path):
        from abovepy.qgis import _build_footprints_gpkg

        gdf = self._make_gdf()
        out = tmp_path / "footprints.gpkg"
        _build_footprints_gpkg(gdf, out)

        loaded = gpd.read_file(out)
        assert "tile_id" in loaded.columns
        assert "product" in loaded.columns
        assert "datetime" in loaded.columns
        assert "asset_url" in loaded.columns

    def test_gpkg_layer_name(self, tmp_path):
        try:
            import fiona
            _list_layers = lambda p: fiona.listlayers(str(p))
        except ModuleNotFoundError:
            import pyogrio
            _list_layers = lambda p: list(pyogrio.list_layers(str(p))[:, 0])

        from abovepy.qgis import _build_footprints_gpkg

        gdf = self._make_gdf()
        out = tmp_path / "footprints.gpkg"
        _build_footprints_gpkg(gdf, out)

        layers = _list_layers(out)
        assert "tiles" in layers
