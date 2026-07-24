import uuid
from datetime import datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import BookingStatus, UserRole

T = TypeVar("T")


class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    full_name: Annotated[str | None, Field(max_length=255)] = None


class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: Annotated[str | None, Field(max_length=255)] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole



class TokenPair(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    refresh_token: str



class MovieCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Annotated[str, Field(min_length=1, max_length=255)]
    description: Annotated[str | None, Field(max_length=2000)] = None
    duration_minutes: Annotated[int | None, Field(gt=0)] = None
    poster_url: Annotated[str | None, Field(max_length=500)] = None


class MovieUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    description: Annotated[str | None, Field(max_length=2000)] = None
    duration_minutes: Annotated[int | None, Field(gt=0)] = None
    poster_url: Annotated[str | None, Field(max_length=500)] = None


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: str | None
    duration_minutes: int | None
    poster_url: str | None




class CinemaCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Annotated[str, Field(min_length=1, max_length=255)]
    location: Annotated[str | None, Field(max_length=255)] = None


class CinemaUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    location: Annotated[str | None, Field(max_length=255)] = None


class CinemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    location: str | None




class HallCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cinema_id: uuid.UUID
    name: Annotated[str, Field(min_length=1, max_length=255)]
    seat_rows: Annotated[int, Field(gt=0)]
    seat_columns: Annotated[int, Field(gt=0)]


class HallUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    seat_rows: Annotated[int | None, Field(gt=0)] = None
    seat_columns: Annotated[int | None, Field(gt=0)] = None


class HallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cinema_id: uuid.UUID
    name: str
    seat_rows: int
    seat_columns: int




class ScreeningCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    movie_id: uuid.UUID
    hall_id: uuid.UUID
    start_time: datetime
    price: Annotated[float, Field(gt=0)]


class ScreeningUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    start_time: datetime | None = None
    price: Annotated[float | None, Field(gt=0)] = None


class ScreeningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    movie_id: uuid.UUID
    hall_id: uuid.UUID
    start_time: datetime
    price: float




class SeatCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hall_id: uuid.UUID
    row_label: Annotated[str, Field(min_length=1, max_length=10)]
    seat_number: Annotated[int, Field(gt=0)]


class SeatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    row_label: str
    seat_number: int
    is_available: bool




class ReserveRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    screening_id: uuid.UUID
    seat_ids: Annotated[list[uuid.UUID], Field(min_length=1)]


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    screening_id: uuid.UUID
    status: BookingStatus
    expires_at: datetime | None
    total_amount: float | None



class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)
    items: list[T]
    total: int
    page: int
    page_size: int
