"""Tests for export helpers."""

import geopandas as gpd
import numpy as np
import pytest
from rasterio.transform import from_bounds
from shapely.geometry import box

from abovepy.export import to_geopackage, to_geotiff, to_shapefile, to_stl


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


@pytest.fixture
def dem_data():
    """A simple 32x32 DEM with known elevation values and EPSG:3089 profile."""
    rng = np.random.default_rng(42)
    data = (rng.random((32, 32)) * 100 + 800).astype(np.float32)
    transform = from_bounds(1_598_000, 310_000, 1_602_000, 314_000, 32, 32)
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "width": 32,
        "height": 32,
        "count": 1,
        "crs": "EPSG:3089",
        "transform": transform,
        "nodata": -9999.0,
    }
    return data, profile


# ---------------------------------------------------------------------------
# to_landxml removal (v2.2.0)
# ---------------------------------------------------------------------------


class TestLandXMLRemoved:
    def test_access_raises_helpful_error(self):
        import abovepy.export as export_module

        with pytest.raises(AttributeError, match=r"removed in abovepy 2\.2\.0"):
            _ = export_module.to_landxml

    def test_other_missing_attributes_still_raise(self):
        import abovepy.export as export_module

        with pytest.raises(AttributeError, match="no attribute"):
            _ = export_module.does_not_exist


# ---------------------------------------------------------------------------
# to_stl
# ---------------------------------------------------------------------------


class TestToSTL:
    def test_creates_stl_file(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "terrain.stl"
        result = to_stl(data, profile, output)
        assert result.exists()
        assert result.suffix == ".stl"

    def test_valid_binary_stl_header(self, dem_data, tmp_path):
        import struct

        data, profile = dem_data
        output = tmp_path / "terrain.stl"
        to_stl(data, profile, output)

        with open(output, "rb") as f:
            header = f.read(80)
            assert b"AbovePy" in header
            tri_count = struct.unpack("<I", f.read(4))[0]
            assert tri_count > 0

    def test_triangle_count_positive(self, dem_data, tmp_path):
        import struct

        data, profile = dem_data
        output = tmp_path / "terrain.stl"
        to_stl(data, profile, output)

        with open(output, "rb") as f:
            f.read(80)
            tri_count = struct.unpack("<I", f.read(4))[0]

        # Must have triangles for top surface + base + walls
        assert tri_count > 0

    def test_file_size_consistent(self, dem_data, tmp_path):
        import struct

        data, profile = dem_data
        output = tmp_path / "terrain.stl"
        to_stl(data, profile, output)

        with open(output, "rb") as f:
            f.read(80)
            tri_count = struct.unpack("<I", f.read(4))[0]

        # Binary STL: 80 header + 4 count + (50 bytes per triangle)
        expected_size = 80 + 4 + tri_count * 50
        assert output.stat().st_size == expected_size

    def test_exaggeration(self, dem_data, tmp_path):
        data, profile = dem_data
        normal = tmp_path / "normal.stl"
        exaggerated = tmp_path / "exaggerated.stl"
        to_stl(data, profile, normal, exaggeration=1.0)
        to_stl(data, profile, exaggerated, exaggeration=3.0)
        # Same number of triangles, different Z values
        assert normal.stat().st_size == exaggerated.stat().st_size

    def test_decimate_reduces_triangles(self, dem_data, tmp_path):
        data, profile = dem_data
        full = tmp_path / "full.stl"
        decimated = tmp_path / "decimated.stl"
        to_stl(data, profile, full, decimate=1)
        to_stl(data, profile, decimated, decimate=2)
        assert decimated.stat().st_size < full.stat().st_size

    def test_custom_base_height(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "terrain.stl"
        result = to_stl(data, profile, output, base_height=750.0)
        assert result.exists()

    def test_3d_input_squeezed(self, dem_data, tmp_path):
        data, profile = dem_data
        data_3d = data[np.newaxis, :, :]
        output = tmp_path / "terrain.stl"
        result = to_stl(data_3d, profile, output)
        assert result.exists()

    def test_creates_parent_dirs(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "sub" / "dir" / "terrain.stl"
        result = to_stl(data, profile, output)
        assert result.exists()

    def test_nodata_handled(self, tmp_path):
        data = np.ones((16, 16), dtype=np.float32) * 850.0
        data[0:4, 0:4] = -9999.0
        transform = from_bounds(0, 0, 160, 160, 16, 16)
        profile = {
            "driver": "GTiff",
            "dtype": "float32",
            "width": 16,
            "height": 16,
            "transform": transform,
            "nodata": -9999.0,
        }
        output = tmp_path / "nodata.stl"
        result = to_stl(data, profile, output)
        assert result.exists()
        assert result.stat().st_size > 84  # more than just header


# ---------------------------------------------------------------------------
# Dict-column sanitization for GIS writers (v2.2 assets column)
# ---------------------------------------------------------------------------


class TestObjectColumnSanitization:
    @pytest.fixture
    def gdf_with_assets(self):
        return gpd.GeoDataFrame(
            {
                "tile_id": ["A", "B"],
                "assets": [
                    {"data": "https://x/a.tif", "thumbnail": "https://x/a.png"},
                    {"data": "https://x/b.tif"},
                ],
            },
            geometry=[box(0, 0, 1, 1), box(1, 1, 2, 2)],
            crs="EPSG:4326",
        )

    def test_geopackage_roundtrip_with_assets(self, gdf_with_assets, tmp_path):
        import json

        output = to_geopackage(gdf_with_assets, tmp_path / "assets.gpkg")
        read_back = gpd.read_file(output)
        assert json.loads(read_back.iloc[0]["assets"])["data"] == "https://x/a.tif"

    def test_shapefile_write_with_assets(self, gdf_with_assets, tmp_path):
        output = to_shapefile(gdf_with_assets, tmp_path / "assets.shp")
        assert output.exists()

    def test_original_gdf_not_mutated(self, gdf_with_assets, tmp_path):
        to_geopackage(gdf_with_assets, tmp_path / "assets.gpkg")
        assert isinstance(gdf_with_assets.iloc[0]["assets"], dict)
