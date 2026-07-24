from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas import CinemaCreate, CinemaOut, PaginatedResponse
from app.services.cinemas import CinemaService

router = APIRouter(prefix="/api/v1/cinemas", tags=["cinemas"])


@router.get("", response_model=PaginatedResponse[CinemaOut])
async def list_cinemas(db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1)):
    service = CinemaService(db)
    items, total = await service.list_cinemas(page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=CinemaOut, status_code=status.HTTP_201_CREATED)
async def create_cinema(payload: CinemaCreate, db: AsyncSession = Depends(get_db)):
    service = CinemaService(db)
    return await service.create_cinema(payload)
