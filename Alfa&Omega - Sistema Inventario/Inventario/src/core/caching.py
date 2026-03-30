"""Módulo de caching simple in-memory con TTL.
Diseñado para ser plug-and-play: proporciona decoradores y funciones
get/set/clear que los servicios o el repository pueden usar sin alterar
la lógica existente.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional
import time
import threading
from collections import OrderedDict
from logging import getLogger

from config import settings

_lock = threading.RLock()
# store maintains insertion order; we will treat end as most-recently-used
_store: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()

# estadísticas internas
_hits = 0
_misses = 0
_evictions = 0
_ops = 0
_LOGGER = getLogger(__name__)

# valores configurables desde settings, con defaults conservadores
DEFAULT_TTL = getattr(settings, "CACHE_DEFAULT_TTL", 15)
MAXSIZE = getattr(settings, "CACHE_MAXSIZE", 256)

_SENTINEL = object()  # valor centinela para distinguir None válido de cache miss


def _now() -> float:
    return time.time()


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Store value under key with TTL seconds and enforce maxsize (LRU).

    If the cache is full, evict the least-recently-used entry. Stats are
    updated and logged periodically.
    """
    global _evictions, _ops
    expiry = _now() + (ttl if ttl is not None else DEFAULT_TTL)
    with _lock:
        # overwrite existing key to update its position
        if key in _store:
            del _store[key]
        _store[key] = (expiry, value)
        _ops += 1
        if len(_store) > MAXSIZE:
            evicted_key, _ = _store.popitem(last=False)
            _evictions += 1
        if _ops % 100 == 0:
            _LOGGER.debug("Cache stats %s", get_stats())


def get_cache(key: str) -> Any:
    """Return value or _SENTINEL if expired/missing.

    Access updates LRU order and statistics.
    """
    global _hits, _misses, _ops
    with _lock:
        data = _store.get(key)
        if not data:
            _misses += 1
            _ops += 1
            if _ops % 100 == 0:
                _LOGGER.debug("Cache stats %s", get_stats())
            return _SENTINEL
        expiry, value = data
        if _now() >= expiry:
            del _store[key]
            _misses += 1
            _ops += 1
            if _ops % 100 == 0:
                _LOGGER.debug("Cache stats %s", get_stats())
            return _SENTINEL
        # hit
        _hits += 1
        _ops += 1
        # move to end to mark as recently used
        _store.move_to_end(key)
        if _ops % 100 == 0:
            _LOGGER.debug("Cache stats %s", get_stats())
        return value


def clear_cache(key_prefix: Optional[str] = None) -> None:
    """Clear single key or keys that start with prefix. If prefix is None, clear all.

    This is identical to :func:`invalidate_prefix` but kept for backwards
    compatibility with existing callers.
    """
    with _lock:
        if key_prefix is None:
            _store.clear()
            return
        keys = [k for k in _store.keys() if k.startswith(key_prefix)]
        for k in keys:
            del _store[k]


def invalidate_all() -> None:
    """Limpia todo el caché de una vez. Útil tras operaciones masivas."""
    clear_cache(None)


def invalidate_prefix(prefix: str) -> None:
    """Invalidate every key that starts with ``prefix``.

    Ejemplo: ``invalidate_prefix("products")`` borra ``"products:foo"`` y
    ``"products:bar"``. Esta función facilita la eliminación por grupos en
    lugar de tener que calcular manualmente cada clave.
    """
    clear_cache(prefix)


def get_stats() -> Dict[str, int]:
    """Return cache statistics (hits, misses, evictions, current size)."""
    with _lock:
        return {"hits": _hits, "misses": _misses, "evictions": _evictions, "size": len(_store)}


def cached(ttl: Optional[int] = None, key_builder: Optional[Callable[..., str]] = None):
    """Decorator to cache function results using a key_builder or default key.
    Default key: module.func:args:kwargs
    """
    def decorator(fn: Callable):
        def wrapper(*args, **kwargs):
            key = None
            if key_builder:
                try:
                    key = key_builder(*args, **kwargs)
                except Exception:
                    key = f"{fn.__module__}.{fn.__name__}:{args}:{kwargs}"
            else:
                key = f"{fn.__module__}.{fn.__name__}:{args}:{kwargs}"

            # FIX: usar _SENTINEL para distinguir None válido de cache miss
            res = get_cache(key)
            if res is not _SENTINEL:
                return res

            res = fn(*args, **kwargs)
            try:
                set_cache(key, res, ttl)
            except Exception:
                pass
            return res
        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper
    return decorator