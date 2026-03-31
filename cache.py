"""
utils/cache.py
--------------
Thin Redis caching layer using flask-caching.

Usage:
  from utils.cache import cache, cached_response, invalidate

  @cached_response("drives:approved", ttl=300)
  def list_drives(): ...

  invalidate("drives:*")   # wipe a pattern
"""

import json
import logging
import hashlib
from functools import wraps
from flask import request
import redis as _redis
from config import Config

logger = logging.getLogger(__name__)

# ── Raw Redis client (used for pattern-based invalidation) ────────────────────
try:
    _r = _redis.from_url(Config.REDIS_URL, decode_responses=True)
    _r.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connected: %s", Config.REDIS_URL)
except Exception as e:
    _r = None
    REDIS_AVAILABLE = False
    logger.warning("Redis unavailable — caching disabled. %s", e)


# ── TTL presets (seconds) ─────────────────────────────────────────────────────
TTL = {
    "short":   60,        # 1 min   — dashboard stats
    "medium":  300,       # 5 min   — drive/company listings
    "long":    900,       # 15 min  — static-ish data
    "session": 3600,      # 1 hour  — user profile snapshots
}


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _get(key: str):
    if not REDIS_AVAILABLE:
        return None
    try:
        raw = _r.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.debug("Cache GET error (%s): %s", key, e)
        return None


def _set(key: str, value, ttl: int):
    if not REDIS_AVAILABLE:
        return
    try:
        _r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.debug("Cache SET error (%s): %s", key, e)


def _delete(key: str):
    if not REDIS_AVAILABLE:
        return
    try:
        _r.delete(key)
    except Exception as e:
        logger.debug("Cache DEL error (%s): %s", key, e)


def invalidate_pattern(pattern: str):
    """Delete all keys matching a glob pattern (e.g. 'drives:*')."""
    if not REDIS_AVAILABLE:
        return
    try:
        keys = _r.keys(f"ppa:{pattern}")
        if keys:
            _r.delete(*keys)
            logger.debug("Cache invalidated %d keys for pattern '%s'", len(keys), pattern)
    except Exception as e:
        logger.debug("Cache INVALIDATE error (%s): %s", pattern, e)


def invalidate(*patterns: str):
    """Invalidate one or more patterns."""
    for p in patterns:
        invalidate_pattern(p)


def cache_stats() -> dict:
    """Return basic Redis info for the admin health endpoint."""
    if not REDIS_AVAILABLE:
        return {"available": False}
    try:
        info = _r.info("memory")
        keys = _r.dbsize()
        return {
            "available":       True,
            "total_keys":      keys,
            "used_memory_mb":  round(info.get("used_memory", 0) / 1024 / 1024, 2),
            "peak_memory_mb":  round(info.get("used_memory_peak", 0) / 1024 / 1024, 2),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


# ── Decorator ─────────────────────────────────────────────────────────────────

def cached_response(key_prefix: str, ttl: int = TTL["medium"],
                    vary_on_args: bool = False,
                    vary_on_query: bool = True):
    """
    Decorator for Flask route functions.

    Parameters
    ----------
    key_prefix   : str   — base cache key (e.g. "drives:approved")
    ttl          : int   — seconds to keep the cached value
    vary_on_args : bool  — include positional route args in the key
    vary_on_query: bool  — include query-string params in the key

    The decorator short-circuits and returns the cached JSON response
    when a hit is found; otherwise it calls the real function, caches
    the result, and returns it.

    Works with functions that return either:
      • a plain dict / list  (will be jsonified)
      • a (response, status_code) tuple
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Build cache key
            key_parts = [key_prefix]
            if vary_on_args and (args or kwargs):
                sig = json.dumps(
                    {"args": list(args), "kwargs": kwargs},
                    sort_keys=True, default=str)
                key_parts.append(hashlib.md5(sig.encode()).hexdigest()[:8])
            if vary_on_query and request.args:
                qs = json.dumps(dict(sorted(request.args.items())),
                                sort_keys=True)
                key_parts.append(hashlib.md5(qs.encode()).hexdigest()[:8])

            cache_key = "ppa:" + ":".join(key_parts)

            # Cache HIT
            cached = _get(cache_key)
            if cached is not None:
                from flask import jsonify
                logger.debug("Cache HIT  %s", cache_key)
                if isinstance(cached, dict) and "__status__" in cached:
                    return jsonify(cached["__data__"]), cached["__status__"]
                return jsonify(cached)

            # Cache MISS — call real function
            logger.debug("Cache MISS %s", cache_key)
            result = fn(*args, **kwargs)

            # Normalise result for storage
            if isinstance(result, tuple):
                response_obj, status = result
                # Extract JSON-able data from Flask Response
                try:
                    data = response_obj.get_json()
                except Exception:
                    data = result
                _set(cache_key, {"__data__": data, "__status__": status}, ttl)
            else:
                _set(cache_key, result, ttl)

            return result

        return wrapper
    return decorator
