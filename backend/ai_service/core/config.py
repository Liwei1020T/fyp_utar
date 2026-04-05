from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class AIServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="StringSense AI Service", alias="AI_APP_NAME")
    internal_api_key: str = Field(alias="AI_INTERNAL_API_KEY")


@lru_cache(maxsize=1)
def get_ai_settings() -> AIServiceSettings:
    return AIServiceSettings()  # type: ignore[call-arg]
