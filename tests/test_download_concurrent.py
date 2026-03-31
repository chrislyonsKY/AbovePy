"""Tests for concurrent and resumable download functionality."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from abovepy._constants import DEFAULT_DOWNLOAD_WORKERS
from abovepy._download import _download_file, download_tiles


def _make_mock_tiles(urls):
    """Create a mock GeoDataFrame-like object with asset_url column."""
    return pd.DataFrame({"asset_url": urls})


# ---------------------------------------------------------------------------
# Helpers to build mock httpx responses
# ---------------------------------------------------------------------------


def _mock_stream_response(status_code=200, data=b"tiledata"):
    """Return a context-manager mock that simulates ``client.stream()``."""
    response = MagicMock()
    response.status_code = status_code
    response.raise_for_status = MagicMock()
    response.iter_bytes = MagicMock(return_value=iter([data]))
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)
    return response


class TestThreadPoolExecutorWorkers:
    """ThreadPoolExecutor receives the correct max_workers value."""

    def test_default_max_workers(self, tmp_path):
        from concurrent.futures import ThreadPoolExecutor as _RealTPE

        tiles = _make_mock_tiles(["https://example.com/a.tif"])
        with (
            patch("abovepy._download._download_file"),
            patch(
                "abovepy._download.ThreadPoolExecutor",
                wraps=_RealTPE,
            ) as mock_pool,
        ):
            download_tiles(tiles, output_dir=tmp_path)
        mock_pool.assert_called_once_with(max_workers=DEFAULT_DOWNLOAD_WORKERS)

    def test_custom_max_workers(self, tmp_path):
        from concurrent.futures import ThreadPoolExecutor as _RealTPE

        tiles = _make_mock_tiles(["https://example.com/a.tif"])
        with (
            patch("abovepy._download._download_file"),
            patch(
                "abovepy._download.ThreadPoolExecutor",
                wraps=_RealTPE,
            ) as mock_pool,
        ):
            download_tiles(tiles, output_dir=tmp_path, max_workers=8)
        mock_pool.assert_called_once_with(max_workers=8)


class TestPartFileProtocol:
    """Download creates .part then renames to final destination."""

    def test_download_creates_part_then_renames(self, tmp_path):
        dest = tmp_path / "tile.tif"
        part = tmp_path / "tile.tif.part"

        client = MagicMock()
        response = _mock_stream_response(200, b"full-tile-data")
        client.stream = MagicMock(return_value=response)

        _download_file(client, "https://example.com/tile.tif", dest, resume=True)

        # .part should have been renamed to dest
        assert dest.exists()
        assert not part.exists()
        assert dest.read_bytes() == b"full-tile-data"

    def test_part_file_not_left_on_success(self, tmp_path):
        dest = tmp_path / "tile.tif"

        client = MagicMock()
        response = _mock_stream_response(200, b"data")
        client.stream = MagicMock(return_value=response)

        _download_file(client, "https://example.com/tile.tif", dest)

        assert dest.exists()
        assert not dest.with_suffix(".tif.part").exists()


class TestResumeRangeHeader:
    """Resume sends Range header when .part file exists."""

    def test_range_header_sent_on_resume(self, tmp_path):
        dest = tmp_path / "tile.tif"
        part = tmp_path / "tile.tif.part"
        part.write_bytes(b"partial")  # 7 bytes

        client = MagicMock()
        response = _mock_stream_response(206, b"-remaining")
        client.stream = MagicMock(return_value=response)

        _download_file(client, "https://example.com/tile.tif", dest, resume=True)

        # Verify Range header was passed
        client.stream.assert_called_once()
        _, kwargs = client.stream.call_args
        assert kwargs["headers"]["Range"] == "bytes=7-"

        # File should contain partial + remaining (appended)
        assert dest.exists()
        assert dest.read_bytes() == b"partial-remaining"

    def test_server_returns_200_starts_fresh(self, tmp_path):
        dest = tmp_path / "tile.tif"
        part = tmp_path / "tile.tif.part"
        part.write_bytes(b"old-partial-data")

        client = MagicMock()
        # Server ignores Range header and returns 200 with full content
        response = _mock_stream_response(200, b"full-new-data")
        client.stream = MagicMock(return_value=response)

        _download_file(client, "https://example.com/tile.tif", dest, resume=True)

        # Range header still sent
        _, kwargs = client.stream.call_args
        assert "Range" in kwargs["headers"]

        # But since response is 200, file is overwritten (wb mode)
        assert dest.exists()
        assert dest.read_bytes() == b"full-new-data"


class TestFailedDownloadLeavesPartFile:
    """Failed download leaves .part file intact for later resume."""

    def test_part_file_remains_on_failure(self, tmp_path):
        from abovepy._exceptions import DownloadError

        dest = tmp_path / "tile.tif"

        client = MagicMock()
        # First chunk writes data, then raise on the second
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.iter_bytes = MagicMock(side_effect=ConnectionError("broken"))
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        client.stream = MagicMock(return_value=response)

        with pytest.raises(DownloadError):
            _download_file(client, "https://example.com/tile.tif", dest, resume=True)

        part = tmp_path / "tile.tif.part"
        # .part file should exist (even if empty from the failed write)
        assert part.exists()
        # Final destination should NOT exist
        assert not dest.exists()


class TestDefaultWorkers:
    """DEFAULT_DOWNLOAD_WORKERS constant is 4."""

    def test_default_is_four(self):
        assert DEFAULT_DOWNLOAD_WORKERS == 4


class TestContentLengthValidation:
    """Content-Length header validation on completed downloads."""

    def test_size_mismatch_logs_warning(self, tmp_path, caplog):
        import logging

        dest = tmp_path / "tile.tif"

        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.iter_bytes = MagicMock(return_value=iter([b"short"]))
        # Report a content-length larger than what we actually wrote
        response.headers = {"content-length": "9999"}
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        client.stream = MagicMock(return_value=response)

        with caplog.at_level(logging.WARNING):
            _download_file(client, "https://example.com/tile.tif", dest)

        assert "Size mismatch" in caplog.text

    def test_matching_size_no_warning(self, tmp_path, caplog):
        import logging

        dest = tmp_path / "tile.tif"
        data = b"exact-data"

        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.iter_bytes = MagicMock(return_value=iter([data]))
        response.headers = {"content-length": str(len(data))}
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        client.stream = MagicMock(return_value=response)

        with caplog.at_level(logging.WARNING):
            _download_file(client, "https://example.com/tile.tif", dest)

        assert "Size mismatch" not in caplog.text
        assert dest.read_bytes() == data

    def test_no_content_length_header_skips_check(self, tmp_path, caplog):
        import logging

        dest = tmp_path / "tile.tif"

        client = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        response.iter_bytes = MagicMock(return_value=iter([b"data"]))
        response.headers = {}
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        client.stream = MagicMock(return_value=response)

        with caplog.at_level(logging.WARNING):
            _download_file(client, "https://example.com/tile.tif", dest)

        assert "Size mismatch" not in caplog.text
        assert dest.exists()


class TestHierarchicalFilenames:
    """Downloads with collection_id get placed in product subdirectories."""

    def test_collection_id_creates_subdirectory(self, tmp_path):
        tiles = pd.DataFrame(
            {
                "asset_url": ["https://example.com/tile1.tif", "https://example.com/tile2.tif"],
                "collection_id": ["dem-phase3", "dem-phase3"],
            }
        )

        with patch("abovepy._download._download_file") as mock_dl:
            download_tiles(tiles, output_dir=tmp_path)

        # Verify subdirectory was created
        assert (tmp_path / "dem-phase3").is_dir()
        # Verify _download_file was called with paths inside the subdirectory
        for call in mock_dl.call_args_list:
            dest = call.args[2]  # third positional arg is dest
            assert "dem-phase3" in str(dest)

    def test_mixed_collections_create_separate_subdirs(self, tmp_path):
        tiles = pd.DataFrame(
            {
                "asset_url": ["https://example.com/a.tif", "https://example.com/b.tif"],
                "collection_id": ["dem-phase3", "orthos-phase3"],
            }
        )

        with patch("abovepy._download._download_file"):
            download_tiles(tiles, output_dir=tmp_path)

        assert (tmp_path / "dem-phase3").is_dir()
        assert (tmp_path / "orthos-phase3").is_dir()

    def test_no_collection_id_uses_flat_dir(self, tmp_path):
        tiles = pd.DataFrame(
            {
                "asset_url": ["https://example.com/tile.tif"],
            }
        )

        with patch("abovepy._download._download_file") as mock_dl:
            download_tiles(tiles, output_dir=tmp_path)

        # Should be called with dest directly in output_dir, no subdirectory
        dest = mock_dl.call_args.args[2]
        assert dest.parent == tmp_path

    def test_existing_file_in_subdirectory_skipped(self, tmp_path):
        subdir = tmp_path / "dem-phase3"
        subdir.mkdir()
        (subdir / "tile.tif").write_bytes(b"existing")

        tiles = pd.DataFrame(
            {
                "asset_url": ["https://example.com/tile.tif"],
                "collection_id": ["dem-phase3"],
            }
        )

        with patch("abovepy._download._download_file") as mock_dl:
            result = download_tiles(tiles, output_dir=tmp_path, overwrite=False)

        mock_dl.assert_not_called()
        assert len(result) == 1
        assert result[0] == subdir / "tile.tif"
