"""Tests for the download module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from abovepy.download import download_tiles


def _make_mock_tiles(urls):
    """Create a mock GeoDataFrame-like object with asset_url column."""
    import pandas as pd
    return pd.DataFrame({"asset_url": urls})


class TestDownloadTiles:
    def test_empty_urls_returns_empty(self, tmp_path):
        tiles = _make_mock_tiles([])
        result = download_tiles(tiles, output_dir=tmp_path)
        assert result == []

    def test_nan_urls_skipped(self, tmp_path):
        import numpy as np
        tiles = _make_mock_tiles([np.nan, None])
        result = download_tiles(tiles, output_dir=tmp_path)
        assert result == []

    def test_creates_output_dir(self, tmp_path):
        out = tmp_path / "new_dir"
        tiles = _make_mock_tiles([])
        download_tiles(tiles, output_dir=out)
        assert out.exists()

    def test_skip_existing(self, tmp_path):
        # Create existing file
        (tmp_path / "tile.tif").write_bytes(b"data")
        tiles = _make_mock_tiles(["https://example.com/tile.tif"])

        with patch("abovepy.download._download_file") as mock_dl:
            result = download_tiles(tiles, output_dir=tmp_path, overwrite=False)
        assert len(result) == 1
        mock_dl.assert_not_called()
