"""Identity models derived only from a cryptographically verified token."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedPrincipal(BaseModel):
    """Minimal identity projection; application roles are intentionally absent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject: str = Field(min_length=1, max_length=255)
    issuer: str = Field(min_length=1, max_length=2048)
    audience: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    session_id: str | None = Field(default=None, max_length=255)
    authenticated_at: datetime

    @property
    def principal_id(self) -> str:
        return f"human:{self.subject}"
