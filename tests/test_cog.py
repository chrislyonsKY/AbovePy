"""Tests for COG read operations."""

from abovepy.io.cog import _to_vsi_path, _reproject_bbox


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
        for orig, res in zip(bbox, result):
            assert abs(orig - res) < 1e-6
