from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


def uuid_pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    hashed_token: Mapped[str] = mapped_column(String, nullable=False)
    revoked: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class Cinema(Base):
    __tablename__ = "cinemas"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str | None] = mapped_column(String)

    halls: Mapped[list["Hall"]] = relationship(back_populates="cinema")


class Hall(Base):
    __tablename__ = "halls"
    __table_args__ = (
        CheckConstraint("seat_rows > 0", name="ck_hall_seat_rows_positive"),
        CheckConstraint("seat_columns > 0", name="ck_hall_seat_columns_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    cinema_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cinemas.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    seat_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_columns: Mapped[int] = mapped_column(Integer, nullable=False)

    cinema: Mapped["Cinema"] = relationship(back_populates="halls")
    seats: Mapped[list["Seat"]] = relationship(back_populates="hall")
    screenings: Mapped[list["Screening"]] = relationship(back_populates="hall")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    poster_url: Mapped[str | None] = mapped_column(String)

    screenings: Mapped[list["Screening"]] = relationship(back_populates="movie")


class Screening(Base):
    __tablename__ = "screenings"
    __table_args__ = (
        UniqueConstraint("hall_id", "start_time", name="uq_hall_start_time"),
        CheckConstraint("price > 0", name="ck_screening_price_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    movie_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("movies.id"))
    hall_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("halls.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    movie: Mapped["Movie"] = relationship(back_populates="screenings")
    hall: Mapped["Hall"] = relationship(back_populates="screenings")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="screening")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("hall_id", "row_label", "seat_number", name="uq_hall_seat"),
        CheckConstraint("seat_number > 0", name="ck_seat_number_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    hall_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("halls.id"))
    row_label: Mapped[str] = mapped_column(String, nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)

    hall: Mapped["Hall"] = relationship(back_populates="seats")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    screening_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("screenings.id"))
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))

    user: Mapped["User"] = relationship(back_populates="bookings")
    screening: Mapped["Screening"] = relationship(back_populates="bookings")
    booking_seats: Mapped[list["BookingSeat"]] = relationship(back_populates="booking", cascade="all, delete-orphan")


class BookingSeat(Base):
    __tablename__ = "booking_seats"

    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), primary_key=True)
    seat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seats.id"), primary_key=True)

    booking: Mapped["Booking"] = relationship(back_populates="booking_seats")
    seat: Mapped["Seat"] = relationship()
