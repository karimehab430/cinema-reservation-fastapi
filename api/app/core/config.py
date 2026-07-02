from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "production"] = "development"
    database_url: str = Field(default="postgresql+asyncpg://user:pass@db:5432/cinema")
    redis_url: str = Field(default="redis://redis:6379/0")

    jwt_secret: str 
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)
    seat_hold_minutes: int = Field(default=10, ge=1)

    resend_api_key: str 
    resend_from_email: str


settings = Settings() # pyright: ignore[reportCallIssue]
