"""Tests for the STAC wrapper module."""

from unittest.mock import MagicMock, patch

import pytest

from abovepy.stac import (
    _extract_primary_asset_url,
    _search_with_retry,
    clear_cache,
    items_to_geodataframe,
)


def _make_mock_item(item_id="tile-001", asset_key="data", href="https://example.com/tile.tif"):
    """Create a mock STAC item."""
    item = MagicMock()
    item.id = item_id
    item.datetime = None
    item.collection_id = "dem-phase3"
    item.geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [-84.9, 38.15],
                [-84.8, 38.15],
                [-84.8, 38.25],
                [-84.9, 38.25],
                [-84.9, 38.15],
            ]
        ],
    }
    asset = MagicMock()
    asset.href = href
    item.assets = {asset_key: asset}
    return item


class TestExtractPrimaryAssetUrl:
    def test_data_key(self):
        item = _make_mock_item(asset_key="data", href="https://data.tif")
        assert _extract_primary_asset_url(item) == "https://data.tif"

    def test_default_key(self):
        item = _make_mock_item(asset_key="default", href="https://default.tif")
        assert _extract_primary_asset_url(item) == "https://default.tif"

    def test_fallback_non_thumbnail(self):
        item = _make_mock_item(asset_key="some_raster", href="https://raster.tif")
        assert _extract_primary_asset_url(item) == "https://raster.tif"

    def test_no_assets(self):
        item = MagicMock()
        item.assets = {}
        assert _extract_primary_asset_url(item) is None


class TestItemsToGeoDataFrame:
    def test_empty_items(self):
        gdf = items_to_geodataframe([], "dem_phase3")
        assert gdf.empty
        assert "tile_id" in gdf.columns
        assert str(gdf.crs) == "EPSG:4326"

    def test_single_item(self):
        items = [_make_mock_item()]
        gdf = items_to_geodataframe(items, "dem_phase3")
        assert len(gdf) == 1
        assert gdf.iloc[0]["tile_id"] == "tile-001"
        assert gdf.iloc[0]["product"] == "dem_phase3"
        assert gdf.iloc[0]["asset_url"] == "https://example.com/tile.tif"

    def test_multiple_items(self):
        items = [
            _make_mock_item(item_id="tile-001"),
            _make_mock_item(item_id="tile-002"),
            _make_mock_item(item_id="tile-003"),
        ]
        gdf = items_to_geodataframe(items, "ortho_phase3")
        assert len(gdf) == 3
        assert list(gdf["tile_id"]) == ["tile-001", "tile-002", "tile-003"]


class TestSearchWithRetry:
    def test_success_on_first_attempt(self):
        client = MagicMock()
        mock_search = MagicMock()
        mock_search.items.return_value = iter([_make_mock_item()])
        client.search.return_value = mock_search

        items = _search_with_retry(client, "dem-phase3", (-84.9, 38.15, -84.8, 38.25), None, 500)
        assert len(items) == 1
        client.search.assert_called_once()

    @patch("abovepy.stac.time.sleep")
    def test_retries_on_failure(self, mock_sleep):
        client = MagicMock()
        client.search.side_effect = [
            ConnectionError("timeout"),
            ConnectionError("timeout"),
            MagicMock(items=MagicMock(return_value=iter([_make_mock_item()]))),
        ]

        items = _search_with_retry(client, "dem-phase3", (-84.9, 38.15, -84.8, 38.25), None, 500)
        assert len(items) == 1
        assert client.search.call_count == 3

    @patch("abovepy.stac.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep):
        client = MagicMock()
        client.search.side_effect = ConnectionError("timeout")

        with pytest.raises(Exception, match="failed after"):
            _search_with_retry(client, "dem-phase3", (-84.9, 38.15, -84.8, 38.25), None, 500)


def test_clear_cache():
    clear_cache()  # Should not raise
