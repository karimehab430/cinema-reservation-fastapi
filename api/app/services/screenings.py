from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models import Booking, BookingSeat, BookingStatus, Screening, Seat
from app.schemas import SeatOut


class ScreeningService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_screenings(
        self,
        movie_id: uuid.UUID | None,
        cinema_id: uuid.UUID | None,
        on_date: date | None,
        page: int,
        page_size: int,
        sort_by: str,
        order: str,
    ) -> tuple[list[Screening], int]:
        stmt = select(Screening)
        if movie_id:
            stmt = stmt.where(Screening.movie_id == movie_id)
        if on_date:
            start = datetime.combine(on_date, datetime.min.time())
            end = start + timedelta(days=1)
            stmt = stmt.where(Screening.start_time >= start, Screening.start_time < end)

        if cinema_id:
            stmt = stmt.join(Screening.hall).where(
                Screening.hall.has(cinema_id=cinema_id)
            )

        sort_column = {"date": Screening.start_time, "price": Screening.price}.get(
            sort_by, Screening.start_time
        )
        stmt = stmt.order_by(
            sort_column.asc() if order != "desc" else sort_column.desc()
        )

        total = (
            await self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), int(total)

    async def get_screening_seats(self, screening_id: uuid.UUID) -> list[SeatOut]:
        screening = await self.db.get(Screening, screening_id)
        if screening is None:
            raise NotFoundError("Screening not found")

        seats_result = await self.db.execute(
            select(Seat).where(Seat.hall_id == screening.hall_id)
        )
        seats = seats_result.scalars().all()

        taken_result = await self.db.execute(
            select(BookingSeat.seat_id)
            .join(Booking, Booking.id == BookingSeat.booking_id)
            .where(
                Booking.screening_id == screening_id,
                Booking.status.in_(
                    [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
            )
        )
        taken_ids = {row[0] for row in taken_result.all()}

        return [
            SeatOut(
                id=s.id,
                row_label=s.row_label,
                seat_number=s.seat_number,
                is_available=s.id not in taken_ids,
            )
            for s in seats
        ]
