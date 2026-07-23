"""Liveness, dependency readiness and service-level metrics endpoints."""

from __future__ import annotations

import secrets
from typing import cast

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict

from campaignos.data import DatabaseRuntime
from campaignos.identity.oidc import TokenVerifier
from campaignos.observability import MetricsRegistry

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
    metrics = cast(MetricsRegistry, request.app.state.metrics)
    for item in checks:
        metrics.set_readiness(item.name, item.ready)
    all_ready = all(item.ready for item in checks)
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="READY" if all_ready else "NOT_READY",
        service=settings.service_name,
        version=settings.service_version,
        checks=checks,
    )


@router.get(
    "/metrics",
    response_class=Response,
    summary="Low-cardinality Prometheus service metrics",
    include_in_schema=False,
)
def metrics(request: Request) -> Response:
    settings = request.app.state.settings
    if not settings.metrics_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    configured_token = settings.metrics_bearer_token
    if configured_token is not None:
        authorization = request.headers.get("authorization", "")
        scheme, _, supplied_token = authorization.partition(" ")
        expected_token = configured_token.get_secret_value()
        if scheme.lower() != "bearer" or not secrets.compare_digest(supplied_token, expected_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Metrics authentication is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
    registry = cast(MetricsRegistry, request.app.state.metrics)
    database = cast(DatabaseRuntime, request.app.state.database)
    payload = registry.render_prometheus(
        service=settings.service_name,
        version=settings.service_version,
        database_pool=database.pool_snapshot(),
    )
    return Response(
        content=payload,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
