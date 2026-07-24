import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas import MovieOut, PaginatedResponse
from app.services.movies import MovieService

router = APIRouter(prefix="/api/v1/movies", tags=["movies"])


@router.get("", response_model=PaginatedResponse[MovieOut])
async def list_movies(
    db: AsyncSession = Depends(get_db),
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    sort_by: str = Query("title"),
    order: str = Query("asc"),
):
    service = MovieService(db)
    items, total = await service.list_movies(search, page, page_size, sort_by, order)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(movie_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = MovieService(db)
    return await service.get_movie(movie_id)
