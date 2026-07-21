"""Identity models derived only from a cryptographically verified token."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthenticatedPrincipal(BaseModel):
    """Minimal identity projection; application roles are intentionally absent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject: str = Field(min_length=1, max_length=255)
    issuer: str = Field(min_length=1, max_length=2048)
    audience: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    email_verified: bool | None = None
    session_id: str | None = Field(default=None, max_length=255)
    authenticated_at: datetime
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_times(self) -> AuthenticatedPrincipal:
        if self.authenticated_at.utcoffset() is None:
            raise ValueError("authenticated_at must include a timezone")
        if self.email_verified is not None and self.email is None:
            raise ValueError("email verification state requires an email claim")
        if self.expires_at is not None:
            if self.expires_at.utcoffset() is None:
                raise ValueError("expires_at must include a timezone")
            if self.expires_at <= self.authenticated_at:
                raise ValueError("expires_at must be after authenticated_at")
        return self

    @property
    def principal_id(self) -> str:
        return f"human:{self.subject}"
