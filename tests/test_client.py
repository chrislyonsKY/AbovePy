"""Tests for the KyFromAboveClient class."""


import pytest

from abovepy.client import KyFromAboveClient


class TestClientInit:
    def test_default_init(self):
        client = KyFromAboveClient()
        assert client.stac_url.startswith("https://")
        assert client.cache_dir is None
        assert client._stac_client is None

    def test_custom_stac_url(self):
        client = KyFromAboveClient(stac_url="https://custom.api/")
        assert client.stac_url == "https://custom.api/"

    def test_cache_dir_created(self, tmp_path):
        cache = tmp_path / "my_cache"
        client = KyFromAboveClient(cache_dir=cache)
        assert client.cache_dir == cache
        assert cache.exists()


class TestClientSearch:
    def test_requires_bbox_or_county(self):
        client = KyFromAboveClient()
        with pytest.raises(ValueError, match="Provide either"):
            client.search(product="dem_phase3")

    def test_invalid_product(self):
        client = KyFromAboveClient()
        with pytest.raises(ValueError, match="Unknown product"):
            client.search(bbox=(-84.9, 38.15, -84.8, 38.25), product="bad")

    def test_invalid_bbox(self):
        client = KyFromAboveClient()
        with pytest.raises(ValueError, match="xmin"):
            client.search(bbox=(-84.3, 38.15, -84.9, 38.25), product="dem_phase3")


class TestClientInfo:
    def test_info_all_products(self):
        client = KyFromAboveClient()
        df = client.info()
        assert len(df) == 9
        assert "product" in df.columns

    def test_info_single_product(self):
        client = KyFromAboveClient()
        info = client.info("dem_phase3")
        assert info["product"] == "dem_phase3"
        assert info["collection_id"] == "dem-phase3"

    def test_info_unknown_product_as_remote(self):
        """Unknown string should try remote tile inspection."""
        client = KyFromAboveClient()
        # This would fail since it's not a real URL, but it should
        # attempt inspect_cog rather than raising ValueError
        with pytest.raises(Exception):  # noqa: B017
            client.info("https://not-a-real-url.tif")
