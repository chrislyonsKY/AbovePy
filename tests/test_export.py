"""Tests for export helpers."""


import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box

from abovepy.export import to_geopackage, to_geotiff, to_shapefile


@pytest.fixture
def sample_gdf():
    """A simple GeoDataFrame for vector export tests."""
    return gpd.GeoDataFrame(
        {"tile_id": ["A", "B"], "product": ["dem", "dem"]},
        geometry=[box(0, 0, 1, 1), box(1, 1, 2, 2)],
        crs="EPSG:4326",
    )


@pytest.fixture
def sample_raster():
    """A simple raster array + profile for raster export tests."""
    data = np.random.rand(1, 64, 64).astype(np.float32)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": 64,
        "height": 64,
        "count": 1,
        "crs": "EPSG:4326",
        "transform": (0.01, 0.0, -85.0, 0.0, -0.01, 39.0, 0.0, 0.0, 1.0),
    }
    return data, profile


# ---------------------------------------------------------------------------
# to_geotiff
# ---------------------------------------------------------------------------


class TestToGeotiff:
    def test_creates_file(self, sample_raster, tmp_path):
        data, profile = sample_raster
        output = tmp_path / "test.tif"
        result = to_geotiff(data, profile, output)
        assert result.exists()
        assert result == output

    def test_2d_array_promoted(self, sample_raster, tmp_path):
        data, profile = sample_raster
        output = tmp_path / "test2d.tif"
        result = to_geotiff(data[0], profile, output)  # Pass 2D
        assert result.exists()

    def test_creates_parent_dirs(self, sample_raster, tmp_path):
        data, profile = sample_raster
        output = tmp_path / "subdir" / "deep" / "test.tif"
        result = to_geotiff(data, profile, output)
        assert result.exists()


# ---------------------------------------------------------------------------
# to_geopackage
# ---------------------------------------------------------------------------


class TestToGeopackage:
    def test_creates_file(self, sample_gdf, tmp_path):
        output = tmp_path / "test.gpkg"
        result = to_geopackage(sample_gdf, output)
        assert result.exists()
        assert result == output

    def test_custom_layer_name(self, sample_gdf, tmp_path):
        output = tmp_path / "test.gpkg"
        to_geopackage(sample_gdf, output, layer="results")
        # Read back and verify
        read_back = gpd.read_file(output, layer="results")
        assert len(read_back) == 2

    def test_creates_parent_dirs(self, sample_gdf, tmp_path):
        output = tmp_path / "subdir" / "test.gpkg"
        result = to_geopackage(sample_gdf, output)
        assert result.exists()


# ---------------------------------------------------------------------------
# to_shapefile
# ---------------------------------------------------------------------------


class TestToShapefile:
    def test_creates_file(self, sample_gdf, tmp_path):
        output = tmp_path / "test.shp"
        result = to_shapefile(sample_gdf, output)
        assert result.exists()
        assert result == output

    def test_creates_parent_dirs(self, sample_gdf, tmp_path):
        output = tmp_path / "subdir" / "test.shp"
        result = to_shapefile(sample_gdf, output)
        assert result.exists()
