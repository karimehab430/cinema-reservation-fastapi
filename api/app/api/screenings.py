import uuid
from datetime import date

from fastapi import APIRouter, Query

from app.dependencies import DbSession
from app.schemas import PaginatedResponse, ScreeningOut, SeatOut
from app.services.screenings import ScreeningService

router = APIRouter(prefix="/api/v1/screenings", tags=["screenings"])


@router.get("", response_model=PaginatedResponse[ScreeningOut])
async def list_screenings(
    db: DbSession,
    movie_id: uuid.UUID | None = None,
    cinema_id: uuid.UUID | None = None,
    on_date: date | None = Query(None, alias="date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    sort_by: str = Query("date"),
    order: str = Query("asc"),
):
    service = ScreeningService(db)
    items, total = await service.list_screenings(movie_id, cinema_id, on_date, page, page_size, sort_by, order)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{screening_id}/seats", response_model=list[SeatOut])
async def get_screening_seats(screening_id: uuid.UUID, db: DbSession):
    service = ScreeningService(db)
    return await service.get_screening_seats(screening_id)
