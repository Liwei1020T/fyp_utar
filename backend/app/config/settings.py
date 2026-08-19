from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

from pydantic import Field
from pydantic import SecretStr
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_STRING_COHORT_PATH = BACKEND_ROOT.parent / "config/approved_string_cohort_v1.csv"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="StringSense Backend", alias="APP_NAME")
    api_prefix: str = "/api"
    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    port: int = Field(default=3001, alias="PORT")
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = Field(default="stringsense-python-api", alias="JWT_ISSUER")
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    store_timezone: str = Field(
        default="Asia/Kuala_Lumpur",
        alias="STORE_TIMEZONE",
    )
    password_reset_code_expire_minutes: int = Field(
        default=10,
        alias="PASSWORD_RESET_CODE_EXPIRE_MINUTES",
    )
    password_reset_code_max_attempts: int = Field(
        default=5,
        alias="PASSWORD_RESET_CODE_MAX_ATTEMPTS",
    )
    password_reset_dev_preview_enabled: bool = Field(
        default=False,
        alias="PASSWORD_RESET_DEV_PREVIEW_ENABLED",
    )
    expo_push_enabled: bool = Field(default=False, alias="EXPO_PUSH_ENABLED")
    expo_push_access_token: SecretStr | None = Field(
        default=None,
        alias="EXPO_ACCESS_TOKEN",
    )
    expo_push_endpoint: str = Field(
        default="https://exp.host/--/api/v2/push/send",
        alias="EXPO_PUSH_ENDPOINT",
    )
    openwa_enabled: bool = Field(default=False, alias="OPENWA_ENABLED")
    openwa_base_url: str = Field(
        default="http://127.0.0.1:2785/api",
        alias="OPENWA_BASE_URL",
    )
    openwa_session_id: str | None = Field(default=None, alias="OPENWA_SESSION_ID")
    openwa_api_key: SecretStr | None = Field(default=None, alias="OPENWA_API_KEY")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "http://127.0.0.1:8081",
            "http://localhost:8081",
        ],
        alias="CORS_ORIGINS",
    )
    approved_strings_source_path: str = Field(
        default="data/string_catalog_db_ready.json",
        alias="APPROVED_STRINGS_SOURCE_PATH",
    )
    recommendation_matrix_source_path: str = Field(
        default="../ml/nlp-workbench-latest/output/latest_macbert_review_matrix_system12.xlsx",
        alias="RECOMMENDATION_MATRIX_SOURCE_PATH",
    )
    seed_admin_enabled: bool = Field(default=False, alias="SEED_ADMIN_ENABLED")
    seed_admin_username: str | None = Field(default=None, alias="SEED_ADMIN_USERNAME")
    seed_admin_phone_number: str | None = Field(
        default=None,
        alias="SEED_ADMIN_PHONE_NUMBER",
    )
    seed_admin_password: str | None = Field(default=None, alias="SEED_ADMIN_PASSWORD")
    ai_internal_api_key: str | None = Field(default=None, alias="AI_INTERNAL_API_KEY")
    agent_enabled: bool = Field(default=False, alias="AGENT_ENABLED")
    agent_api_key: SecretStr | None = Field(default=None, alias="AGENT_API_KEY")
    agent_model: str = Field(default="deepseek-v4-flash", alias="AGENT_MODEL")
    agent_base_url: str = Field(
        default="https://api.deepseek.com",
        alias="AGENT_BASE_URL",
    )
    agent_timeout_seconds: float = Field(
        default=20,
        ge=1,
        le=60,
        alias="AGENT_TIMEOUT_SECONDS",
    )
    agent_max_tool_rounds: int = Field(
        default=2,
        ge=1,
        le=3,
        alias="AGENT_MAX_TOOL_ROUNDS",
    )
    upload_root_path_raw: str = Field(default="var/uploads", alias="UPLOAD_ROOT_PATH")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | Sequence[str]) -> list[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return [str(part).strip() for part in value if str(part).strip()]

    @field_validator("store_timezone")
    @classmethod
    def validate_store_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("STORE_TIMEZONE must be a valid IANA timezone") from error
        return value

    @model_validator(mode="after")
    def apply_defaults(self) -> "Settings":
        if self.jwt_secret_key is None:
            if self.environment == "production":
                raise ValueError("JWT_SECRET_KEY must be set in production")
            self.jwt_secret_key = "stringsense-local-dev-secret-key-2026"

        return self

    @property
    def approved_strings_path(self) -> Path:
        candidate = Path(self.approved_strings_source_path)
        if candidate.is_absolute():
            return candidate
        return BACKEND_ROOT / candidate

    @property
    def approved_string_cohort_path(self) -> Path:
        return SYSTEM_STRING_COHORT_PATH

    @property
    def recommendation_matrix_path(self) -> Path:
        candidate = Path(self.recommendation_matrix_source_path)
        if candidate.is_absolute():
            return candidate
        return BACKEND_ROOT / candidate

    @property
    def upload_root_path(self) -> Path:
        candidate = Path(self.upload_root_path_raw)
        if candidate.is_absolute():
            return candidate
        return BACKEND_ROOT / candidate

    @property
    def is_dev_like(self) -> bool:
        return self.environment in {"development", "testing"}

    @property
    def sqlalchemy_database_url(self) -> str:
        raw = self.database_url.strip()
        if raw.startswith("sqlite"):
            return raw
        if raw.startswith("file:"):
            candidate = Path(raw.removeprefix("file:"))
            if not candidate.is_absolute():
                candidate = BACKEND_ROOT / candidate
            return f"sqlite+pysqlite:///{candidate}"
        return raw

    def validate_runtime(self) -> None:
        if self.expo_push_enabled and self.openwa_enabled:
            raise ValueError("Enable only one remote notification provider")
        if (
            self.environment == "production"
            and self.expo_push_enabled
            and (
                self.expo_push_access_token is None
                or not self.expo_push_access_token.get_secret_value().strip()
            )
        ):
            raise ValueError(
                "EXPO_ACCESS_TOKEN must be set when Expo push is enabled in production"
            )
        if self.openwa_enabled:
            if not self.openwa_session_id:
                raise ValueError("OPENWA_SESSION_ID must be set when OpenWA is enabled")
            if (
                self.openwa_api_key is None
                or not self.openwa_api_key.get_secret_value().strip()
            ):
                raise ValueError("OPENWA_API_KEY must be set when OpenWA is enabled")
        if self.agent_enabled and (
            self.agent_api_key is None
            or not self.agent_api_key.get_secret_value().strip()
        ):
            raise ValueError("AGENT_API_KEY must be set when Agent is enabled")
        if self.seed_admin_enabled:
            self._require_seed_fields(
                "admin",
                self.seed_admin_username,
                self.seed_admin_phone_number,
                self.seed_admin_password,
            )

    @staticmethod
    def _require_seed_fields(
        role: str,
        username: str | None,
        phone_number: str | None,
        password: str | None,
    ) -> None:
        missing = [
            name
            for name, value in (
                ("username", username),
                ("phone_number", phone_number),
                ("password", password),
            )
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing seed {role} fields: {joined}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    settings.validate_runtime()
    return settings
