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


class TestExceptionMessages:
    """Exceptions preserve messages and support string formatting."""

    def test_search_error_message(self):
        exc = SearchError("STAC API unreachable")
        assert str(exc) == "STAC API unreachable"

    def test_download_error_message(self):
        exc = DownloadError("HTTP 403 for tile.tif")
        assert "403" in str(exc)

    def test_product_error_includes_key(self):
        exc = ProductError("Unknown product 'bad_key'")
        assert "bad_key" in str(exc)

    def test_county_error_includes_name(self):
        exc = CountyError("Unknown county 'Atlantis'")
        assert "Atlantis" in str(exc)

    def test_bbox_error_includes_values(self):
        exc = BboxError("xmin (5.0) must be less than xmax (3.0)")
        assert "5.0" in str(exc)

    def test_exception_chaining(self):
        """Exceptions support __cause__ for chaining."""
        original = ConnectionError("timeout")
        exc = SearchError("STAC failed")
        exc.__cause__ = original
        assert exc.__cause__ is original


class TestExceptionPickle:
    """Exceptions can be pickled (important for multiprocessing)."""

    def test_pickle_roundtrip(self):
        import pickle

        for cls in [
            SearchError,
            DownloadError,
            ReadError,
            MosaicError,
            ProductError,
            CountyError,
            BboxError,
        ]:
            exc = cls("test message")
            restored = pickle.loads(pickle.dumps(exc))
            assert str(restored) == "test message"
            assert type(restored) is cls
