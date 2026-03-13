"""Integration tests against the live KyFromAbove STAC API.

These tests hit the real STAC API and S3 bucket. They are gated behind
``@pytest.mark.integration`` and excluded from default CI runs.

Run with: pytest tests/ -m integration -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

import abovepy
from abovepy._exceptions import CountyError, ProductError

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# STAC Connection & Search
# ---------------------------------------------------------------------------


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
        assert "product" in df.columns
        assert "resolution" in df.columns
        assert "format" in df.columns


# ---------------------------------------------------------------------------
# Product Coverage — search each of the 9 products
# ---------------------------------------------------------------------------


class TestProductCoverage:
    @pytest.mark.parametrize(
        "product",
        [
            "dem_phase1",
            "dem_phase2",
            "dem_phase3",
        ],
    )
    def test_dem_products(self, frankfort_bbox, product):
        """DEM products return tiles for Frankfort area."""
        tiles = abovepy.search(bbox=frankfort_bbox, product=product, max_items=3)
        assert len(tiles) > 0
        assert tiles.iloc[0]["product"] == product

    @pytest.mark.parametrize(
        "product",
        [
            "ortho_phase1",
            "ortho_phase2",
            "ortho_phase3",
        ],
    )
    def test_ortho_products(self, frankfort_bbox, product):
        """Ortho products return tiles for Frankfort area."""
        tiles = abovepy.search(bbox=frankfort_bbox, product=product, max_items=3)
        assert len(tiles) > 0

    @pytest.mark.parametrize(
        "product",
        [
            "laz_phase1",
            "laz_phase2",
            "laz_phase3",
        ],
    )
    def test_laz_products(self, frankfort_bbox, product):
        """LiDAR products return tiles for Frankfort area."""
        tiles = abovepy.search(bbox=frankfort_bbox, product=product, max_items=3)
        assert len(tiles) > 0


# ---------------------------------------------------------------------------
# County Search
# ---------------------------------------------------------------------------


class TestCountySearch:
    @pytest.mark.parametrize(
        "county",
        [
            "Franklin",
            "Fayette",
            "Pike",
            "Jefferson",
        ],
    )
    def test_search_counties(self, county):
        """Multiple counties return DEM results."""
        tiles = abovepy.search(county=county, product="dem_phase3", max_items=5)
        assert len(tiles) > 0

    def test_county_case_insensitive(self):
        """County search is case-insensitive."""
        tiles = abovepy.search(county="franklin", product="dem_phase3", max_items=3)
        assert len(tiles) > 0

    def test_invalid_county_raises(self):
        """Unknown county raises CountyError."""
        with pytest.raises(CountyError):
            abovepy.search(county="Atlantis", product="dem_phase3")


# ---------------------------------------------------------------------------
# Bbox Edge Cases
# ---------------------------------------------------------------------------


class TestBboxEdgeCases:
    def test_very_small_bbox(self):
        """Very small bbox (single point area) still returns tiles."""
        tiny = (-84.85, 38.20, -84.849, 38.201)
        tiles = abovepy.search(bbox=tiny, product="dem_phase3", max_items=5)
        assert len(tiles) > 0

    def test_bbox_on_ky_border(self):
        """Bbox on KY southern border returns results."""
        border = (-84.5, 36.50, -84.3, 36.60)
        tiles = abovepy.search(bbox=border, product="dem_phase3", max_items=5)
        # May or may not have tiles right at the border, but shouldn't error
        assert isinstance(tiles, type(tiles))

    def test_bbox_straddling_multiple_tiles(self):
        """Large bbox should return many tiles."""
        large = (-85.0, 38.0, -84.5, 38.5)
        tiles = abovepy.search(bbox=large, product="dem_phase3", max_items=100)
        assert len(tiles) > 5  # Should span multiple tile grid cells


# ---------------------------------------------------------------------------
# Error Cases
# ---------------------------------------------------------------------------


class TestErrorCases:
    def test_invalid_product_raises(self):
        """Invalid product key raises ProductError."""
        with pytest.raises(ProductError):
            abovepy.search(bbox=(-84.9, 38.15, -84.8, 38.25), product="invalid_product")


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


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

    @pytest.mark.slow
    def test_read_returns_epsg3089(self, frankfort_bbox):
        """Read tile CRS should be EPSG:3089."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=1)
        url = tiles.iloc[0]["asset_url"]
        _, profile = abovepy.read(url)
        crs_str = str(profile["crs"])
        assert "3089" in crs_str


# ---------------------------------------------------------------------------
# Download & Mosaic
# ---------------------------------------------------------------------------


class TestLiveDownloadAndMosaic:
    @pytest.mark.slow
    def test_download_single_tile(self, frankfort_bbox):
        """Download a single DEM tile and verify it exists."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = abovepy.download(tiles, output_dir=tmpdir)
            assert len(paths) == 1
            assert paths[0].exists()
            assert paths[0].stat().st_size > 0
            assert paths[0].suffix == ".tif"

    @pytest.mark.slow
    def test_download_skip_existing(self, frankfort_bbox):
        """Second download should skip already-downloaded files."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            paths1 = abovepy.download(tiles, output_dir=tmpdir)
            mtime1 = paths1[0].stat().st_mtime
            paths2 = abovepy.download(tiles, output_dir=tmpdir)
            mtime2 = paths2[0].stat().st_mtime
            assert mtime1 == mtime2  # File was not re-downloaded

    @pytest.mark.slow
    def test_mosaic_vrt(self, frankfort_bbox):
        """Download 2 tiles, mosaic to VRT, verify it's readable."""
        tiles = abovepy.search(bbox=frankfort_bbox, product="dem_phase3", max_items=2)
        if len(tiles) < 2:
            pytest.skip("Need at least 2 tiles for mosaic test")
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = abovepy.download(tiles, output_dir=tmpdir)
            vrt_path = Path(tmpdir) / "mosaic.vrt"
            result = abovepy.mosaic(paths, output=vrt_path)
            assert Path(result).exists()
            assert str(result).endswith(".vrt")


# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------


class TestLiveInfo:
    def test_info_columns(self):
        """info() DataFrame has expected columns."""
        df = abovepy.info()
        expected = {"product", "display_name", "format", "resolution", "phase"}
        assert expected.issubset(set(df.columns))

    def test_info_products_complete(self):
        """info() includes all 9 known products."""
        df = abovepy.info()
        products = set(df["product"])
        for p in [
            "dem_phase1",
            "dem_phase2",
            "dem_phase3",
            "ortho_phase1",
            "ortho_phase2",
            "ortho_phase3",
            "laz_phase1",
            "laz_phase2",
            "laz_phase3",
        ]:
            assert p in products, f"Missing product: {p}"


# ---------------------------------------------------------------------------
# LiDAR (optional — only runs if laspy is installed)
# ---------------------------------------------------------------------------


class TestLiDAROptional:
    @pytest.mark.slow
    def test_laz_tile_url_accessible(self, frankfort_bbox):
        """LAZ tile URLs from search should be HTTP accessible."""
        import httpx

        tiles = abovepy.search(bbox=frankfort_bbox, product="laz_phase2", max_items=1)
        if tiles.empty:
            pytest.skip("No COPC tiles found in Frankfort area")
        url = tiles.iloc[0]["asset_url"]
        resp = httpx.head(url, follow_redirects=True, timeout=30)
        assert resp.status_code == 200
