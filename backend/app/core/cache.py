"""SignalFlow 后端 - Redis 缓存封装。

设计原则：
1. 异常安全：Redis 不可用时降级为无缓存，不阻塞主业务。
2. 统一序列化：支持 JSON 自动编码/解码。
3. 可复用：Service 层通过 `cache` 实例直接调用 get / set / delete / expire。
4. 连接复用：单例 Redis 客户端，生命周期与 FastAPI 应用绑定。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


try:
    import redis.asyncio as aioredis
    _REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    aioredis = None  # type: ignore[assignment]
    _REDIS_AVAILABLE = False


class CacheClient:
    """Redis 缓存客户端（异常安全降级）。"""

    def __init__(self, url: str | None = None) -> None:
        self._url = url or settings.redis_url
        self._client: Any = None
        self._healthy = False

    async def connect(self) -> None:
        """建立连接。应在应用启动事件（lifespan）中调用。"""
        if not _REDIS_AVAILABLE:
            logger.warning("redis 包未安装，缓存功能不可用")
            return
        try:
            self._client = aioredis.from_url(self._url, decode_responses=True)
            await self._client.ping()
            self._healthy = True
            logger.info("Redis 缓存连接成功")
        except Exception:
            logger.warning("Redis 连接失败，缓存降级为无缓存模式", exc_info=True)
            self._healthy = False

    async def disconnect(self) -> None:
        """关闭连接。应在应用关闭事件（lifespan）中调用。"""
        if self._client is not None:
            await self._client.close()
            self._healthy = False

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Any | None:
        """获取缓存值（JSON 反序列化）。"""
        if not self._healthy or self._client is None:
            return None
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.debug("Cache get error for key %s", key, exc_info=True)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        *,
        expire_seconds: int | None = None,
    ) -> bool:
        """写入缓存值（JSON 序列化）。"""
        if not self._healthy or self._client is None:
            return False
        try:
            raw = json.dumps(value, ensure_ascii=False, default=str)
            if expire_seconds:
                await self._client.setex(key, expire_seconds, raw)
            else:
                await self._client.set(key, raw)
            return True
        except Exception:
            logger.debug("Cache set error for key %s", key, exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存键。"""
        if not self._healthy or self._client is None:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception:
            logger.debug("Cache delete error for key %s", key, exc_info=True)
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间。"""
        if not self._healthy or self._client is None:
            return False
        try:
            await self._client.expire(key, seconds)
            return True
        except Exception:
            logger.debug("Cache expire error for key %s", key, exc_info=True)
            return False

    async def clear_prefix(self, prefix: str) -> int:
        """按前缀批量删除（用于缓存失效）。返回删除数量。"""
        if not self._healthy or self._client is None:
            return 0
        try:
            keys = []
            async for key in self._client.scan_iter(match=f"{prefix}*"):
                keys.append(key)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception:
            logger.debug("Cache clear_prefix error for %s", prefix, exc_info=True)
            return 0


# 单例（生命周期由 lifespan 事件管理）
cache = CacheClient()
