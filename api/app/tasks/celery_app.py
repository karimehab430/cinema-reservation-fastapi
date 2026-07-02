from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "cinema",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.send_booking_confirmation_email": {"queue": "high_priority"},
        "app.tasks.release_seats_task": {"queue": "default"},
        "app.tasks.release_expired_seats": {"queue": "default"},
    },
    beat_schedule={
        "release-expired-seats-every-minute": {
            "task": "app.tasks.release_expired_seats",
            "schedule": 60.0,
        },
    },
)
