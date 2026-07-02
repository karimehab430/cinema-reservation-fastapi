from fastapi import APIRouter, Query

from app.dependencies import DbSession
from app.schemas import CinemaOut, PaginatedResponse
from app.services.cinemas import CinemaService

router = APIRouter(prefix="/api/v1/cinemas", tags=["cinemas"])


@router.get("", response_model=PaginatedResponse[CinemaOut])
async def list_cinemas(db: DbSession, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1)):
    service = CinemaService(db)
    items, total = await service.list_cinemas(page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
