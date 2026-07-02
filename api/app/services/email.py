from __future__ import annotations

from typing import Any

import resend

from app.core.config import settings


class EmailService:
    def __init__(self):
        resend.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        from_email: str | None = None,
    ) -> Any:
        
        try:
            response = resend.Emails.send(
                {
                    "from": from_email or self.from_email,
                    "to": to,
                    "subject": subject,
                    "html": html,
                }
            )
            return response
        
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    async def send_booking_confirmation(
        self,
        to: str,
        booking_id: str,
        movie_title: str,
        screening_time: str,
        seats: list[str],
    ) -> Any:
        """Send a booking confirmation email."""
        seats_str = ", ".join(seats)
        html = f"""
        <h2>Booking Confirmation</h2>
        <p>Your booking has been confirmed!</p>
        <ul>
            <li><strong>Booking ID:</strong> {booking_id}</li>
            <li><strong>Movie:</strong> {movie_title}</li>
            <li><strong>Screening:</strong> {screening_time}</li>
            <li><strong>Seats:</strong> {seats_str}</li>
        </ul>
        <p>Thank you for your booking!</p>
        """
        return await self.send_email(to, "Booking Confirmation", html)

    async def send_registration_confirmation(self, to: str, user_name: str) -> Any:
        """Send a registration confirmation email."""
        html = f"""
        <h2>Welcome {user_name}!</h2>
        <p>Your account has been successfully created.</p>
        <p>You can now log in and start booking movie tickets.</p>
        """
        return await self.send_email(to, "Welcome to Cinema Reservation", html)
