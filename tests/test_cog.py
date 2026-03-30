"""Tests for COG read operations."""

from abovepy.io.cog import _reproject_bbox, _to_vsi_path


class TestToVsiPath:
    def test_s3_uri(self):
        assert _to_vsi_path("s3://kyfromabove/dem/tile.tif") == "/vsis3/kyfromabove/dem/tile.tif"

    def test_https_url(self):
        result = _to_vsi_path("https://example.com/tile.tif")
        assert result == "/vsicurl/https://example.com/tile.tif"

    def test_http_url(self):
        result = _to_vsi_path("http://example.com/tile.tif")
        assert result == "/vsicurl/http://example.com/tile.tif"

    def test_local_path(self):
        assert _to_vsi_path("/data/tile.tif") == "/data/tile.tif"

    def test_windows_path(self):
        assert _to_vsi_path("C:\\data\\tile.tif") == "C:\\data\\tile.tif"


class TestReprojectBbox:
    def test_4326_to_3089(self):
        bbox_4326 = (-84.9, 38.15, -84.8, 38.25)
        bbox_3089 = _reproject_bbox(bbox_4326, "EPSG:4326", "EPSG:3089")

        # Kentucky coords in EPSG:3089 are large US feet values
        assert all(abs(v) > 1000 for v in bbox_3089)
        assert bbox_3089[0] < bbox_3089[2]
        assert bbox_3089[1] < bbox_3089[3]

    def test_identity_transform(self):
        bbox = (-84.9, 38.15, -84.8, 38.25)
        result = _reproject_bbox(bbox, "EPSG:4326", "EPSG:4326")
        for orig, res in zip(bbox, result, strict=True):
            assert abs(orig - res) < 1e-6


class TestReadCogCrsDefault:
    """Test that read_cog defaults bbox CRS to EPSG:4326 via code inspection."""

    def test_source_code_defaults_to_4326(self):
        """Verify the default CRS logic in read_cog source."""
        import inspect

        from abovepy.io.cog import read_cog

        source = inspect.getsource(read_cog)
        # The fix: crs defaults to EPSG:4326 when not provided
        assert 'crs or "EPSG:4326"' in source or "crs or 'EPSG:4326'" in source

    def test_reproject_bbox_called_for_different_crs(self):
        """Verify reprojection produces different coords for 4326→3089."""
        bbox_4326 = (-84.85, 38.18, -84.82, 38.21)
        result = _reproject_bbox(bbox_4326, "EPSG:4326", "EPSG:3089")

        # Reprojected bbox should be in US feet (millions range)
        assert result[0] > 1_000_000
        assert result[1] > 1_000_000
        # Should maintain bbox ordering
        assert result[0] < result[2]
        assert result[1] < result[3]
