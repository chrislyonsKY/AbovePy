"""Security utilities — URL validation, input sanitization, and remote read guards."""

from __future__ import annotations

import logging
import re

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

# Safe patterns for values that appear in URL paths or filesystem paths
_SAFE_PATH_SEGMENT = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._\-]*$")

# S3 bucket name rules: 3-63 chars, lowercase alphanumeric, hyphens, dots
_S3_BUCKET_NAME = re.compile(r"^[a-z0-9][a-z0-9.\-]{1,61}[a-z0-9]$")

# Allowed image formats for TiTiler URL builders
ALLOWED_IMAGE_FORMATS = frozenset({"png", "jpeg", "jpg", "tif", "tiff", "webp", "npy"})


def validate_remote_url(url: str, *, allow_untrusted: bool = False) -> None:
    """Validate a remote URL against known KyFromAbove hosts.

    Parameters
    ----------
    url : str
        The remote URL to check.
    allow_untrusted : bool
        If True, only log a warning for untrusted hosts instead of raising.

    Raises
    ------
    ValueError
        If the host is not trusted and ``allow_untrusted`` is False.
    """
    if url.startswith("s3://"):
        return  # S3 URIs are converted to HTTPS internally
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = parsed.hostname or ""
    if not any(host == h or host.endswith("." + h) for h in TRUSTED_HOSTS):
        if allow_untrusted:
            logger.warning(
                "URL host '%s' is not a known KyFromAbove endpoint.",
                host,
            )
        else:
            raise ValueError(
                f"URL host '{host}' is not a known KyFromAbove endpoint. "
                f"Pass allow_untrusted=True to allow requests to other hosts."
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


# ---------------------------------------------------------------------------
# Input sanitization for paths and URLs
# ---------------------------------------------------------------------------


def sanitize_filename(url: str) -> str:
    """Extract and sanitize a filename from a URL.

    Strips path traversal sequences, query strings, and unsafe characters
    to produce a safe filename for local storage.

    Parameters
    ----------
    url : str
        Source URL.

    Returns
    -------
    str
        Safe filename.

    Raises
    ------
    ValueError
        If no safe filename can be extracted.
    """
    from urllib.parse import unquote, urlparse

    parsed = urlparse(url)
    # Extract the last path component after URL-decoding
    path = unquote(parsed.path)
    filename = path.rsplit("/", maxsplit=1)[-1] if "/" in path else path

    # Strip any remaining path separators
    filename = filename.replace("\\", "_").replace("/", "_")

    # Remove leading dots (hidden files / traversal)
    filename = filename.lstrip(".")

    # Collapse to safe characters only
    filename = re.sub(r"[^\w.\-]", "_", filename)

    if not filename or filename in (".", ".."):
        raise ValueError(f"Cannot extract safe filename from URL: {url}")

    return filename


def validate_path_segment(value: str, name: str = "value") -> str:
    """Validate a string is safe for use in URL paths or filesystem paths.

    Rejects path traversal sequences, slashes, and other unsafe characters.

    Parameters
    ----------
    value : str
        The string to validate.
    name : str
        Human-readable name for error messages.

    Returns
    -------
    str
        The validated string (unchanged).

    Raises
    ------
    ValueError
        If the string contains unsafe characters.
    """
    if not value:
        raise ValueError(f"{name} must not be empty")
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"{name} contains path traversal characters: {value!r}")
    if not _SAFE_PATH_SEGMENT.match(value):
        raise ValueError(
            f"{name} contains unsafe characters: {value!r}. "
            f"Only alphanumerics, dots, hyphens, and underscores are allowed."
        )
    return value


def validate_image_format(fmt: str) -> str:
    """Validate an image format string for TiTiler URL construction.

    Parameters
    ----------
    fmt : str
        Image format (e.g., ``"png"``, ``"jpeg"``, ``"tif"``).

    Returns
    -------
    str
        The validated format string.

    Raises
    ------
    ValueError
        If the format is not in the allowlist.
    """
    if fmt not in ALLOWED_IMAGE_FORMATS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_FORMATS))
        raise ValueError(f"Invalid image format {fmt!r}. Allowed: {allowed}")
    return fmt


def validate_s3_bucket(bucket: str) -> str:
    """Validate an S3 bucket name.

    Parameters
    ----------
    bucket : str
        S3 bucket name.

    Returns
    -------
    str
        The validated bucket name.

    Raises
    ------
    ValueError
        If the bucket name is invalid.
    """
    if not _S3_BUCKET_NAME.match(bucket):
        raise ValueError(f"Invalid S3 bucket name: {bucket!r}")
    # Reject IP-address-style names and consecutive dots
    if ".." in bucket or (bucket[0].isdigit() and bucket.count(".") == 3):
        raise ValueError(f"Suspicious S3 bucket name: {bucket!r}")
    return bucket
