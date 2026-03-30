import threading
import time
import pytest

from src.core import caching


@pytest.fixture(autouse=True)
def clear_between_tests():
    # ensure fresh cache for each test
    caching.invalidate_all()
    # reset stats by directly manipulating internal counters
    # (tests allowed to reach inside because it's private)
    caching._hits = 0
    caching._misses = 0
    caching._evictions = 0
    caching._ops = 0
    yield
    caching.invalidate_all()


def test_lru_eviction(monkeypatch):
    # force a small cache size
    monkeypatch.setattr(caching, "MAXSIZE", 3)
    caching.set_cache("a", 1)
    caching.set_cache("b", 2)
    caching.set_cache("c", 3)
    # access "a" to mark it as recently used
    assert caching.get_cache("a") == 1
    # insert fourth element -> should evict "b" (LRU)
    caching.set_cache("d", 4)
    assert caching.get_cache("b") is caching._SENTINEL
    assert caching.get_cache("a") == 1
    assert caching.get_cache("c") == 3
    assert caching.get_cache("d") == 4


def test_thread_safety():
    def worker(idx: int):
        for j in range(100):
            key = f"t{idx}:{j}"
            caching.set_cache(key, j)
            assert caching.get_cache(key) == j

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def test_invalidate_prefix():
    caching.set_cache("foo:1", 1)
    caching.set_cache("foo:2", 2)
    caching.set_cache("bar:3", 3)
    caching.invalidate_prefix("foo:")
    assert caching.get_cache("foo:1") is caching._SENTINEL
    assert caching.get_cache("foo:2") is caching._SENTINEL
    assert caching.get_cache("bar:3") == 3


def test_ttl_expiry():
    caching.set_cache("x", "y", ttl=1)
    assert caching.get_cache("x") == "y"
    time.sleep(1.05)
    assert caching.get_cache("x") is caching._SENTINEL


def test_stats():
    # initially empty
    assert caching.get_stats() == {"hits": 0, "misses": 0, "evictions": 0, "size": 0}
    # cache a value and hit it
    caching.set_cache("k", 10)
    assert caching.get_cache("k") == 10
    # miss on another key
    assert caching.get_cache("nope") is caching._SENTINEL
    stats = caching.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["evictions"] == 0
    assert stats["size"] == 1
