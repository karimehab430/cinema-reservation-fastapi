import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    password: str
    full_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: str


class TokenPair(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    refresh_token: str


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: str | None
    duration_minutes: int | None
    poster_url: str | None


class CinemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    location: str | None


class ScreeningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    movie_id: uuid.UUID
    hall_id: uuid.UUID
    start_time: datetime
    price: float


class SeatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    row_label: str
    seat_number: int
    is_available: bool


class ReserveRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    screening_id: uuid.UUID
    seat_ids: list[uuid.UUID]


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    screening_id: uuid.UUID
    status: str
    expires_at: datetime | None
    total_amount: float | None


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    items: list[T]
    total: int
    page: int
    page_size: int
