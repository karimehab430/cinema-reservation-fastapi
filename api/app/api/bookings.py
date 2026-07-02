import uuid

from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, DbSession
from app.schemas import BookingOut, PaginatedResponse, ReserveRequest
from app.services.bookings import BookingService

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.post("/reserve", response_model=BookingOut)
async def reserve_seats(payload: ReserveRequest, user: CurrentUser, db: DbSession):
    service = BookingService(db)
    return await service.reserve_seats(payload, user.id)


@router.post("/{booking_id}/confirm", response_model=BookingOut)
async def confirm_booking(booking_id: uuid.UUID, user: CurrentUser, db: DbSession):
    service = BookingService(db)
    return await service.confirm_booking(booking_id, user.id)


@router.get("/me", response_model=PaginatedResponse[BookingOut])
async def my_bookings(user: CurrentUser, db: DbSession, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1)):
    service = BookingService(db)
    items, total = await service.list_my_bookings(user.id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.delete("/{booking_id}", status_code=204)
async def cancel_booking(booking_id: uuid.UUID, user: CurrentUser, db: DbSession):
    service = BookingService(db)
    await service.cancel_booking(booking_id, user.id)
