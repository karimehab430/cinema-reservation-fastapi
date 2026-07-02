from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import Cache, serialize_model
from app.exceptions import NotFoundError
from app.models import Movie


class MovieService:
    def __init__(self, db: AsyncSession | None, cache: Cache | None = None):
        self.db = db
        self.cache = cache or Cache()

    async def list_movies(
        self,
        search: str | None,
        page: int,
        page_size: int,
        sort_by: str,
        order: str,
    ) -> tuple[list[Movie], int]:
        cache_key = f"movies:list:{search or ''}:{page}:{page_size}:{sort_by}:{order}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return [Movie(**item) for item in cached["items"]], int(cached["total"])

        if self.db is None:
            raise ValueError("Database session is required")

        stmt = select(Movie)
        if search:
            stmt = stmt.where(Movie.title.ilike(f"%{search}%"))

        sort_column = {
            "title": Movie.title,
            "duration": Movie.duration_minutes,
            "created": Movie.id,
        }.get(sort_by, Movie.title)
        if order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        payload = {"items": [serialize_model(item) for item in items], "total": int(total)}
        await self.cache.set(cache_key, payload, ttl_seconds=300)
        return items, int(total)

    async def get_movie(self, movie_id) -> Movie:
        cache_key = f"movies:detail:{movie_id}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return Movie(**cached)

        if self.db is None:
            raise ValueError("Database session is required")

        movie = await self.db.get(Movie, movie_id)
        if movie is None:
            raise NotFoundError("Movie not found")
        await self.cache.set(cache_key, serialize_model(movie), ttl_seconds=300)
        return movie
