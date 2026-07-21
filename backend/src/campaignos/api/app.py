"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from campaignos.api.errors import install_exception_handlers
from campaignos.api.middleware import request_controls
from campaignos.api.routes import campaigns, health, me, tenant_me, workspaces
from campaignos.campaigns import (
    CampaignCreator,
    CampaignDirectory,
    CampaignReadinessReader,
    CampaignWriter,
    SqlAlchemyCampaignCreator,
    SqlAlchemyCampaignDirectory,
    SqlAlchemyCampaignReadinessReader,
    SqlAlchemyCampaignWriter,
    UnavailableCampaignCreator,
    UnavailableCampaignDirectory,
    UnavailableCampaignReadinessReader,
    UnavailableCampaignWriter,
)
from campaignos.config import Settings, get_settings
from campaignos.data import Database, DatabaseRuntime, UnavailableDatabase
from campaignos.identity.authorization import (
    MembershipDirectory,
    SqlAlchemyMembershipDirectory,
    UnavailableMembershipDirectory,
)
from campaignos.identity.oidc import OidcTokenVerifier, TokenVerifier, UnavailableTokenVerifier
from campaignos.workspaces import (
    SqlAlchemyWorkspaceWriter,
    UnavailableWorkspaceWriter,
    WorkspaceWriter,
)


def create_app(
    settings: Settings | None = None,
    *,
    token_verifier: TokenVerifier | None = None,
    database: DatabaseRuntime | None = None,
    membership_directory: MembershipDirectory | None = None,
    campaign_creator: CampaignCreator | None = None,
    campaign_directory: CampaignDirectory | None = None,
    campaign_readiness_reader: CampaignReadinessReader | None = None,
    campaign_writer: CampaignWriter | None = None,
    workspace_writer: WorkspaceWriter | None = None,
) -> FastAPI:
    runtime_settings = settings or get_settings()
    verifier = token_verifier
    if verifier is None and runtime_settings.oidc_configured:
        verifier = OidcTokenVerifier(runtime_settings)
    verifier = verifier or UnavailableTokenVerifier()
    database_runtime = database
    if database_runtime is None and runtime_settings.database_url:
        database_runtime = Database.from_url(
            runtime_settings.database_url,
            pool_size=runtime_settings.database_pool_size,
            max_overflow=runtime_settings.database_max_overflow,
            pool_timeout_seconds=runtime_settings.database_pool_timeout_seconds,
        )
    database_runtime = database_runtime or UnavailableDatabase()
    authorization_directory = membership_directory
    if authorization_directory is None and isinstance(database_runtime, Database):
        authorization_directory = SqlAlchemyMembershipDirectory(database_runtime)
    authorization_directory = authorization_directory or UnavailableMembershipDirectory()
    campaign_create_boundary = campaign_creator
    if campaign_create_boundary is None and isinstance(database_runtime, Database):
        campaign_create_boundary = SqlAlchemyCampaignCreator(database_runtime)
    campaign_create_boundary = campaign_create_boundary or UnavailableCampaignCreator()
    campaign_read_directory = campaign_directory
    if campaign_read_directory is None and isinstance(database_runtime, Database):
        campaign_read_directory = SqlAlchemyCampaignDirectory(database_runtime)
    campaign_read_directory = campaign_read_directory or UnavailableCampaignDirectory()
    campaign_readiness_boundary = campaign_readiness_reader
    if campaign_readiness_boundary is None and isinstance(database_runtime, Database):
        campaign_readiness_boundary = SqlAlchemyCampaignReadinessReader(database_runtime)
    campaign_readiness_boundary = (
        campaign_readiness_boundary or UnavailableCampaignReadinessReader()
    )
    campaign_write_boundary = campaign_writer
    if campaign_write_boundary is None and isinstance(database_runtime, Database):
        campaign_write_boundary = SqlAlchemyCampaignWriter(database_runtime)
    campaign_write_boundary = campaign_write_boundary or UnavailableCampaignWriter()
    workspace_write_boundary = workspace_writer
    if workspace_write_boundary is None and isinstance(database_runtime, Database):
        workspace_write_boundary = SqlAlchemyWorkspaceWriter(database_runtime)
    workspace_write_boundary = workspace_write_boundary or UnavailableWorkspaceWriter()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.logger.info(
            "campaignos_api_started",
            extra={"environment": runtime_settings.environment.value},
        )
        yield
        database_runtime.dispose()
        app.state.logger.info("campaignos_api_stopped")

    docs_url = "/docs" if runtime_settings.expose_api_docs else None
    redoc_url = "/redoc" if runtime_settings.expose_api_docs else None
    app = FastAPI(
        title="CampaignOS API",
        summary="Human-gated campaign operating system",
        version=runtime_settings.service_version,
        openapi_url="/api/v1/openapi.json",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )
    app.state.settings = runtime_settings
    app.state.token_verifier = verifier
    app.state.database = database_runtime
    app.state.membership_directory = authorization_directory
    app.state.campaign_creator = campaign_create_boundary
    app.state.campaign_directory = campaign_read_directory
    app.state.campaign_readiness_reader = campaign_readiness_boundary
    app.state.campaign_writer = campaign_write_boundary
    app.state.workspace_writer = workspace_write_boundary
    app.state.logger = logging.getLogger(runtime_settings.service_name)

    app.middleware("http")(request_controls)
    install_exception_handlers(app)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(me.router, prefix="/api/v1")
    app.include_router(tenant_me.router, prefix="/api/v1")
    app.include_router(campaigns.router, prefix="/api/v1")
    app.include_router(workspaces.router, prefix="/api/v1")
    return app


app = create_app()
