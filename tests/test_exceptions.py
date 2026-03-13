"""Tests for the custom exception hierarchy."""

from abovepy._exceptions import (
    AbovepyError,
    BboxError,
    CountyError,
    DownloadError,
    MosaicError,
    ProductError,
    ReadError,
    SearchError,
)


class TestInheritance:
    """All exceptions inherit from AbovepyError."""

    def test_search_error(self):
        assert issubclass(SearchError, AbovepyError)

    def test_download_error(self):
        assert issubclass(DownloadError, AbovepyError)

    def test_read_error(self):
        assert issubclass(ReadError, AbovepyError)

    def test_mosaic_error(self):
        assert issubclass(MosaicError, AbovepyError)

    def test_product_error(self):
        assert issubclass(ProductError, AbovepyError)

    def test_county_error(self):
        assert issubclass(CountyError, AbovepyError)

    def test_bbox_error(self):
        assert issubclass(BboxError, AbovepyError)


class TestBackwardCompatibility:
    """ValueError subclasses remain catchable as ValueError."""

    def test_product_error_is_value_error(self):
        assert issubclass(ProductError, ValueError)

    def test_county_error_is_value_error(self):
        assert issubclass(CountyError, ValueError)

    def test_bbox_error_is_value_error(self):
        assert issubclass(BboxError, ValueError)

    def test_catch_product_error_as_value_error(self):
        try:
            raise ProductError("test")
        except ValueError:
            pass  # Should be caught

    def test_catch_all_as_abovepy_error(self):
        for cls in [
            SearchError,
            DownloadError,
            ReadError,
            MosaicError,
            ProductError,
            CountyError,
            BboxError,
        ]:
            try:
                raise cls("test")
            except AbovepyError:
                pass  # All should be caught
