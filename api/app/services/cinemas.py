from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import Cache, serialize_model
from app.models import Cinema
from app.schemas import CinemaCreate


class CinemaService:
    def __init__(self, db: AsyncSession | None, cache: Cache | None = None):
        self.db = db
        self.cache = cache or Cache()

    async def list_cinemas(self, page: int, page_size: int) -> tuple[list[Cinema], int]:
        cache_key = f"cinemas:list:{page}:{page_size}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return [Cinema(**item) for item in cached["items"]], int(cached["total"])

        if self.db is None:
            raise ValueError("Database session is required")

        total = await self.db.scalar(select(func.count()).select_from(Cinema)) or 0
        result = await self.db.execute(
            select(Cinema).offset((page - 1) * page_size).limit(page_size)
        )
        items = list(result.scalars().all())
        payload = {"items": [serialize_model(item) for item in items], "total": int(total or 0)}
        await self.cache.set(cache_key, payload, ttl_seconds=300)
        return items, int(total or 0)

    async def create_cinema(self, payload: CinemaCreate) -> Cinema:
        if self.db is None:
            raise ValueError("Database session is required")

        cinema = Cinema(name=payload.name, location=payload.location)
        self.db.add(cinema)
        await self.db.commit()
        await self.db.refresh(cinema)
        await self.cache.delete_pattern("cinemas:list:")
        return cinema
