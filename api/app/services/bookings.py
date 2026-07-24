from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Booking, BookingSeat, BookingStatus, Screening, Seat
from app.schemas import ReserveRequest
from app.tasks import release_seats_task, send_booking_confirmation_email

logger = get_logger(__name__)


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def reserve_seats(
        self, payload: ReserveRequest, user_id: uuid.UUID
    ) -> Booking:
        
        if not payload.seat_ids:
            raise ValidationError("No seats selected")

        async with self.db.begin():
            screening = await self.db.get(Screening, payload.screening_id)
            if screening is None:
                raise NotFoundError("Screening not found")

            lock_stmt = (
                select(Seat.id)
                .where(Seat.id.in_(payload.seat_ids), Seat.hall_id == screening.hall_id)
                .with_for_update(skip_locked=True)
            )
            locked = (await self.db.execute(lock_stmt)).scalars().all()
            locked_ids = set(locked)

            missing = set(payload.seat_ids) - locked_ids
            if missing:
                raise ConflictError("One or more seats are unavailable")

            taken_stmt = (
                select(BookingSeat.seat_id)
                .join(Booking, Booking.id == BookingSeat.booking_id)
                .where(
                    Booking.screening_id == screening.id,
                    BookingSeat.seat_id.in_(locked_ids),
                    Booking.status.in_(
                        [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                    ),
                )
            )
            taken = (await self.db.execute(taken_stmt)).scalars().all()
            if taken:
                raise ConflictError("One or more seats are already booked")

            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.seat_hold_minutes
            )
            total = Decimal(str(screening.price)) * len(locked_ids)

            booking = Booking(
                user_id=user_id,
                screening_id=screening.id,
                status=BookingStatus.PENDING,
                expires_at=expires_at,
                total_amount=total,
            )
            self.db.add(booking)
            await self.db.flush()

            for seat_id in locked_ids:
                self.db.add(BookingSeat(booking_id=booking.id, seat_id=seat_id))

        await self.db.refresh(booking)
        release_seats_task.delay(str(booking.id))  # type: ignore

        logger.info(
            "booking_created",
            extra={
                "event": "booking_created",
                "booking_id": str(booking.id),
                "user_id": str(user_id),
            },
        )
        return booking

    async def confirm_booking(
        self, booking_id: uuid.UUID, user_id: uuid.UUID
    ) -> Booking:
        expired = False
        async with self.db.begin():
            stmt = (
                select(Booking)
                .where(Booking.id == booking_id)
                .with_for_update()
            )
            booking = (await self.db.execute(stmt)).scalar_one_or_none()
            if not booking or booking.user_id != user_id:
                raise NotFoundError("Booking not found")
            if booking.status != BookingStatus.PENDING:
                raise ConflictError(f"Booking is {booking.status.value}, cannot confirm")
            if booking.expires_at and booking.expires_at < datetime.now(timezone.utc):
                booking.status = BookingStatus.EXPIRED
                expired = True
            else:
                booking.status = BookingStatus.CONFIRMED
                booking.expires_at = None

        if expired:
            logger.warning(
                "booking_expired",
                extra={
                    "event": "booking_expired",
                    "booking_id": str(booking.id),
                    "user_id": str(user_id),
                },
            )
            raise ConflictError("Booking hold has expired")

        await self.db.refresh(booking)
        send_booking_confirmation_email.delay(str(booking.id))  # type: ignore

        logger.info(
            "payment_completed",
            extra={
                "event": "payment_completed",
                "booking_id": str(booking.id),
                "user_id": str(user_id),
            },
        )
        logger.info(
            "booking_confirmed",
            extra={
                "event": "booking_confirmed",
                "booking_id": str(booking.id),
                "user_id": str(user_id),
            },
        )
        return booking

    async def list_my_bookings(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[Booking], int]:
        total = (
            await self.db.scalar(
                select(func.count())
                .select_from(Booking)
                .where(Booking.user_id == user_id)
            )
            or 0
        )
        result = await self.db.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.booked_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total)

    async def cancel_booking(self, booking_id: uuid.UUID, user_id: uuid.UUID) -> None:
        async with self.db.begin():
            stmt = (
                select(Booking)
                .where(Booking.id == booking_id)
                .with_for_update()
            )
            booking = (await self.db.execute(stmt)).scalar_one_or_none()
            if not booking or booking.user_id != user_id:
                raise NotFoundError("Booking not found")
            if booking.status != BookingStatus.PENDING:
                raise ConflictError("Only pending bookings can be cancelled")

            booking.status = BookingStatus.CANCELLED
