"""Authenticated identity projection."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from campaignos.api.dependencies import current_principal
from campaignos.identity.models import AuthenticatedPrincipal

router = APIRouter(tags=["identity"])
CurrentPrincipal = Annotated[AuthenticatedPrincipal, Depends(current_principal)]


class MeResponse(BaseModel):
    """Identity only; memberships must later come from application persistence."""

    model_config = ConfigDict(extra="forbid")

    principal_id: str
    subject: str
    issuer: str
    display_name: str | None
    email: str | None
    authenticated_at: datetime
    application_memberships: list[dict[str, str]]
    authorization_status: str


@router.get("/me", response_model=MeResponse, summary="Current authenticated identity")
def me(principal: CurrentPrincipal) -> MeResponse:
    return MeResponse(
        principal_id=principal.principal_id,
        subject=principal.subject,
        issuer=principal.issuer,
        display_name=principal.display_name,
        email=principal.email,
        authenticated_at=principal.authenticated_at,
        application_memberships=[],
        authorization_status="NOT_LOADED",
    )
