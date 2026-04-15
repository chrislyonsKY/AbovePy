"""Tests for QGIS interoperability."""

from __future__ import annotations

import xml.etree.ElementTree as ET
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


class TestGenerateProject:
    def test_xml_fallback_creates_file(self, tmp_path):
        from abovepy.qgis import generate_project
        from abovepy.products import get_product

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        tile = data_dir / "N123_dem_phase3.tif"
        tile.write_bytes(b"fake")

        footprints = data_dir / "footprints.gpkg"
        footprints.write_bytes(b"fake")

        styles_dir = tmp_path / "styles"
        styles_dir.mkdir()

        product = get_product("dem_phase3")
        result = generate_project(
            package_dir=tmp_path,
            tiles=[tile],
            footprints_path=footprints,
            product=product,
            extent=(1600000.0, 200000.0, 1700000.0, 300000.0),
            styles_dir=styles_dir,
        )

        assert result.exists()
        assert result.suffix == ".qgs"

    def test_xml_is_well_formed(self, tmp_path):
        from abovepy.qgis import generate_project
        from abovepy.products import get_product

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        tile = data_dir / "tile.tif"
        tile.write_bytes(b"fake")

        footprints = data_dir / "footprints.gpkg"
        footprints.write_bytes(b"fake")

        styles_dir = tmp_path / "styles"
        styles_dir.mkdir()

        product = get_product("dem_phase3")
        result = generate_project(
            package_dir=tmp_path,
            tiles=[tile],
            footprints_path=footprints,
            product=product,
            extent=(1600000.0, 200000.0, 1700000.0, 300000.0),
            styles_dir=styles_dir,
        )

        tree = ET.parse(result)
        root = tree.getroot()
        assert root.tag == "qgis"

    def test_xml_contains_layers(self, tmp_path):
        from abovepy.qgis import generate_project
        from abovepy.products import get_product

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        for name in ["a.tif", "b.tif"]:
            (data_dir / name).write_bytes(b"fake")

        footprints = data_dir / "footprints.gpkg"
        footprints.write_bytes(b"fake")

        styles_dir = tmp_path / "styles"
        styles_dir.mkdir()

        product = get_product("dem_phase3")
        result = generate_project(
            package_dir=tmp_path,
            tiles=[data_dir / "a.tif", data_dir / "b.tif"],
            footprints_path=footprints,
            product=product,
            extent=(1600000.0, 200000.0, 1700000.0, 300000.0),
            styles_dir=styles_dir,
        )

        content = result.read_text()
        assert "a.tif" in content
        assert "b.tif" in content
        assert "footprints.gpkg" in content
