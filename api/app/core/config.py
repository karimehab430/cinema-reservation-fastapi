from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "production"] = "development"
    database_url: str = Field(default="postgresql+asyncpg://user:pass@db:5432/cinema")
    redis_url: str = Field(default="redis://redis:6379/0")

    jwt_secret: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)
    seat_hold_minutes: int = Field(default=10, ge=1)

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if value in {"change-me-in-production", ""} and cls.__name__ == "Settings":
            return value
        return value

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()
