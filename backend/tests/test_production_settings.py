from __future__ import annotations

import pytest

from app.config.settings import Settings


def production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "APP_ENV": "production",
        "DATABASE_URL": "postgresql+psycopg://user:password@postgres/stringsense",
        "JWT_SECRET_KEY": "production-test-secret-with-32-characters",
        "CORS_ORIGINS": "https://app.example.com",
        "TRUSTED_HOSTS": "api.example.com",
        "SEED_ADMIN_ENABLED": False,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_production_accepts_explicit_tunnel_security_config() -> None:
    production_settings().validate_runtime()


def test_comma_separated_lists_are_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@postgres/stringsense",
    )
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "production-test-secret-with-32-characters",
    )
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.example.com,https://admin.example.com",
    )
    monkeypatch.setenv(
        "TRUSTED_HOSTS",
        "api.example.com,127.0.0.1,backend",
    )
    monkeypatch.setenv("SEED_ADMIN_ENABLED", "false")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    settings.validate_runtime()

    assert settings.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
    assert settings.trusted_hosts == [
        "api.example.com",
        "127.0.0.1",
        "backend",
    ]


@pytest.mark.parametrize(
    "jwt_secret",
    (
        "short",
        "replace-with-a-long-random-secret",
        "stringsense-local-dev-secret-key-2026",
    ),
)
def test_production_rejects_weak_or_placeholder_jwt_secret(
    jwt_secret: str,
) -> None:
    settings = production_settings(JWT_SECRET_KEY=jwt_secret)

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        settings.validate_runtime()


def test_production_rejects_wildcard_trusted_hosts() -> None:
    settings = production_settings(TRUSTED_HOSTS="*")

    with pytest.raises(ValueError, match="TRUSTED_HOSTS"):
        settings.validate_runtime()


def test_production_rejects_insecure_cors_origin() -> None:
    settings = production_settings(CORS_ORIGINS="http://app.example.com")

    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        settings.validate_runtime()


def test_production_rejects_password_reset_code_preview() -> None:
    settings = production_settings(PASSWORD_RESET_DEV_PREVIEW_ENABLED=True)

    with pytest.raises(ValueError, match="PASSWORD_RESET_DEV_PREVIEW_ENABLED"):
        settings.validate_runtime()


def test_production_rejects_placeholder_seed_admin_password() -> None:
    settings = production_settings(
        SEED_ADMIN_ENABLED=True,
        SEED_ADMIN_USERNAME="admin",
        SEED_ADMIN_PHONE_NUMBER="+60123456789",
        SEED_ADMIN_PASSWORD="replace-with-a-strong-admin-password",
    )

    with pytest.raises(ValueError, match="SEED_ADMIN_PASSWORD"):
        settings.validate_runtime()
