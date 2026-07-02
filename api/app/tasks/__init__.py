import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models import Booking, BookingStatus
from app.services.email import EmailService


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_booking_confirmation_email(self, booking_id: str):
    """Send a booking confirmation email via Resend."""
    try:
        asyncio.run(_send_confirmation(booking_id))
    except Exception as exc:
        self.retry(exc=exc)


async def _send_confirmation(booking_id: str):
    """Fetch booking details and send confirmation email."""
    async with AsyncSessionLocal() as db:
        booking = await db.get(Booking, booking_id)
        if not booking:
            print(f"[email] Booking {booking_id} not found")
            return

        movie = booking.screening.movie
        screening = booking.screening
        seats = [f"{bs.seat.row_label}{bs.seat.seat_number}" for bs in booking.booking_seats]

        email_service = EmailService()
        await email_service.send_booking_confirmation(
            to=booking.user.email,
            booking_id=booking_id,
            movie_title=movie.title,
            screening_time=screening.start_time.isoformat(),
            seats=seats,
        )
        print(f"[email] Sent confirmation for booking {booking_id} to {booking.user.email}")


async def _release_booking(booking_id: uuid.UUID):
    async with AsyncSessionLocal() as db:
        booking = await db.get(Booking, booking_id)
        if booking and booking.status == BookingStatus.PENDING.value:
            booking.status = BookingStatus.EXPIRED.value
            await db.commit()


@celery_app.task
def release_seats_task(booking_id: str):
    """Scheduled with an ETA at reservation time; idempotent no-op if already confirmed/cancelled."""
    asyncio.run(_release_booking(uuid.UUID(booking_id)))


async def _release_all_expired():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Booking).where(
                Booking.status == BookingStatus.PENDING.value,
                Booking.expires_at < now,
            )
        )
        expired = result.scalars().all()
        for booking in expired:
            booking.status = BookingStatus.EXPIRED.value
        if expired:
            await db.commit()
        return len(expired)


@celery_app.task
def release_expired_seats():
    """Safety-net sweep in case a per-booking ETA task was lost (worker restart, etc.)."""
    count = asyncio.run(_release_all_expired())
    print(f"[beat] Released {count} expired bookings")
