"""
内存缓存工具 - LRU缓存，减少akshare重复请求
"""
from cachetools import TTLCache
from typing import Any


# 全局缓存实例
cache = TTLCache(maxsize=1000, ttl=900)  # 最多1000条，15分钟过期


def get(key: str) -> Any:
    """获取缓存"""
    return cache.get(key)


def set(key: str, value: Any, ttl: int = 900):
    """设置缓存"""
    cache[key] = value


def clear():
    """清空缓存"""
    cache.clear()
