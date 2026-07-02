from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cinema


class CinemaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_cinemas(self, page: int, page_size: int) -> tuple[list[Cinema], int]:
        total = await self.db.scalar(select(func.count()).select_from(Cinema)) or 0
        result = await self.db.execute(
            select(Cinema).offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)
