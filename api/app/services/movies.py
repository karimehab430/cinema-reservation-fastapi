from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models import Movie


class MovieService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_movies(
        self,
        search: str | None,
        page: int,
        page_size: int,
        sort_by: str,
        order: str,
    ) -> tuple[list[Movie], int]:
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
        return list(result.scalars().all()), int(total)

    async def get_movie(self, movie_id) -> Movie:
        movie = await self.db.get(Movie, movie_id)
        if movie is None:
            raise NotFoundError("Movie not found")
        return movie
