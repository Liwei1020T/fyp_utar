from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "StringSense API"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    token_issuer: str = "stringsense-backend"
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    password_reset_code_expire_minutes: int = Field(
        default=10,
        alias="PASSWORD_RESET_CODE_EXPIRE_MINUTES",
    )
    password_reset_code_max_attempts: int = Field(
        default=5,
        alias="PASSWORD_RESET_CODE_MAX_ATTEMPTS",
    )
    enable_dev_auth: bool = Field(default=False, alias="ENABLE_DEV_AUTH")
    password_reset_dev_preview_enabled: bool = Field(
        default=False,
        alias="PASSWORD_RESET_DEV_PREVIEW_ENABLED",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        alias="CORS_ORIGINS",
    )
    seed_admin_full_name: str = Field(
        default="System Admin",
        alias="SEED_ADMIN_FULL_NAME",
    )
    seed_admin_phone_number: str = Field(
        default="0190000000",
        alias="SEED_ADMIN_PHONE_NUMBER",
    )
    seed_admin_password: str = Field(
        default="admin123",
        alias="SEED_ADMIN_PASSWORD",
    )
    dev_customer_phone_number: str = Field(
        default="0110000000",
        alias="DEV_CUSTOMER_PHONE_NUMBER",
    )
    dev_customer_full_name: str = Field(
        default="Dev Customer",
        alias="DEV_CUSTOMER_FULL_NAME",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: str | Sequence[str]) -> list[str]:
        if isinstance(value, str):
            parts = [item.strip() for item in value.split(",")]
            return [item for item in parts if item]
        return [str(item).strip() for item in value if str(item).strip()]

    @model_validator(mode="after")
    def _set_safe_defaults(self) -> "Settings":
        if self.database_url is None:
            if self.environment == "testing":
                self.database_url = "sqlite+pysqlite:///./test_stringsense.db"
            else:
                raise ValueError("DATABASE_URL must be set")

        if self.jwt_secret_key is None:
            if self.environment == "production":
                raise ValueError("JWT_SECRET_KEY must be set in production")
            self.jwt_secret_key = "stringsense-local-dev-secret-key-2026"

        return self

    @property
    def is_dev_like(self) -> bool:
        return self.environment in {"development", "testing"}


settings = Settings()
