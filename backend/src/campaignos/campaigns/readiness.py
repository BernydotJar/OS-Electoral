"""Audited tenant-scoped campaign operational-readiness projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal, Protocol, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from campaignos.data.audit import (
    AuditScopeUnavailable,
    append_audit_event,
    lock_tenant_audit_stream,
)
from campaignos.data.database import Database
from campaignos.data.models import Campaign, Workspace

ReadinessCheckKey = Literal[
    "campaign_name",
    "jurisdiction",
    "campaign_stage",
    "active_workspace",
]
ReadinessStatus = Literal[
    "NEEDS_CAMPAIGN_METADATA",
    "NEEDS_CAMPAIGN_WORKSPACE",
    "READY_FOR_GUIDED_INTAKE",
]
ReadinessNextAction = Literal[
    "COMPLETE_CAMPAIGN_METADATA",
    "CREATE_CAMPAIGN_WORKSPACE",
    "BEGIN_GUIDED_INTAKE",
]


class CampaignReadinessNotFound(LookupError):
    """The campaign cannot be assessed in the selected tenant."""


class CampaignReadinessUnavailable(RuntimeError):
    """The readiness projection or mandatory audit append cannot complete."""


class CampaignReadinessInput(BaseModel):
    """Minimal persisted facts used by the deterministic readiness policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: str = Field(pattern="^(DRAFT|ACTIVE)$")
    name: str = Field(max_length=255)
    jurisdiction: str = Field(max_length=255)
    stage: str = Field(max_length=80)
    active_workspace_count: int = Field(ge=0)


class CampaignReadinessCheck(BaseModel):
    """One machine-readable operational setup check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: ReadinessCheckKey
    complete: bool
    reason_code: str = Field(min_length=1, max_length=100, pattern=r"^[A-Z0-9_]+$")


class CampaignReadinessProjection(BaseModel):
    """Operational readiness only; never a political or production approval."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: str = Field(pattern="^(DRAFT|ACTIVE)$")
    readiness_scope: Literal["OPERATIONAL_SETUP_ONLY"] = "OPERATIONAL_SETUP_ONLY"
    status: ReadinessStatus
    ready_for_guided_intake: bool
    completed_checks: int = Field(ge=0)
    total_checks: int = Field(ge=1)
    active_workspace_count: int = Field(ge=0)
    next_action: ReadinessNextAction
    checks: tuple[CampaignReadinessCheck, ...]
    limitation_codes: tuple[
        Literal[
            "NOT_A_HUMAN_APPROVAL",
            "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
        ],
        ...,
    ] = (
        "NOT_A_HUMAN_APPROVAL",
        "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
    )

    @model_validator(mode="after")
    def validate_summary(self) -> Self:
        if self.total_checks != len(self.checks):
            raise ValueError("total_checks must match checks")
        completed = sum(check.complete for check in self.checks)
        if self.completed_checks != completed:
            raise ValueError("completed_checks must match checks")
        keys = tuple(check.key for check in self.checks)
        if keys != (
            "campaign_name",
            "jurisdiction",
            "campaign_stage",
            "active_workspace",
        ):
            raise ValueError("readiness checks must use the canonical ordered policy")
        reason_codes = {
            ("campaign_name", True): "CAMPAIGN_NAME_PRESENT",
            ("campaign_name", False): "CAMPAIGN_NAME_MISSING",
            ("jurisdiction", True): "JURISDICTION_PRESENT",
            ("jurisdiction", False): "JURISDICTION_MISSING",
            ("campaign_stage", True): "CAMPAIGN_STAGE_PRESENT",
            ("campaign_stage", False): "CAMPAIGN_STAGE_MISSING",
            ("active_workspace", True): "ACTIVE_WORKSPACE_PRESENT",
            ("active_workspace", False): "ACTIVE_WORKSPACE_MISSING",
        }
        if any(
            check.reason_code != reason_codes[(check.key, check.complete)] for check in self.checks
        ):
            raise ValueError("readiness reason codes must match check outcomes")
        if self.checks[3].complete != (self.active_workspace_count > 0):
            raise ValueError("active workspace check must match active_workspace_count")

        metadata_complete = all(check.complete for check in self.checks[:3])
        workspace_complete = self.checks[3].complete
        if not metadata_complete:
            expected_status: ReadinessStatus = "NEEDS_CAMPAIGN_METADATA"
            expected_action: ReadinessNextAction = "COMPLETE_CAMPAIGN_METADATA"
        elif not workspace_complete:
            expected_status = "NEEDS_CAMPAIGN_WORKSPACE"
            expected_action = "CREATE_CAMPAIGN_WORKSPACE"
        else:
            expected_status = "READY_FOR_GUIDED_INTAKE"
            expected_action = "BEGIN_GUIDED_INTAKE"
        expected_ready = expected_status == "READY_FOR_GUIDED_INTAKE"
        if self.ready_for_guided_intake != expected_ready:
            raise ValueError("ready_for_guided_intake must match completed checks")
        if self.status != expected_status or self.next_action != expected_action:
            raise ValueError("status and next_action must match readiness checks")
        if self.limitation_codes != (
            "NOT_A_HUMAN_APPROVAL",
            "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
        ):
            raise ValueError("readiness limitations are mandatory")
        return self


class CampaignReadinessEvidence(BaseModel):
    """Readiness projection plus the committed audit receipt identifier."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    readiness: CampaignReadinessProjection
    audit_event_id: UUID


class CampaignReadinessReader(Protocol):
    """Assess one campaign and append mandatory read-audit evidence."""

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> CampaignReadinessEvidence:
        """Return an audited operational readiness projection or fail closed."""


class UnavailableCampaignReadinessReader:
    """Fail-closed reader used until persistence is configured."""

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        **kwargs: object,
    ) -> CampaignReadinessEvidence:
        del tenant_id, campaign_id, kwargs
        raise CampaignReadinessUnavailable("Campaign readiness is unavailable")


def assess_campaign_readiness(source: CampaignReadinessInput) -> CampaignReadinessProjection:
    """Apply the deterministic operational setup policy to persisted facts."""
    checks = (
        CampaignReadinessCheck(
            key="campaign_name",
            complete=bool(source.name.strip()),
            reason_code=(
                "CAMPAIGN_NAME_PRESENT" if source.name.strip() else "CAMPAIGN_NAME_MISSING"
            ),
        ),
        CampaignReadinessCheck(
            key="jurisdiction",
            complete=bool(source.jurisdiction.strip()),
            reason_code=(
                "JURISDICTION_PRESENT" if source.jurisdiction.strip() else "JURISDICTION_MISSING"
            ),
        ),
        CampaignReadinessCheck(
            key="campaign_stage",
            complete=bool(source.stage.strip()),
            reason_code=(
                "CAMPAIGN_STAGE_PRESENT" if source.stage.strip() else "CAMPAIGN_STAGE_MISSING"
            ),
        ),
        CampaignReadinessCheck(
            key="active_workspace",
            complete=source.active_workspace_count > 0,
            reason_code=(
                "ACTIVE_WORKSPACE_PRESENT"
                if source.active_workspace_count > 0
                else "ACTIVE_WORKSPACE_MISSING"
            ),
        ),
    )
    completed = sum(check.complete for check in checks)
    metadata_complete = all(check.complete for check in checks[:3])
    if not metadata_complete:
        status: ReadinessStatus = "NEEDS_CAMPAIGN_METADATA"
        next_action: ReadinessNextAction = "COMPLETE_CAMPAIGN_METADATA"
    elif not checks[3].complete:
        status = "NEEDS_CAMPAIGN_WORKSPACE"
        next_action = "CREATE_CAMPAIGN_WORKSPACE"
    else:
        status = "READY_FOR_GUIDED_INTAKE"
        next_action = "BEGIN_GUIDED_INTAKE"

    return CampaignReadinessProjection(
        tenant_id=source.tenant_id,
        campaign_id=source.campaign_id,
        campaign_version=source.campaign_version,
        campaign_status=source.campaign_status,
        status=status,
        ready_for_guided_intake=completed == len(checks),
        completed_checks=completed,
        total_checks=len(checks),
        active_workspace_count=source.active_workspace_count,
        next_action=next_action,
        checks=checks,
    )


@dataclass(frozen=True, slots=True)
class InMemoryCampaignReadinessAudit:
    audit_event_id: UUID
    tenant_id: UUID
    campaign_id: UUID
    principal_id: UUID
    authorization_grant_id: UUID
    approval_receipt_id: str
    authorization_purpose: str
    correlation_id: str
    occurred_at: datetime


@dataclass(slots=True)
class InMemoryCampaignReadinessReader:
    """Deterministic in-memory adapter retained for unit tests and local contracts."""

    snapshots: dict[tuple[UUID, UUID], CampaignReadinessInput]
    audit_events: list[InMemoryCampaignReadinessAudit] = field(default_factory=list)

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> CampaignReadinessEvidence:
        source = self.snapshots.get((tenant_id, campaign_id))
        if source is None:
            raise CampaignReadinessNotFound("Campaign was not found")
        if source.tenant_id != tenant_id or source.campaign_id != campaign_id:
            raise CampaignReadinessUnavailable("Campaign readiness scope is invalid")
        audit_event_id = uuid4()
        self.audit_events.append(
            InMemoryCampaignReadinessAudit(
                audit_event_id=audit_event_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                occurred_at=datetime.now(UTC),
            )
        )
        return CampaignReadinessEvidence(
            readiness=assess_campaign_readiness(source),
            audit_event_id=audit_event_id,
        )


@dataclass(slots=True)
class SqlAlchemyCampaignReadinessReader:
    """Read campaign setup facts and commit one append-only access audit."""

    database: Database

    def get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> CampaignReadinessEvidence:
        try:
            return self._get(
                tenant_id,
                campaign_id,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
            )
        except CampaignReadinessNotFound:
            raise
        except (AuditScopeUnavailable, SQLAlchemyError, ValidationError, ValueError) as exc:
            raise CampaignReadinessUnavailable("Campaign readiness is unavailable") from exc

    def _get(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> CampaignReadinessEvidence:
        with self.database.tenant_transaction(tenant_id) as session:
            # Acquire the audit-stream lock before reading so the recorded projection
            # is ordered consistently with other audited writes in this tenant.
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            campaign = session.scalar(
                select(Campaign).where(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == tenant_id,
                    Campaign.status.in_(("DRAFT", "ACTIVE")),
                )
            )
            if campaign is None:
                raise CampaignReadinessNotFound("Campaign was not found")
            active_workspace_count = int(
                session.scalar(
                    select(func.count(Workspace.id)).where(
                        Workspace.tenant_id == tenant_id,
                        Workspace.campaign_id == campaign_id,
                        Workspace.status == "ACTIVE",
                    )
                )
                or 0
            )
            readiness = assess_campaign_readiness(
                CampaignReadinessInput(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    campaign_version=campaign.version,
                    campaign_status=campaign.status,
                    name=campaign.name,
                    jurisdiction=campaign.jurisdiction,
                    stage=campaign.stage,
                    active_workspace_count=active_workspace_count,
                )
            )
            audit_append = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="campaign.readiness_viewed",
                resource_type="campaign_readiness",
                resource_id=str(campaign_id),
                payload={
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "campaign_version": readiness.campaign_version,
                    "readiness_status": readiness.status,
                    "completed_checks": readiness.completed_checks,
                    "total_checks": readiness.total_checks,
                    "active_workspace_count": readiness.active_workspace_count,
                    "external_effects": "NONE",
                },
            )
        return CampaignReadinessEvidence(
            readiness=readiness,
            audit_event_id=audit_append.event_id,
        )
