"""Custom exception hierarchy for abovepy.

All abovepy exceptions inherit from AbovepyError so users can
``except AbovepyError`` to catch any library-specific failure.

Exceptions that replace ValueError also inherit from ValueError
for backward compatibility with existing ``except ValueError`` handlers.
"""

from __future__ import annotations


class AbovepyError(Exception):
    """Base exception for all abovepy errors."""


class SearchError(AbovepyError):
    """Raised when a STAC search fails after retries."""


class DownloadError(AbovepyError):
    """Raised when a tile download fails."""


class ReadError(AbovepyError):
    """Raised when reading a raster or point cloud fails."""


class MosaicError(AbovepyError):
    """Raised when mosaicking tiles fails."""


class ProductError(AbovepyError, ValueError):
    """Raised for invalid product keys.

    Inherits ValueError for backward compatibility.
    """


class CountyError(AbovepyError, ValueError):
    """Raised for invalid county names.

    Inherits ValueError for backward compatibility.
    """


class BboxError(AbovepyError, ValueError):
    """Raised for invalid bounding boxes.

    Inherits ValueError for backward compatibility.
    """
