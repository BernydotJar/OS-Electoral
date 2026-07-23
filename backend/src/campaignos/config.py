"""Typed runtime configuration with fail-closed production validation."""

from __future__ import annotations

import re
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

from campaignos import __version__

DEFAULT_SECRETS_DIR = Path("/run/secrets")
CONFIGURED_SECRETS_DIR = DEFAULT_SECRETS_DIR if DEFAULT_SECRETS_DIR.is_dir() else None


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """CampaignOS configuration loaded from environment or mounted secrets.

    OIDC values are optional only so liveness diagnostics can start in a local
    environment. Staging and production fail during settings validation when
    identity configuration is absent or insecure.
    """

    model_config = SettingsConfigDict(
        env_prefix="CAMPAIGNOS_",
        case_sensitive=False,
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        secrets_dir=CONFIGURED_SECRETS_DIR,
    )

    environment: Environment = Environment.DEVELOPMENT
    service_name: str = "campaignos-api"
    service_version: str = __version__
    log_level: str = "INFO"
    expose_api_docs: bool = True
    metrics_enabled: bool = True
    metrics_bearer_token: SecretStr | None = None

    database_url: str | None = None
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=5, ge=0, le=50)
    database_pool_timeout_seconds: int = Field(default=5, ge=1, le=30)

    object_storage_endpoint: str | None = None
    object_storage_access_key: str | None = None
    object_storage_secret_key: SecretStr | None = None
    object_storage_bucket: str | None = None
    object_storage_region: str = "us-east-1"
    object_storage_force_path_style: bool = False

    smtp_host: str | None = None
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_from: str | None = None

    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_algorithm: str = "RS256"
    oidc_token_use: Literal["id"] = "id"  # noqa: S105 - OIDC claim value, not a secret.
    oidc_clock_skew_seconds: int = Field(default=30, ge=0, le=120)
    oidc_jwks_timeout_seconds: int = Field(default=5, ge=1, le=15)
    oidc_jwks_cache_seconds: int = Field(default=300, ge=60, le=3600)

    development_access_token: SecretStr | None = None
    development_principal_subject: str = Field(
        default="local-operator", min_length=1, max_length=255
    )
    development_principal_display_name: str | None = Field(default="Operador local", max_length=255)
    development_principal_email: str | None = Field(default="operator@localhost", max_length=320)

    @field_validator("development_access_token", "metrics_bearer_token", mode="before")
    @classmethod
    def normalize_optional_secret(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_security_configuration(self) -> Settings:
        if self.oidc_algorithm != "RS256":
            raise ValueError("CampaignOS supports only the pinned RS256 OIDC algorithm")

        configured = (self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url)
        if any(configured) and not all(configured):
            raise ValueError("OIDC issuer, audience and JWKS URL must be configured together")

        if (
            self.metrics_bearer_token is not None
            and len(self.metrics_bearer_token.get_secret_value()) < 24
        ):
            raise ValueError("Metrics bearer token must contain at least 24 characters")

        if self.development_access_token is not None:
            if self.environment is not Environment.DEVELOPMENT:
                raise ValueError(
                    "Development identity is allowed only in the development environment"
                )
            if any(configured):
                raise ValueError("Development identity cannot be combined with OIDC configuration")
            if len(self.development_access_token.get_secret_value()) < 24:
                raise ValueError("Development access token must contain at least 24 characters")

        if all(configured):
            for field_name, value in (
                ("oidc_issuer", self.oidc_issuer),
                ("oidc_jwks_url", self.oidc_jwks_url),
            ):
                parsed = urlparse(value or "")
                if parsed.scheme != "https" or not parsed.netloc or parsed.username:
                    raise ValueError(f"{field_name} must be an absolute HTTPS URL")

        if self.database_url:
            try:
                database = make_url(self.database_url)
            except Exception as exc:
                raise ValueError("database_url must be a valid SQLAlchemy URL") from exc
            if database.drivername != "postgresql+psycopg":
                raise ValueError("CampaignOS database_url must use postgresql+psycopg")
            if not database.host or not database.database or not database.username:
                raise ValueError("database_url must include host, database and username")

        storage = (
            self.object_storage_endpoint,
            self.object_storage_access_key,
            self.object_storage_secret_key,
            self.object_storage_bucket,
        )
        if any(storage) and not all(storage):
            raise ValueError(
                "Object storage endpoint, credentials and bucket must be configured together"
            )
        if all(storage):
            endpoint = urlparse(self.object_storage_endpoint or "")
            if (
                endpoint.scheme not in {"http", "https"}
                or not endpoint.netloc
                or endpoint.username
                or endpoint.password
                or endpoint.query
                or endpoint.fragment
            ):
                raise ValueError("object_storage_endpoint must be an absolute HTTP(S) URL")
            if self.environment in {Environment.STAGING, Environment.PRODUCTION} and (
                endpoint.scheme != "https"
            ):
                raise ValueError("Object storage must use HTTPS outside development and test")
            if not re.fullmatch(
                r"(?=.{3,63}\Z)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?",
                self.object_storage_bucket or "",
            ):
                raise ValueError("object_storage_bucket must be a valid S3 bucket name")
            secret = self.object_storage_secret_key
            if secret is None or len(secret.get_secret_value()) < 8:
                raise ValueError("object_storage_secret_key must contain at least 8 characters")

        smtp = (self.smtp_host, self.smtp_from)
        if any(smtp) and not all(smtp):
            raise ValueError("SMTP host and sender must be configured together")
        if all(smtp):
            if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", self.smtp_host or ""):
                raise ValueError("smtp_host must be a hostname without a URL scheme")
            if not re.fullmatch(r"[^@\s]+@[^@\s]+", self.smtp_from or ""):
                raise ValueError("smtp_from must be an email address")

        if self.environment in {Environment.STAGING, Environment.PRODUCTION}:
            if not all(configured):
                raise ValueError("OIDC configuration is required outside development and test")
            if self.expose_api_docs:
                raise ValueError(
                    "Interactive API documentation must be disabled in staging/production"
                )
            if not self.database_url:
                raise ValueError(
                    "PostgreSQL configuration is required outside development and test"
                )
            if self.metrics_enabled and self.metrics_bearer_token is None:
                raise ValueError(
                    "Metrics bearer token is required when metrics are enabled "
                    "outside development and test"
                )

        return self

    @property
    def oidc_configured(self) -> bool:
        return bool(self.oidc_issuer and self.oidc_audience and self.oidc_jwks_url)

    @property
    def development_identity_configured(self) -> bool:
        return self.development_access_token is not None

    @property
    def object_storage_configured(self) -> bool:
        return bool(
            self.object_storage_endpoint
            and self.object_storage_access_key
            and self.object_storage_secret_key
            and self.object_storage_bucket
        )

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)


@lru_cache
def get_settings() -> Settings:
    return Settings()
