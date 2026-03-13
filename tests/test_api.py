"""Tests for the public API surface and convenience functions."""

import abovepy


class TestPublicAPI:
    """Verify all documented public symbols are importable."""

    def test_search_is_callable(self):
        assert callable(abovepy.search)

    def test_download_is_callable(self):
        assert callable(abovepy.download)

    def test_read_is_callable(self):
        assert callable(abovepy.read)

    def test_mosaic_is_callable(self):
        assert callable(abovepy.mosaic)

    def test_download_not_shadowed_by_module(self):
        """Regression: module rename prevents shadowing."""
        import importlib

        importlib.import_module("abovepy._download")
        assert callable(abovepy.download)

    def test_mosaic_not_shadowed_by_module(self):
        """Regression: module rename prevents shadowing."""
        import importlib

        importlib.import_module("abovepy._mosaic")
        assert callable(abovepy.mosaic)

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

    def test_list_counties_is_callable(self):
        assert callable(abovepy.list_counties)


class TestListCounties:
    def test_returns_list(self):
        counties = abovepy.list_counties()
        assert isinstance(counties, list)

    def test_returns_120_counties(self):
        assert len(abovepy.list_counties()) == 120

    def test_sorted_alphabetically(self):
        counties = abovepy.list_counties()
        assert counties == sorted(counties)

    def test_contains_all_regions(self):
        """Spot-check counties from different parts of Kentucky."""
        counties = abovepy.list_counties()
        for name in ["Adair", "Franklin", "Jefferson", "Pike", "Woodford"]:
            assert name in counties


class TestInfoConvenience:
    def test_info_returns_dataframe(self):
        df = abovepy.info()
        assert len(df) == 9
        assert "product" in df.columns

    def test_info_single_product(self):
        result = abovepy.info("dem_phase3")
        assert result["product"] == "dem_phase3"
        assert result["collection_id"] == "dem-phase3"
