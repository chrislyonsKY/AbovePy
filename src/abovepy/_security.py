"""Security utilities — URL validation and remote read guards."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Trusted host patterns for remote reads
TRUSTED_HOSTS = (
    "kyfromabove.s3.amazonaws.com",
    "kyfromabove.s3.us-west-2.amazonaws.com",
    "s3.us-west-2.amazonaws.com",
    "spved5ihrl.execute-api.us-west-2.amazonaws.com",
    "6hp4guqpwe.execute-api.us-west-2.amazonaws.com",
    "vdo05uew72.execute-api.us-west-2.amazonaws.com",
)

# Default max file size for full in-memory remote reads (MB)
DEFAULT_MAX_REMOTE_SIZE_MB = 500


def validate_remote_url(url: str, *, allow_untrusted: bool = False) -> None:
    """Warn if a URL is not from a known KyFromAbove host.

    Parameters
    ----------
    url : str
        The remote URL to check.
    allow_untrusted : bool
        If False (default), log a warning for untrusted hosts.
    """
    if url.startswith("s3://"):
        return  # S3 URIs are converted to HTTPS internally
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not any(host == h or host.endswith("." + h) for h in TRUSTED_HOSTS) and not allow_untrusted:
        logger.warning(
            "URL host '%s' is not a known KyFromAbove endpoint. "
            "Set allow_untrusted=True to suppress this warning.",
            host,
        )


def check_remote_size(url: str, max_size_mb: float = DEFAULT_MAX_REMOTE_SIZE_MB) -> int | None:
    """HEAD request to check Content-Length before full download.

    Returns the size in bytes, or None if unavailable.
    Raises ValueError if size exceeds max_size_mb.
    """
    import httpx

    try:
        resp = httpx.head(url, timeout=10, follow_redirects=True)
        content_length = resp.headers.get("content-length")
        if content_length is not None:
            size_bytes = int(content_length)
            size_mb = size_bytes / (1024 * 1024)
            if size_mb > max_size_mb:
                raise ValueError(
                    f"Remote file is {size_mb:.0f} MB, exceeds limit of {max_size_mb:.0f} MB. "
                    f"Use read_copc() for spatial queries or download the file first."
                )
            return size_bytes
    except httpx.HTTPError:
        logger.debug("HEAD request failed for %s, skipping size check", url)
    return None
