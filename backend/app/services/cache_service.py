import logging
from typing import Any

import orjson
from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache wrapper with safe degradation."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Redis | None = None

    async def connect(self) -> None:
        try:
            self._client = Redis.from_url(self._settings.redis_url, encoding="utf-8", decode_responses=False)
            await self._client.ping()
        except Exception as exc:  # pragma: no cover - defensive runtime fallback
            logger.warning("Redis unavailable, continuing without cache: %s", exc)
            self._client = None

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_json(self, key: str) -> dict[str, Any] | None:
        if self._client is None:
            return None
        raw_value = await self._client.get(key)
        if not raw_value:
            return None
        return orjson.loads(raw_value)

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
        if self._client is None:
            return
        await self._client.set(
            key,
            orjson.dumps(value),
            ex=ttl_seconds or self._settings.cache_ttl_seconds,
        )
