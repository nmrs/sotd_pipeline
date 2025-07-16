"""
Centralized cache for brush matching operations.

Provides LRU-style eviction, statistics, and debug info.
"""

from collections import OrderedDict
from threading import RLock
from typing import Any, Optional


class MatchCache:
    """
    LRU cache for brush matching operations.
    Thread-safe, with statistics and debug info.
    """

    def __init__(self, max_size: int = 1000, enabled: bool = True):
        self.max_size = max_size
        self.enabled = enabled
        self._cache = OrderedDict()
        self._lock = RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self.hits += 1
                return self._cache[key]
            else:
                self.misses += 1
                return None

    def set(self, key: str, value: Any) -> None:
        if not self.enabled:
            return
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
                self.evictions += 1

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0
            self.evictions = 0

    def stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "enabled": self.enabled,
            }

    def debug_info(self) -> dict:
        with self._lock:
            return {
                "cache_keys": list(self._cache.keys()),
                **self.stats(),
            }
