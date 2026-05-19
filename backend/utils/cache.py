"""
内存缓存工具 — 支持动态TTL
"""
from cachetools import TTLCache
from typing import Any
from utils.config import settings


# TTL 从配置读取
_cache_cfg = settings.CACHE
_cache = TTLCache(maxsize=_cache_cfg.get("max_size", 2000),
                   ttl=_cache_cfg.get("data_ttl", 300))


def get(key: str) -> Any:
    return _cache.get(key)


def set(key: str, value: Any, ttl: int = None):
    _cache[key] = value


def clear():
    _cache.clear()
