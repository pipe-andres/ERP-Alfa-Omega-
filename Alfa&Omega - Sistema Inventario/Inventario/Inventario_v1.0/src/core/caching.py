"""Módulo de caching simple in-memory con TTL.
Diseñado para ser plug-and-play: proporciona decoradores y funciones
get/set/clear que los servicios o el repository pueden usar sin alterar
la lógica existente.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional
import time
import threading

_lock = threading.RLock()
_store: Dict[str, tuple[float, Any]] = {}

DEFAULT_TTL = 300  # 5 minutes


def _now() -> float:
    return time.time()


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Store value under key with TTL seconds."""
    expiry = _now() + (ttl if ttl is not None else DEFAULT_TTL)
    with _lock:
        _store[key] = (expiry, value)


def get_cache(key: str) -> Optional[Any]:
    """Return value or None if expired/missing."""
    with _lock:
        data = _store.get(key)
        if not data:
            return None
        expiry, value = data
        if _now() >= expiry:
            del _store[key]
            return None
        return value


def clear_cache(key_prefix: Optional[str] = None) -> None:
    """Clear single key or keys that start with prefix. If prefix is None, clear all."""
    with _lock:
        if key_prefix is None:
            _store.clear()
            return
        keys = [k for k in _store.keys() if k.startswith(key_prefix)]
        for k in keys:
            del _store[k]


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
            res = get_cache(key)
            if res is not None:
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
