import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models import Booking, BookingStatus


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_booking_confirmation_email(self, booking_id: str):
    # Plug in your real email provider (SES, SendGrid, etc.) here.
    print(f"[email] Sending confirmation for booking {booking_id}")


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
