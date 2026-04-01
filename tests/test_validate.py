"""Tests for cloud-native format validation."""

from unittest.mock import MagicMock, patch

from abovepy.validate import (
    Check,
    ValidationResult,
    _validate_cog,
    _validate_copc,
    _validate_pointcloud,
    validate,
)


class TestValidationResult:
    def test_summary_valid(self):
        result = ValidationResult(
            source="test.tif",
            format="COG",
            is_valid=True,
            checks=[Check("a", True, "ok"), Check("b", True, "ok")],
        )
        assert "VALID" in result.summary()
        assert "2/2" in result.summary()

    def test_summary_invalid(self):
        result = ValidationResult(
            source="test.tif",
            format="GeoTIFF",
            is_valid=False,
            checks=[Check("a", True, "ok"), Check("b", False, "bad")],
        )
        assert "INVALID" in result.summary()
        assert "1/2" in result.summary()

    def test_repr(self):
        result = ValidationResult(source="x.tif", format="COG", is_valid=True)
        assert "COG" in repr(result)


class TestFormatDetection:
    def test_unknown_extension(self):
        result = validate("file.xyz")
        assert result.format == "unknown"
        assert not result.is_valid

    @patch("abovepy.validate._validate_cog")
    def test_tif_routes_to_cog(self, mock_cog):
        mock_cog.return_value = ValidationResult("f.tif", "COG", True)
        validate("f.tif")
        mock_cog.assert_called_once_with("f.tif")

    @patch("abovepy.validate._validate_cog_deep")
    def test_tif_deep_routes_to_deep(self, mock_deep):
        mock_deep.return_value = ValidationResult("f.tif", "COG", True)
        validate("f.tif", deep=True)
        mock_deep.assert_called_once_with("f.tif")

    @patch("abovepy.validate._validate_copc")
    def test_copc_laz_routes_to_copc(self, mock_copc):
        mock_copc.return_value = ValidationResult("f.copc.laz", "COPC", True)
        validate("f.copc.laz")
        mock_copc.assert_called_once_with("f.copc.laz")

    @patch("abovepy.validate._validate_pointcloud")
    def test_laz_routes_to_pointcloud(self, mock_pc):
        mock_pc.return_value = ValidationResult("f.laz", "LAZ", False)
        validate("f.laz")
        mock_pc.assert_called_once_with("f.laz")


class TestValidateCog:
    @patch("rasterio.open")
    def test_valid_cog(self, mock_open):
        ds = MagicMock()
        ds.profile = {
            "driver": "GTiff",
            "tiled": True,
            "blockxsize": 512,
            "blockysize": 512,
            "compress": "deflate",
        }
        ds.crs = MagicMock()
        ds.overviews.return_value = [2, 4, 8]
        ds.width = 5000
        ds.height = 5000
        ds.count = 1
        ds.dtypes = ("float32",)
        mock_open.return_value.__enter__ = MagicMock(return_value=ds)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = _validate_cog("/data/dem.tif")
        assert result.is_valid
        assert result.format == "COG"
        assert any(c.name == "internal_tiling" and c.passed for c in result.checks)
        assert any(c.name == "has_overviews" and c.passed for c in result.checks)

    @patch("rasterio.open")
    def test_non_tiled_geotiff(self, mock_open):
        ds = MagicMock()
        ds.profile = {
            "driver": "GTiff",
            "tiled": False,
            "blockxsize": 0,
            "blockysize": 0,
            "compress": None,
        }
        ds.crs = MagicMock()
        ds.overviews.return_value = []
        ds.width = 100
        ds.height = 100
        ds.count = 1
        ds.dtypes = ("uint8",)
        mock_open.return_value.__enter__ = MagicMock(return_value=ds)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = _validate_cog("/data/plain.tif")
        assert not result.is_valid
        assert result.format == "GeoTIFF"

    @patch("rasterio.open", side_effect=Exception("not found"))
    def test_unreadable_file(self, mock_open):
        result = _validate_cog("/data/missing.tif")
        assert not result.is_valid
        assert result.format == "unknown"

    def test_s3_uri_conversion(self):
        from abovepy.validate import _open_rasterio_source

        assert _open_rasterio_source("s3://bucket/key.tif") == "/vsis3/bucket/key.tif"
        assert (
            _open_rasterio_source("https://example.com/f.tif")
            == "/vsicurl/https://example.com/f.tif"
        )
        assert _open_rasterio_source("/local/file.tif") == "/local/file.tif"


class TestValidateCopc:
    @patch("laspy.CopcReader.open")
    def test_valid_copc(self, mock_open):
        reader = MagicMock()
        header = MagicMock()
        header.point_format.id = 6
        header.point_count = 1_000_000
        header.mins = MagicMock()
        header.mins.__getitem__ = lambda s, i: [100.0, 200.0, 300.0][i]
        header.mins.tolist.return_value = [100.0, 200.0, 300.0]
        header.maxs = MagicMock()
        header.maxs.__getitem__ = lambda s, i: [500.0, 600.0, 700.0][i]
        header.maxs.tolist.return_value = [500.0, 600.0, 700.0]
        crs_mock = MagicMock()
        crs_mock.to_wkt.return_value = "PROJCS[...]"
        header.parse_crs.return_value = crs_mock
        reader.header = header
        mock_open.return_value = reader

        result = _validate_copc("data/cloud.copc.laz")
        assert result.is_valid
        assert result.format == "COPC"
        assert any(c.name == "copc_format" and c.passed for c in result.checks)

    @patch("laspy.CopcReader.open", side_effect=Exception("not a copc file"))
    def test_non_copc_laz(self, mock_open):
        result = _validate_copc("data/plain.laz")
        assert not result.is_valid
        assert result.format == "LAZ"


class TestValidatePointcloud:
    @patch("laspy.open")
    def test_plain_laz(self, mock_open):
        reader = MagicMock()
        reader.header.point_count = 500_000
        mock_open.return_value.__enter__ = MagicMock(return_value=reader)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        result = _validate_pointcloud("data/old.laz")
        assert not result.is_valid
        assert result.format == "LAZ"
        assert any("not COPC" in c.message for c in result.checks)
