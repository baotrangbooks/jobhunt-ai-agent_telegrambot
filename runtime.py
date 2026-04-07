"""
Telegram Runtime Context
Cung cấp context cho API calls, rate limiting, caching, và kết nối với core (Tương tự runtime.ts)
"""

import logging
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import functools

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_second: float = 2.0  # Telegram limit
    burst_size: int = 10
    retry_after_header: bool = True


@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    ttl_seconds: int = 3600
    max_items: int = 1000


class TelegramRuntimeContext:
    """
    Runtime context for Telegram API operations
    Manages rate limiting, caching, and error handling
    """

    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        cache_config: Optional[CacheConfig] = None
    ):
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.cache_config = cache_config or CacheConfig()

        # Rate limiter state
        self.request_times: Dict[str, list] = defaultdict(list)  # bucket -> [timestamps]
        self.last_request_time = 0.0

        # Cache
        self.cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)

        # Stats
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.rate_limit_hits = 0

    def wait_for_rate_limit(self, bucket: str = "default") -> float:
        """
        Wait if necessary to respect rate limits
        Returns: delay in seconds
        """
        config = self.rate_limit_config
        request_list = self.request_times[bucket]
        now = time.time()

        # Remove old requests outside the window
        window_start = now - 1.0
        request_list[:] = [t for t in request_list if t > window_start]

        delay = 0.0
        if len(request_list) >= config.burst_size:
            # At rate limit, need to wait
            oldest_request = request_list[0]
            delay = (oldest_request + 1.0) - now
            if delay > 0:
                self.rate_limit_hits += 1
                logger.debug(f"Rate limit reached, waiting {delay:.2f}s")
                time.sleep(delay)

        # Record this request
        request_list.append(now)
        self.request_count += 1
        return delay

    def get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache_config.enabled:
            return None

        if key not in self.cache:
            self.cache_misses += 1
            return None

        value, expiry_time = self.cache[key]
        if time.time() > expiry_time:
            del self.cache[key]
            self.cache_misses += 1
            return None

        self.cache_hits += 1
        return value

    def set_cache(self, key: str, value: Any) -> None:
        """Set value in cache"""
        if not self.cache_config.enabled:
            return

        if len(self.cache) >= self.cache_config.max_items:
            # Remove oldest item (simple FIFO)
            self.cache.pop(next(iter(self.cache)))

        expiry_time = time.time() + self.cache_config.ttl_seconds
        self.cache[key] = (value, expiry_time)

    def clear_cache(self) -> None:
        """Clear all cache"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics"""
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            (self.cache_hits / cache_total * 100) if cache_total > 0 else 0
        )

        return {
            "requests_made": self.request_count,
            "rate_limit_hits": self.rate_limit_hits,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache)
        }

    def reset_stats(self) -> None:
        """Reset all statistics"""
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.rate_limit_hits = 0


class CacheDecorator:
    """Decorator for caching function results"""

    def __init__(self, context: TelegramRuntimeContext, ttl: int = 3600):
        self.context = context
        self.ttl = ttl

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = self.context.get_cache(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            self.context.set_cache(cache_key, result)
            return result

        return wrapper


class RetryConfig:
    """Retry configuration"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 10.0,
        backoff_multiplier: float = 2.0,
        retry_on_errors: Optional[list] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.retry_on_errors = retry_on_errors or [
            "ConnectionError",
            "Timeout",
            "TooManyRequests"
        ]


def retry_with_backoff(config: RetryConfig):
    """
    Decorator for retrying with exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = config.base_delay
            last_error = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_type = type(e).__name__

                    if error_type not in config.retry_on_errors:
                        raise

                    if attempt < config.max_attempts - 1:
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{config.max_attempts} "
                            f"for {func.__name__} after {delay:.2f}s "
                            f"(error: {error_type})"
                        )
                        time.sleep(delay)
                        delay = min(
                            delay * config.backoff_multiplier,
                            config.max_delay
                        )

            if last_error:
                raise last_error

        return wrapper
    return decorator


class TelegramRuntimeManager:
    """Singleton manager for runtime context"""

    _instance: Optional['TelegramRuntimeManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.contexts: Dict[str, TelegramRuntimeContext] = {}
        self.default_context = TelegramRuntimeContext()
        self._initialized = True

    def get_context(self, key: str = "default") -> TelegramRuntimeContext:
        """Get runtime context"""
        if key not in self.contexts:
            self.contexts[key] = TelegramRuntimeContext()
        return self.contexts[key]

    def create_context(
        self,
        key: str,
        rate_limit_config: Optional[RateLimitConfig] = None,
        cache_config: Optional[CacheConfig] = None
    ) -> TelegramRuntimeContext:
        """Create a new context"""
        context = TelegramRuntimeContext(rate_limit_config, cache_config)
        self.contexts[key] = context
        return context

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all contexts"""
        return {
            key: context.get_stats()
            for key, context in self.contexts.items()
        }

    def clear_all_caches(self) -> None:
        """Clear cache in all contexts"""
        for context in self.contexts.values():
            context.clear_cache()


# Global singleton
_runtime_manager: Optional[TelegramRuntimeManager] = None


def get_runtime_manager() -> TelegramRuntimeManager:
    """Get global runtime manager"""
    global _runtime_manager
    if _runtime_manager is None:
        _runtime_manager = TelegramRuntimeManager()
    return _runtime_manager


def get_runtime_context(key: str = "default") -> TelegramRuntimeContext:
    """Get runtime context"""
    return get_runtime_manager().get_context(key)


def cache_result(ttl: int = 3600):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        context = get_runtime_context()
        return CacheDecorator(context, ttl)(func)
    return decorator
