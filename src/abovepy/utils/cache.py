"""TTL-based LRU cache for STAC responses to avoid redundant API calls.

Caches search results in-memory for the session lifetime.
Default TTL is 5 minutes — long enough to avoid duplicate queries in
a notebook workflow, short enough to pick up catalog updates.
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# Default cache TTL in seconds
DEFAULT_TTL = 300  # 5 minutes
DEFAULT_MAXSIZE = 128


class TTLCache:
    """Simple in-memory cache with per-entry TTL expiration.

    Parameters
    ----------
    maxsize : int
        Maximum number of cached entries. Oldest evicted on overflow.
    ttl : float
        Time-to-live in seconds for each entry.
    """

    def __init__(self, maxsize: int = DEFAULT_MAXSIZE, ttl: float = DEFAULT_TTL) -> None:
        self._maxsize = maxsize
        self._ttl = ttl
        self._cache: dict[str, tuple[float, Any]] = {}
        self._order: deque[str] = deque()

    def get(self, key: str) -> Any | None:
        """Get a cached value if it exists and hasn't expired.

        Parameters
        ----------
        key : str
            Cache key.

        Returns
        -------
        Any or None
            Cached value, or None if missing/expired.
        """
        if key not in self._cache:
            return None

        ts, value = self._cache[key]
        if time.monotonic() - ts > self._ttl:
            self._evict(key)
            logger.debug("Cache expired: %s", key[:32])
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache.

        Parameters
        ----------
        key : str
            Cache key.
        value : Any
            Value to cache.
        """
        if key in self._cache:
            self._cache[key] = (time.monotonic(), value)
            return

        while len(self._cache) >= self._maxsize:
            oldest = self._order.popleft()
            self._cache.pop(oldest, None)
            logger.debug("Cache evicted: %s", oldest[:32])

        self._cache[key] = (time.monotonic(), value)
        self._order.append(key)

    def _evict(self, key: str) -> None:
        """Remove a single entry."""
        self._cache.pop(key, None)
        with contextlib.suppress(ValueError):
            self._order.remove(key)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._order.clear()

    def __len__(self) -> int:
        return len(self._cache)


def make_cache_key(
    collection_id: str,
    bbox: tuple[float, float, float, float],
    datetime: str | None = None,
    max_items: int = 500,
) -> str:
    """Build a deterministic cache key from search parameters.

    Parameters
    ----------
    collection_id : str
        STAC collection ID.
    bbox : tuple
        Bounding box.
    datetime : str, optional
        Datetime filter.
    max_items : int
        Max items limit.

    Returns
    -------
    str
        Hex digest cache key.
    """
    raw = "{}|{}|{}|{}".format(
        collection_id,
        ",".join(f"{v:.6f}" for v in bbox),
        datetime or "",
        max_items,
    )
    return hashlib.sha256(raw.encode()).hexdigest()
