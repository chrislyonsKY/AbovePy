"""Tests for security utilities — URL validation and remote read guards."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from abovepy._security import check_remote_size, validate_remote_url


class TestValidateRemoteUrl:
    """URL validation warns for untrusted hosts."""

    def test_validate_trusted_url(self, caplog):
        with caplog.at_level(logging.WARNING):
            validate_remote_url("https://kyfromabove.s3.amazonaws.com/tiles/tile.tif")
        assert "not a known KyFromAbove endpoint" not in caplog.text

    def test_validate_untrusted_url(self, caplog):
        with caplog.at_level(logging.WARNING):
            validate_remote_url("https://evil.example.com/data.laz")
        assert "not a known KyFromAbove endpoint" in caplog.text

    def test_validate_s3_uri(self, caplog):
        with caplog.at_level(logging.WARNING):
            validate_remote_url("s3://kyfromabove/tiles/tile.tif")
        assert "not a known KyFromAbove endpoint" not in caplog.text


class TestCheckRemoteSize:
    """HEAD-based size check before full download."""

    def test_check_remote_size_under_limit(self):
        size_100mb = 100 * 1024 * 1024
        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": str(size_100mb)}

        with patch("httpx.head", return_value=mock_resp):
            result = check_remote_size("https://example.com/file.laz")
        assert result == size_100mb

    def test_check_remote_size_over_limit(self):
        size_600mb = 600 * 1024 * 1024
        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": str(size_600mb)}

        with (
            patch("httpx.head", return_value=mock_resp),
            pytest.raises(ValueError, match="exceeds limit"),
        ):
            check_remote_size("https://example.com/file.laz")

    def test_check_remote_size_no_header(self):
        mock_resp = MagicMock()
        mock_resp.headers = {}

        with patch("httpx.head", return_value=mock_resp):
            result = check_remote_size("https://example.com/file.laz")
        assert result is None
