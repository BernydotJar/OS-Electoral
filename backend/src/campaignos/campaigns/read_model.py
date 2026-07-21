"""Tenant-scoped campaign read model for protected API projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from campaignos.data.database import Database
from campaignos.data.models import Campaign


class CampaignNotFound(LookupError):
    """The requested campaign is not available in the selected tenant."""


class CampaignDirectoryUnavailable(RuntimeError):
    """The campaign persistence boundary cannot currently be queried."""


class CampaignProjection(BaseModel):
    """Safe read-only campaign representation returned by the API."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    slug: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    jurisdiction: str = Field(min_length=1, max_length=255)
    stage: str = Field(min_length=1, max_length=80)
    status: str = Field(pattern="^(DRAFT|ACTIVE)$")
    version: int = Field(ge=1)


class CampaignPage(BaseModel):
    """Keyset-paginated campaign page without a tenant-wide total count."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[CampaignProjection, ...]
    next_cursor: UUID | None


class CampaignDirectory(Protocol):
    """Load campaigns inside an explicit tenant scope."""

    def get(self, tenant_id: UUID, campaign_id: UUID) -> CampaignProjection:
        """Return one campaign or fail closed."""

    def list_authorized(
        self,
        tenant_id: UUID,
        campaign_ids: tuple[UUID, ...],
        *,
        limit: int,
        cursor: UUID | None,
    ) -> CampaignPage:
        """Return only explicitly authorized campaigns using UUID keyset pagination."""


class UnavailableCampaignDirectory:
    """Fail-closed directory used before persistence is configured."""

    def get(self, tenant_id: UUID, campaign_id: UUID) -> CampaignProjection:
        del tenant_id, campaign_id
        raise CampaignDirectoryUnavailable("Campaign directory is unavailable")

    def list_authorized(
        self,
        tenant_id: UUID,
        campaign_ids: tuple[UUID, ...],
        *,
        limit: int,
        cursor: UUID | None,
    ) -> CampaignPage:
        del tenant_id, campaign_ids, limit, cursor
        raise CampaignDirectoryUnavailable("Campaign directory is unavailable")


@dataclass(slots=True)
class SqlAlchemyCampaignDirectory:
    """Read active or draft campaigns through the tenant-scoped database session."""

    database: Database

    @staticmethod
    def _projection(campaign: Campaign) -> CampaignProjection:
        return CampaignProjection(
            id=campaign.id,
            tenant_id=campaign.tenant_id,
            slug=campaign.slug,
            name=campaign.name,
            jurisdiction=campaign.jurisdiction,
            stage=campaign.stage,
            status=campaign.status,
            version=campaign.version,
        )

    def get(self, tenant_id: UUID, campaign_id: UUID) -> CampaignProjection:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                campaign = session.scalar(
                    select(Campaign).where(
                        Campaign.id == campaign_id,
                        Campaign.tenant_id == tenant_id,
                        Campaign.status.in_(("DRAFT", "ACTIVE")),
                    )
                )
        except SQLAlchemyError as exc:
            raise CampaignDirectoryUnavailable("Campaign directory is unavailable") from exc

        if campaign is None:
            raise CampaignNotFound("Campaign was not found")
        return self._projection(campaign)

    def list_authorized(
        self,
        tenant_id: UUID,
        campaign_ids: tuple[UUID, ...],
        *,
        limit: int,
        cursor: UUID | None,
    ) -> CampaignPage:
        if not campaign_ids:
            return CampaignPage(items=(), next_cursor=None)

        try:
            with self.database.tenant_transaction(tenant_id) as session:
                statement = (
                    select(Campaign)
                    .where(
                        Campaign.tenant_id == tenant_id,
                        Campaign.id.in_(campaign_ids),
                        Campaign.status.in_(("DRAFT", "ACTIVE")),
                    )
                    .order_by(Campaign.id)
                    .limit(limit + 1)
                )
                if cursor is not None:
                    statement = statement.where(Campaign.id > cursor)
                rows = list(session.scalars(statement))
        except SQLAlchemyError as exc:
            raise CampaignDirectoryUnavailable("Campaign directory is unavailable") from exc

        has_more = len(rows) > limit
        page_rows = rows[:limit]
        next_cursor = page_rows[-1].id if has_more and page_rows else None
        return CampaignPage(
            items=tuple(self._projection(campaign) for campaign in page_rows),
            next_cursor=next_cursor,
        )
