"""
Redis 连接管理模块
用于进度追踪等需要实时状态存储的场景
"""

import redis.asyncio as redis
from typing import Optional

from app.config import settings


_redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """
    初始化 Redis 连接
    
    在应用启动时调用
    """
    global _redis_client
    if settings.REDIS_URL:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        # 测试连接
        await _redis_client.ping()
        print(f"✅ Redis连接已初始化: {settings.REDIS_URL}")


async def close_redis() -> None:
    """
    关闭 Redis 连接
    
    在应用关闭时调用
    """
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        print("🛑 Redis连接已关闭")


def get_redis() -> Optional[redis.Redis]:
    """
    获取 Redis 客户端实例
    
    Returns:
        Redis 客户端实例，如果未初始化则返回 None
    """
    return _redis_client

