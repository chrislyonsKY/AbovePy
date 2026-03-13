"""Tests for the public API surface and convenience functions."""

import abovepy


class TestPublicAPI:
    """Verify all documented public symbols are importable."""

    def test_search_is_callable(self):
        assert callable(abovepy.search)

    def test_download_function_exists(self):
        assert "download" in abovepy.__all__

    def test_read_is_callable(self):
        assert callable(abovepy.read)

    def test_mosaic_function_exists(self):
        assert "mosaic" in abovepy.__all__

    def test_info_is_callable(self):
        assert callable(abovepy.info)

    def test_clear_cache_is_callable(self):
        assert callable(abovepy.clear_cache)

    def test_list_products_is_callable(self):
        assert callable(abovepy.list_products)

    def test_version_exists(self):
        assert isinstance(abovepy.__version__, str)
        assert "." in abovepy.__version__

    def test_all_exports_exist(self):
        for name in abovepy.__all__:
            assert hasattr(abovepy, name), f"Missing export: {name}"

    def test_client_class_importable(self):
        assert abovepy.KyFromAboveClient is not None

    def test_product_class_importable(self):
        assert abovepy.Product is not None

    def test_product_type_enum_importable(self):
        assert abovepy.ProductType is not None


class TestInfoConvenience:
    def test_info_returns_dataframe(self):
        df = abovepy.info()
        assert len(df) == 9
        assert "product" in df.columns

    def test_info_single_product(self):
        result = abovepy.info("dem_phase3")
        assert result["product"] == "dem_phase3"
        assert result["collection_id"] == "dem-phase3"
