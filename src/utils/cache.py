"""In-memory caching with TTL support"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Single cache entry with metadata"""

    key: str
    value: T
    created_at: float
    expires_at: float
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float:
        """Get remaining TTL in seconds"""
        return max(0, self.expires_at - time.time())


@dataclass
class CacheStats:
    """Cache statistics"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": round(self.hit_rate, 4),
        }


class TTLCache(Generic[T]):
    """
    Thread-safe in-memory cache with TTL support.

    Features:
    - Configurable TTL per entry or default
    - LRU eviction when max size reached
    - Statistics tracking
    - Automatic expired entry cleanup
    """

    def __init__(
        self,
        default_ttl: int = 300,  # 5 minutes
        max_size: int = 1000,
        cleanup_interval: int = 60,
    ):
        """
        Initialize cache.

        Args:
            default_ttl: Default TTL in seconds
            max_size: Maximum number of entries
            cleanup_interval: Interval for automatic cleanup (seconds)
        """
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
        self._stats = CacheStats(max_size=max_size)

    def get(self, key: str) -> Optional[T]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            self._maybe_cleanup()

            entry = self._cache.get(key)
            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.size = len(self._cache)
                return None

            entry.hit_count += 1
            entry.last_accessed = time.time()
            self._stats.hits += 1
            return entry.value

    def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override in seconds
        """
        with self._lock:
            self._maybe_cleanup()

            # Evict if at max size
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_lru()

            ttl_seconds = ttl if ttl is not None else self._default_ttl
            now = time.time()

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + ttl_seconds,
                last_accessed=now,
            )
            self._stats.size = len(self._cache)

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache"""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all entries matching pattern.

        Args:
            pattern: Pattern to match (simple substring match)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            self._stats.size = len(self._cache)
            return len(keys_to_delete)

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self._lock:
            self._stats.size = len(self._cache)
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=self._stats.size,
                max_size=self._stats.max_size,
            )

    def _maybe_cleanup(self) -> None:
        """Cleanup expired entries if interval has passed"""
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = now

    def _cleanup_expired(self) -> None:
        """Remove all expired entries"""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            del self._cache[key]
        self._stats.size = len(self._cache)

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._cache:
            return

        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self._stats.evictions += 1
        self._stats.size = len(self._cache)


class QueryCache:
    """
    Specialized cache for RAG query results.

    Features:
    - Query normalization
    - Semantic-aware key generation
    - Cache invalidation by document
    """

    def __init__(
        self,
        default_ttl: int = 300,
        max_size: int = 500,
    ):
        self._cache = TTLCache[dict](default_ttl=default_ttl, max_size=max_size)

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent caching"""
        # Lowercase and strip whitespace
        normalized = query.lower().strip()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized

    def _generate_key(self, query: str, **kwargs) -> str:
        """Generate cache key from query and parameters"""
        normalized_query = self._normalize_query(query)

        # Include relevant parameters in key
        key_data = {
            "query": normalized_query,
            **{k: v for k, v in sorted(kwargs.items()) if v is not None},
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def get(
        self,
        query: str,
        **kwargs,
    ) -> Optional[dict]:
        """
        Get cached result for query.

        Args:
            query: The query string
            **kwargs: Additional parameters (e.g., session_id, top_k)

        Returns:
            Cached result or None
        """
        key = self._generate_key(query, **kwargs)
        return self._cache.get(key)

    def set(
        self,
        query: str,
        result: dict,
        ttl: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Cache query result.

        Args:
            query: The query string
            result: Result to cache
            ttl: Optional TTL override
            **kwargs: Additional parameters
        """
        key = self._generate_key(query, **kwargs)
        self._cache.set(key, result, ttl)

    def invalidate_query(self, query: str, **kwargs) -> bool:
        """Invalidate specific query cache"""
        key = self._generate_key(query, **kwargs)
        return self._cache.delete(key)

    def invalidate_all(self) -> None:
        """Invalidate all cached queries"""
        self._cache.clear()

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return self._cache.get_stats().to_dict()


def cached(
    cache: TTLCache,
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None,
):
    """
    Decorator for caching function results.

    Args:
        cache: Cache instance to use
        key_func: Optional function to generate cache key from arguments
        ttl: Optional TTL override

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        import asyncio
        from functools import wraps

        def generate_key(*args, **kwargs) -> str:
            if key_func:
                return key_func(*args, **kwargs)

            # Default key generation
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key_string = ":".join(key_parts)
            return hashlib.sha256(key_string.encode()).hexdigest()[:16]

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            key = generate_key(*args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            key = generate_key(*args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Global cache instances
_query_cache: Optional[QueryCache] = None
_embedding_cache: Optional[TTLCache] = None


def get_query_cache() -> QueryCache:
    """Get global query cache instance"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def get_embedding_cache() -> TTLCache:
    """Get global embedding cache instance"""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = TTLCache(default_ttl=3600, max_size=10000)  # 1 hour TTL
    return _embedding_cache


def set_query_cache(cache: QueryCache) -> None:
    """Set global query cache instance"""
    global _query_cache
    _query_cache = cache


def set_embedding_cache(cache: TTLCache) -> None:
    """Set global embedding cache instance"""
    global _embedding_cache
    _embedding_cache = cache
