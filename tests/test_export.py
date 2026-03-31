"""Tests for export helpers."""

import xml.etree.ElementTree as ET

import geopandas as gpd
import numpy as np
import pytest
from rasterio.transform import from_bounds
from shapely.geometry import box

from abovepy.export import to_geopackage, to_geotiff, to_landxml, to_shapefile


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


# ---------------------------------------------------------------------------
# to_landxml
# ---------------------------------------------------------------------------

NS = "http://www.landxml.org/schema/LandXML-1.2"


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


class TestToLandXML:
    def test_creates_xml_file(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "surface.xml"
        result = to_landxml(data, profile, output)
        assert result.exists()
        assert result.suffix == ".xml"

    def test_valid_xml(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "surface.xml"
        to_landxml(data, profile, output)
        tree = ET.parse(output)
        assert tree.getroot().tag == f"{{{NS}}}LandXML"

    def test_surface_structure(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "surface.xml"
        to_landxml(data, profile, output)
        tree = ET.parse(output)
        root = tree.getroot()
        surface = root.find(f".//{{{NS}}}Surface")
        assert surface is not None
        definition = surface.find(f"{{{NS}}}Definition")
        assert definition is not None
        assert definition.get("surfType") == "TIN"
        pnts = definition.find(f"{{{NS}}}Pnts")
        faces = definition.find(f"{{{NS}}}Faces")
        assert pnts is not None
        assert faces is not None

    def test_point_count_matches(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "surface.xml"
        to_landxml(data, profile, output)
        tree = ET.parse(output)
        points = tree.findall(f".//{{{NS}}}P")
        # 32x32 = 1024 pixels, all valid (no nodata in fixture)
        assert len(points) == 32 * 32

    def test_face_count_positive(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "surface.xml"
        to_landxml(data, profile, output)
        tree = ET.parse(output)
        faces = tree.findall(f".//{{{NS}}}F")
        assert len(faces) > 0

    def test_decimate_reduces_points(self, dem_data, tmp_path):
        data, profile = dem_data
        full = tmp_path / "full.xml"
        decimated = tmp_path / "decimated.xml"
        to_landxml(data, profile, full, decimate=1)
        to_landxml(data, profile, decimated, decimate=2)
        full_pts = len(ET.parse(full).findall(f".//{{{NS}}}P"))
        dec_pts = len(ET.parse(decimated).findall(f".//{{{NS}}}P"))
        assert dec_pts < full_pts

    def test_custom_surface_name(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "surface.xml"
        to_landxml(data, profile, output, surface_name="My Survey DEM")
        tree = ET.parse(output)
        surface = tree.find(f".//{{{NS}}}Surface")
        assert surface.get("name") == "My Survey DEM"

    def test_nodata_excluded(self, tmp_path):
        data = np.ones((16, 16), dtype=np.float32) * 850.0
        data[0:4, 0:4] = -9999.0  # 16 nodata pixels
        transform = from_bounds(1_598_000, 310_000, 1_600_000, 312_000, 16, 16)
        profile = {
            "driver": "GTiff",
            "dtype": "float32",
            "width": 16,
            "height": 16,
            "count": 1,
            "crs": "EPSG:3089",
            "transform": transform,
            "nodata": -9999.0,
        }
        output = tmp_path / "nodata.xml"
        to_landxml(data, profile, output)
        points = ET.parse(output).findall(f".//{{{NS}}}P")
        assert len(points) == 16 * 16 - 16  # 240, not 256

    def test_imperial_units_for_3089(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "surface.xml"
        to_landxml(data, profile, output)
        tree = ET.parse(output)
        imperial = tree.find(f".//{{{NS}}}Imperial")
        assert imperial is not None
        assert imperial.get("linearUnit") == "usSurveyFoot"

    def test_metric_units_for_4326(self, tmp_path):
        data = np.ones((8, 8), dtype=np.float32) * 300.0
        transform = from_bounds(-85.0, 38.0, -84.9, 38.1, 8, 8)
        profile = {
            "driver": "GTiff",
            "dtype": "float32",
            "width": 8,
            "height": 8,
            "count": 1,
            "crs": "EPSG:4326",
            "transform": transform,
        }
        output = tmp_path / "metric.xml"
        to_landxml(data, profile, output)
        tree = ET.parse(output)
        metric = tree.find(f".//{{{NS}}}Metric")
        assert metric is not None

    def test_creates_parent_dirs(self, dem_data, tmp_path):
        data, profile = dem_data
        output = tmp_path / "sub" / "dir" / "surface.xml"
        result = to_landxml(data, profile, output)
        assert result.exists()

    def test_3d_input_squeezed(self, dem_data, tmp_path):
        data, profile = dem_data
        data_3d = data[np.newaxis, :, :]  # (1, 32, 32)
        output = tmp_path / "surface.xml"
        result = to_landxml(data_3d, profile, output)
        assert result.exists()
