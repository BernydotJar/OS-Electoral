"""Liveness and dependency readiness endpoints."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict

from campaignos.data import DatabaseRuntime
from campaignos.identity.oidc import TokenVerifier

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    version: str


class ReadinessCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    ready: bool
    detail: str


class ReadinessResponse(HealthResponse):
    checks: list[ReadinessCheck]


@router.get("/health", response_model=HealthResponse, summary="Service liveness")
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="UP", service=settings.service_name, version=settings.service_version
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Service readiness")
def ready(request: Request, response: Response) -> ReadinessResponse:
    settings = request.app.state.settings
    verifier = cast(TokenVerifier, request.app.state.token_verifier)
    identity_ready, identity_detail = verifier.readiness()
    database = cast(DatabaseRuntime, request.app.state.database)
    database_ready, database_detail = database.readiness()
    checks = [
        ReadinessCheck(
            name="identity",
            ready=identity_ready,
            detail=identity_detail,
        ),
        ReadinessCheck(name="database", ready=database_ready, detail=database_detail),
    ]
    all_ready = all(item.ready for item in checks)
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="READY" if all_ready else "NOT_READY",
        service=settings.service_name,
        version=settings.service_version,
        checks=checks,
    )
