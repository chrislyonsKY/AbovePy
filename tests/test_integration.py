"""Integration tests against the live KyFromAbove STAC API.

These tests hit the real STAC API and S3 bucket. They are gated behind
``@pytest.mark.integration`` and excluded from default CI runs.

Run with: pytest tests/ -m integration -v
"""

import pytest

import abovepy

pytestmark = pytest.mark.integration


class TestLiveSTACConnection:
    def test_client_connects(self):
        """Client can connect and list collections."""
        client = abovepy.KyFromAboveClient()
        stac = client.get_stac_client()
        collections = list(stac.get_collections())
        assert len(collections) > 0

    def test_search_dem_phase3_frankfort(self, frankfort_bbox):
        """Search returns DEM tiles for the Frankfort area."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=10)
        assert len(tiles) > 0
        assert "tile_id" in tiles.columns
        assert "asset_url" in tiles.columns

    def test_search_by_county(self):
        """County-based search returns results."""
        tiles = abovepy.search(county="Franklin", product="dem_phase3", max_items=10)
        assert len(tiles) > 0

    def test_search_ortho_phase3(self, frankfort_bbox):
        """Ortho search returns results."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="ortho_phase3", max_items=5)
        assert len(tiles) > 0

    def test_search_empty_area_returns_empty(self):
        """Search outside KY returns empty GeoDataFrame."""
        tiles = abovepy.search(bbox=(-70.0, 40.0, -69.9, 40.1), product="dem_phase3")
        assert tiles.empty

    def test_asset_urls_are_accessible(self, frankfort_bbox):
        """Asset URLs from search should return HTTP 200."""
        import httpx

        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=1)
        url = tiles.iloc[0]["asset_url"]
        resp = httpx.head(url, follow_redirects=True, timeout=30)
        assert resp.status_code == 200

    def test_info_all_products(self):
        """info() returns metadata for all 9 products."""
        df = abovepy.info()
        assert len(df) == 9


class TestLiveRead:
    @pytest.mark.slow
    def test_read_cog_windowed(self, frankfort_bbox):
        """Read a real tile with a windowed bbox."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=1)
        url = tiles.iloc[0]["asset_url"]
        data, profile = abovepy.read(url, bbox=frankfort_bbox)
        assert data.shape[0] >= 1
        assert profile["crs"] is not None

    @pytest.mark.slow
    def test_read_full_tile(self, frankfort_bbox):
        """Read a full tile without bbox clipping."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=1)
        url = tiles.iloc[0]["asset_url"]
        data, profile = abovepy.read(url)
        assert data.shape[1] > 0
        assert data.shape[2] > 0
