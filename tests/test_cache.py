"""Tests for the TTL cache module."""

import time

from abovepy.utils.cache import TTLCache, make_cache_key


def test_cache_set_and_get():
    cache = TTLCache(maxsize=10, ttl=60)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_cache_miss_returns_none():
    cache = TTLCache(maxsize=10, ttl=60)
    assert cache.get("nonexistent") is None


def test_cache_expiration():
    cache = TTLCache(maxsize=10, ttl=0.05)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    time.sleep(0.1)
    assert cache.get("key1") is None


def test_cache_eviction_on_overflow():
    cache = TTLCache(maxsize=3, ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    cache.set("d", 4)  # Should evict "a"
    assert cache.get("a") is None
    assert cache.get("d") == 4
    assert len(cache) == 3


def test_cache_update_existing_key():
    cache = TTLCache(maxsize=10, ttl=60)
    cache.set("key", "old")
    cache.set("key", "new")
    assert cache.get("key") == "new"
    assert len(cache) == 1


def test_cache_clear():
    cache = TTLCache(maxsize=10, ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None


def test_make_cache_key_deterministic():
    key1 = make_cache_key("dem-phase3", (-84.9, 38.15, -84.8, 38.25))
    key2 = make_cache_key("dem-phase3", (-84.9, 38.15, -84.8, 38.25))
    assert key1 == key2


def test_make_cache_key_different_params():
    key1 = make_cache_key("dem-phase3", (-84.9, 38.15, -84.8, 38.25))
    key2 = make_cache_key("dem-phase2", (-84.9, 38.15, -84.8, 38.25))
    assert key1 != key2


def test_cache_stats_hits_and_misses():
    cache = TTLCache(maxsize=10, ttl=60)
    cache.set("a", 1)
    cache.get("a")  # hit
    cache.get("a")  # hit
    cache.get("b")  # miss
    stats = cache.stats
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["size"] == 1
    assert stats["maxsize"] == 10


def test_cache_stats_reset_on_clear():
    cache = TTLCache(maxsize=10, ttl=60)
    cache.set("a", 1)
    cache.get("a")  # hit
    cache.get("b")  # miss
    cache.clear()
    assert cache.stats["hits"] == 0
    assert cache.stats["misses"] == 0


def test_cache_stats_expired_counts_as_miss():
    cache = TTLCache(maxsize=10, ttl=0.05)
    cache.set("a", 1)
    cache.get("a")  # hit
    time.sleep(0.1)
    cache.get("a")  # miss (expired)
    assert cache.stats["hits"] == 1
    assert cache.stats["misses"] == 1


def test_make_cache_key_with_datetime():
    key1 = make_cache_key("dem-phase3", (-84.9, 38.15, -84.8, 38.25), datetime="2022-01-01/..")
    key2 = make_cache_key("dem-phase3", (-84.9, 38.15, -84.8, 38.25), datetime=None)
    assert key1 != key2
