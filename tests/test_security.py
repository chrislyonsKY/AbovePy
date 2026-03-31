"""Tests for security utilities — URL validation, input sanitization, and remote read guards."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from abovepy._security import (
    check_remote_size,
    sanitize_filename,
    validate_image_format,
    validate_path_segment,
    validate_remote_url,
    validate_s3_bucket,
)


class TestValidateRemoteUrl:
    """URL validation raises for untrusted hosts."""

    def test_validate_trusted_url(self):
        # Should not raise
        validate_remote_url("https://kyfromabove.s3.amazonaws.com/tiles/tile.tif")

    def test_validate_untrusted_url_raises(self):
        with pytest.raises(ValueError, match="not a known KyFromAbove endpoint"):
            validate_remote_url("https://evil.example.com/data.laz")

    def test_validate_s3_uri(self):
        # S3 URIs are allowed (converted to HTTPS internally)
        validate_remote_url("s3://kyfromabove/tiles/tile.tif")

    def test_allow_untrusted_warns_instead(self, caplog):
        with caplog.at_level(logging.WARNING):
            validate_remote_url("https://evil.example.com/data.laz", allow_untrusted=True)
        assert "not a known KyFromAbove endpoint" in caplog.text

    def test_execute_api_trusted(self):
        validate_remote_url("https://spved5ihrl.execute-api.us-west-2.amazonaws.com/cog/info")

    def test_url_with_path_and_query(self):
        validate_remote_url("https://kyfromabove.s3.amazonaws.com/tiles/dem/tile.tif?v=2")


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

    def test_check_remote_size_custom_limit(self):
        size_50mb = 50 * 1024 * 1024
        mock_resp = MagicMock()
        mock_resp.headers = {"content-length": str(size_50mb)}

        with (
            patch("httpx.head", return_value=mock_resp),
            pytest.raises(ValueError, match="exceeds limit"),
        ):
            check_remote_size("https://example.com/file.laz", max_size_mb=25)

    def test_check_remote_size_http_error_returns_none(self):
        import httpx

        with patch("httpx.head", side_effect=httpx.ConnectError("timeout")):
            result = check_remote_size("https://example.com/file.laz")
        assert result is None


# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    def test_normal_url(self):
        assert sanitize_filename("https://s3.amazonaws.com/bucket/tile.tif") == "tile.tif"

    def test_url_with_query(self):
        result = sanitize_filename("https://example.com/tile.tif?v=2&token=abc")
        assert result == "tile.tif"

    def test_path_traversal_stripped(self):
        result = sanitize_filename("https://example.com/../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result
        assert ".." not in result

    def test_url_encoded_traversal(self):
        result = sanitize_filename("https://example.com/payload%2F..%2F..%2Fetc%2Fpasswd.tif")
        assert "/" not in result
        assert "\\" not in result

    def test_leading_dots_stripped(self):
        result = sanitize_filename("https://example.com/.hidden")
        assert not result.startswith(".")

    def test_empty_filename_raises(self):
        with pytest.raises(ValueError, match="Cannot extract safe filename"):
            sanitize_filename("https://example.com/")


class TestValidatePathSegment:
    def test_valid_segment(self):
        assert validate_path_segment("dem-phase3") == "dem-phase3"

    def test_valid_with_dots(self):
        assert validate_path_segment("tile.v2") == "tile.v2"

    def test_path_traversal_rejected(self):
        with pytest.raises(ValueError, match="path traversal"):
            validate_path_segment("../../../etc")

    def test_slash_rejected(self):
        with pytest.raises(ValueError, match="path traversal"):
            validate_path_segment("dem/phase3")

    def test_backslash_rejected(self):
        with pytest.raises(ValueError, match="path traversal"):
            validate_path_segment("dem\\phase3")

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_path_segment("")

    def test_special_chars_rejected(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_path_segment("tile;drop table")

    def test_leading_dot_rejected(self):
        with pytest.raises(ValueError, match="unsafe characters"):
            validate_path_segment(".hidden")


class TestValidateImageFormat:
    def test_valid_formats(self):
        for fmt in ("png", "jpeg", "jpg", "tif", "tiff", "webp", "npy"):
            assert validate_image_format(fmt) == fmt

    def test_invalid_format_rejected(self):
        with pytest.raises(ValueError, match="Invalid image format"):
            validate_image_format("exe")

    def test_path_traversal_in_format_rejected(self):
        with pytest.raises(ValueError, match="Invalid image format"):
            validate_image_format("png/../admin")

    def test_query_injection_in_format_rejected(self):
        with pytest.raises(ValueError, match="Invalid image format"):
            validate_image_format("png?foo=bar")


class TestValidateS3Bucket:
    def test_valid_bucket(self):
        assert validate_s3_bucket("kyfromabove") == "kyfromabove"

    def test_valid_bucket_with_dots(self):
        assert validate_s3_bucket("my.bucket.name") == "my.bucket.name"

    def test_valid_bucket_with_hyphens(self):
        assert validate_s3_bucket("my-bucket-name") == "my-bucket-name"

    def test_double_dots_rejected(self):
        with pytest.raises(ValueError, match="Suspicious"):
            validate_s3_bucket("bucket..evil")

    def test_too_short_rejected(self):
        with pytest.raises(ValueError, match="Invalid S3 bucket"):
            validate_s3_bucket("ab")

    def test_uppercase_rejected(self):
        with pytest.raises(ValueError, match="Invalid S3 bucket"):
            validate_s3_bucket("MyBucket")

    def test_ip_address_rejected(self):
        with pytest.raises(ValueError, match="Suspicious"):
            validate_s3_bucket("192.168.1.1")
