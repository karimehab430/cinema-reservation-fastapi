from __future__ import annotations

import json
from typing import Any, Protocol

from redis import asyncio as aioredis

from app.core.config import settings


def serialize_model(model: Any) -> dict[str, Any]:
    if model is None:
        return {}
    if isinstance(model, dict):
        return model
    if hasattr(model, "__table__"):
        return {column.name: getattr(model, column.name) for column in model.__table__.columns}
    return model


class CacheBackend(Protocol):
    async def get(self, key: str) -> Any: ...

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def delete_pattern(self, pattern: str) -> None: ...


class RedisCacheBackend:
    def __init__(self, url: str | None = None):
        self.client = aioredis.from_url(url or settings.redis_url, decode_responses=True)

    async def get(self, key: str) -> Any:
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        try:
            payload = json.dumps(value)
            if ttl_seconds is None:
                await self.client.set(key, payload)
            else:
                await self.client.set(key, payload, ex=ttl_seconds)
        except Exception:
            return

    async def delete(self, key: str) -> None:
        try:
            await self.client.delete(key)
        except Exception:
            return

    async def delete_pattern(self, pattern: str) -> None:
        try:
            async for key in self.client.scan_iter(match=f"{pattern}*"):
                await self.client.delete(key)
        except Exception:
            return


class Cache:
    def __init__(self, backend: CacheBackend | None = None, ttl_seconds: int | None = None):
        self.backend = backend or RedisCacheBackend()
        self.ttl_seconds = ttl_seconds

    async def get(self, key: str) -> Any:
        return await self.backend.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        await self.backend.set(key, value, ttl_seconds or self.ttl_seconds)

    async def delete(self, key: str) -> None:
        await self.backend.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        await self.backend.delete_pattern(pattern)
