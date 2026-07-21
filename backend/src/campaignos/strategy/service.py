"""Strategy workspace service contracts and deterministic in-memory adapter."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from campaignos.strategy.contracts import (
    StrategyDecision,
    StrategyDecisionEvidence,
    StrategyDecisionRequest,
    StrategyWorkspaceAssessmentInput,
    StrategyWorkspaceCreate,
    StrategyWorkspaceCreateEvidence,
    StrategyWorkspaceProjection,
    StrategyWorkspaceReadEvidence,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceUpdateEvidence,
    assess_strategy_workspace,
)


class StrategyWorkspaceConflict(RuntimeError):
    """Raised when a campaign already owns a strategy workspace."""


class StrategyWorkspaceIdempotencyConflict(RuntimeError):
    """Raised when an idempotency key is reused with changed request or authority."""


class StrategyWorkspaceNotFound(RuntimeError):
    """Raised when the exact tenant/campaign strategy workspace is absent."""


class StrategyWorkspaceVersionConflict(RuntimeError):
    """Raised when a mutation uses a stale workspace version."""


class StrategyWorkspaceEvidenceConflict(RuntimeError):
    """Raised when evidence relationships fail deterministic governance rules."""


class StrategyWorkspaceUnavailable(RuntimeError):
    """Raised when the durable strategy adapter is unavailable."""


class StrategyPrerequisites(BaseModel):
    """Server-owned versions and team roles required before strategy work."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    campaign_version: int = Field(ge=1)
    campaign_status: str
    campaign_name: str
    candidate_workspace_version: int = Field(ge=1)
    team_workspace_version: int = Field(ge=1)
    known_role_ids: tuple[UUID, ...] = Field(min_length=1, max_length=100)


@dataclass(frozen=True)
class StrategyAuditRecord:
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    principal_id: UUID
    action: str
    resource_type: str
    resource_id: str
    purpose: str
    approval_receipt_id: str
    correlation_id: str
    payload: dict[str, object]
    occurred_at: datetime


@dataclass(frozen=True)
class StrategyOutboxRecord:
    id: UUID
    tenant_id: UUID
    topic: str
    payload: dict[str, object]
    occurred_at: datetime


@dataclass(frozen=True)
class _ReplayRecord:
    digest: str
    response: object


class StrategyWorkspaceService(Protocol):
    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: StrategyWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyWorkspaceCreateEvidence: ...

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
    ) -> StrategyWorkspaceReadEvidence: ...

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: StrategyWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyWorkspaceUpdateEvidence: ...

    def decide(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        request: StrategyDecisionRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyDecisionEvidence: ...


class UnavailableStrategyWorkspaceService:
    def _raise(self) -> None:
        raise StrategyWorkspaceUnavailable("Strategy workspace is unavailable")

    def create(self, *args: object, **kwargs: object) -> StrategyWorkspaceCreateEvidence:
        self._raise()
        raise AssertionError("unreachable")

    def get(self, *args: object, **kwargs: object) -> StrategyWorkspaceReadEvidence:
        self._raise()
        raise AssertionError("unreachable")

    def update(self, *args: object, **kwargs: object) -> StrategyWorkspaceUpdateEvidence:
        self._raise()
        raise AssertionError("unreachable")

    def decide(self, *args: object, **kwargs: object) -> StrategyDecisionEvidence:
        self._raise()
        raise AssertionError("unreachable")


class InMemoryStrategyWorkspaceService:
    """Thread-safe deterministic adapter used for domain and API contract tests."""

    def __init__(
        self,
        prerequisites: dict[tuple[UUID, UUID], StrategyPrerequisites] | None = None,
    ) -> None:
        self._prerequisites = prerequisites or {}
        self._workspaces: dict[tuple[UUID, UUID], StrategyWorkspaceAssessmentInput] = {}
        self._replays: dict[tuple[UUID, str, str], _ReplayRecord] = {}
        self._lock = RLock()
        self.audits: list[StrategyAuditRecord] = []
        self.outbox: list[StrategyOutboxRecord] = []
        self.decisions: list[StrategyDecision] = []

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _digest(
        *,
        operation: str,
        body: dict[str, object],
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
    ) -> str:
        encoded = json.dumps(
            {
                "operation": operation,
                "body": body,
                "principal_id": str(principal_id),
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
                "authorization_purpose": authorization_purpose,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _replay_or_conflict(
        self,
        *,
        tenant_id: UUID,
        operation: str,
        key: str,
        digest: str,
    ) -> object | None:
        existing = self._replays.get((tenant_id, operation, key))
        if existing is None:
            return None
        if existing.digest != digest:
            raise StrategyWorkspaceIdempotencyConflict(
                "Idempotency key was already used with different request or authority"
            )
        return existing.response

    def _record_replay(
        self,
        *,
        tenant_id: UUID,
        operation: str,
        key: str,
        digest: str,
        response: object,
    ) -> None:
        self._replays[(tenant_id, operation, key)] = _ReplayRecord(digest, response)

    def _prerequisite(self, tenant_id: UUID, campaign_id: UUID) -> StrategyPrerequisites:
        try:
            prerequisite = self._prerequisites[(tenant_id, campaign_id)]
        except KeyError as exc:
            raise StrategyWorkspaceNotFound(
                "Campaign strategy prerequisites are unavailable"
            ) from exc
        if prerequisite.campaign_status not in {"DRAFT", "ACTIVE"}:
            raise StrategyWorkspaceConflict("Campaign is not active for strategy work")
        return prerequisite

    def _projection(self, value: StrategyWorkspaceAssessmentInput) -> StrategyWorkspaceProjection:
        try:
            return assess_strategy_workspace(value)
        except ValueError as exc:
            raise StrategyWorkspaceEvidenceConflict(str(exc)) from exc

    def _audit(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        principal_id: UUID,
        action: str,
        resource_id: str,
        purpose: str,
        approval_receipt_id: str,
        correlation_id: str,
        payload: dict[str, object],
        now: datetime,
    ) -> StrategyAuditRecord:
        record = StrategyAuditRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            principal_id=principal_id,
            action=action,
            resource_type="strategy_workspace",
            resource_id=resource_id,
            purpose=purpose,
            approval_receipt_id=approval_receipt_id,
            correlation_id=correlation_id,
            payload=payload,
            occurred_at=now,
        )
        self.audits.append(record)
        return record

    def _outbox(
        self,
        *,
        tenant_id: UUID,
        topic: str,
        payload: dict[str, object],
        now: datetime,
    ) -> StrategyOutboxRecord:
        record = StrategyOutboxRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            topic=topic,
            payload={**payload, "external_effects": "NONE"},
            occurred_at=now,
        )
        self.outbox.append(record)
        return record

    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: StrategyWorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyWorkspaceCreateEvidence:
        operation = "strategy_workspace.create"
        digest = self._digest(
            operation=operation,
            body=request.model_dump(mode="json"),
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        with self._lock:
            replay = self._replay_or_conflict(
                tenant_id=tenant_id,
                operation=operation,
                key=idempotency_key,
                digest=digest,
            )
            if replay is not None:
                assert isinstance(replay, StrategyWorkspaceCreateEvidence)
                return replay
            aggregate_key = (tenant_id, campaign_id)
            if aggregate_key in self._workspaces:
                raise StrategyWorkspaceConflict("Strategy workspace already exists")
            prerequisite = self._prerequisite(tenant_id, campaign_id)
            now = self._now()
            aggregate = StrategyWorkspaceAssessmentInput(
                id=uuid4(),
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                campaign_version=prerequisite.campaign_version,
                campaign_status=prerequisite.campaign_status,
                campaign_name=prerequisite.campaign_name,
                candidate_workspace_version=prerequisite.candidate_workspace_version,
                team_workspace_version=prerequisite.team_workspace_version,
                known_role_ids=prerequisite.known_role_ids,
                title=request.title,
                version=1,
                created_at=now,
                updated_at=now,
            )
            projection = self._projection(aggregate)
            audit = self._audit(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=principal_id,
                action="create",
                resource_id=str(campaign_id),
                purpose=authorization_purpose,
                approval_receipt_id=approval_receipt_id,
                correlation_id=correlation_id,
                payload={
                    "workspace_id": str(aggregate.id),
                    "version": aggregate.version,
                    "authorization_grant_id": str(authorization_grant_id),
                },
                now=now,
            )
            outbox = self._outbox(
                tenant_id=tenant_id,
                topic="strategy.workspace.created",
                payload={
                    "campaign_id": str(campaign_id),
                    "workspace_id": str(aggregate.id),
                    "version": aggregate.version,
                },
                now=now,
            )
            response = StrategyWorkspaceCreateEvidence(
                workspace=projection,
                audit_event_id=audit.id,
                outbox_event_id=outbox.id,
            )
            self._workspaces[aggregate_key] = aggregate
            self._record_replay(
                tenant_id=tenant_id,
                operation=operation,
                key=idempotency_key,
                digest=digest,
                response=response,
            )
            return response

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
    ) -> StrategyWorkspaceReadEvidence:
        with self._lock:
            try:
                aggregate = self._workspaces[(tenant_id, campaign_id)]
            except KeyError as exc:
                raise StrategyWorkspaceNotFound("Strategy workspace was not found") from exc
            projection = self._projection(aggregate)
            audit = self._audit(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=principal_id,
                action="read",
                resource_id=str(campaign_id),
                purpose=authorization_purpose,
                approval_receipt_id=approval_receipt_id,
                correlation_id=correlation_id,
                payload={
                    "workspace_id": str(aggregate.id),
                    "version": aggregate.version,
                    "authorization_grant_id": str(authorization_grant_id),
                },
                now=self._now(),
            )
            return StrategyWorkspaceReadEvidence(
                workspace=projection,
                audit_event_id=audit.id,
            )

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: StrategyWorkspaceUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyWorkspaceUpdateEvidence:
        operation = "strategy_workspace.update"
        body = {
            "expected_version": expected_version,
            "changes": changes.model_dump(mode="json", exclude_unset=True),
        }
        digest = self._digest(
            operation=operation,
            body=body,
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        with self._lock:
            replay = self._replay_or_conflict(
                tenant_id=tenant_id,
                operation=operation,
                key=idempotency_key,
                digest=digest,
            )
            if replay is not None:
                assert isinstance(replay, StrategyWorkspaceUpdateEvidence)
                return replay
            aggregate_key = (tenant_id, campaign_id)
            try:
                current = self._workspaces[aggregate_key]
            except KeyError as exc:
                raise StrategyWorkspaceNotFound("Strategy workspace was not found") from exc
            if current.version != expected_version:
                raise StrategyWorkspaceVersionConflict("Strategy workspace version is stale")
            now = self._now()
            updated_payload = current.model_dump(mode="json")
            updated_payload.update(changes.model_dump(mode="json", exclude_unset=True))
            updated_payload.update(
                {
                    "decision": None,
                    "version": current.version + 1,
                    "updated_at": now,
                }
            )
            try:
                updated = StrategyWorkspaceAssessmentInput.model_validate(updated_payload)
                projection = assess_strategy_workspace(updated)
            except ValueError as exc:
                raise StrategyWorkspaceEvidenceConflict(str(exc)) from exc
            audit = self._audit(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=principal_id,
                action="update",
                resource_id=str(campaign_id),
                purpose=authorization_purpose,
                approval_receipt_id=approval_receipt_id,
                correlation_id=correlation_id,
                payload={
                    "workspace_id": str(current.id),
                    "before_version": current.version,
                    "after_version": updated.version,
                    "authorization_grant_id": str(authorization_grant_id),
                    "decision_invalidated": current.decision is not None,
                },
                now=now,
            )
            outbox = self._outbox(
                tenant_id=tenant_id,
                topic="strategy.workspace.updated",
                payload={
                    "campaign_id": str(campaign_id),
                    "workspace_id": str(current.id),
                    "version": updated.version,
                },
                now=now,
            )
            response = StrategyWorkspaceUpdateEvidence(
                workspace=projection,
                audit_event_id=audit.id,
                outbox_event_id=outbox.id,
            )
            self._workspaces[aggregate_key] = updated
            self._record_replay(
                tenant_id=tenant_id,
                operation=operation,
                key=idempotency_key,
                digest=digest,
                response=response,
            )
            return response

    def decide(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        request: StrategyDecisionRequest,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> StrategyDecisionEvidence:
        operation = "strategy_workspace.decide"
        body = {
            "expected_version": expected_version,
            "request": request.model_dump(mode="json"),
        }
        digest = self._digest(
            operation=operation,
            body=body,
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        with self._lock:
            replay = self._replay_or_conflict(
                tenant_id=tenant_id,
                operation=operation,
                key=idempotency_key,
                digest=digest,
            )
            if replay is not None:
                assert isinstance(replay, StrategyDecisionEvidence)
                return replay
            aggregate_key = (tenant_id, campaign_id)
            try:
                current = self._workspaces[aggregate_key]
            except KeyError as exc:
                raise StrategyWorkspaceNotFound("Strategy workspace was not found") from exc
            if current.version != expected_version:
                raise StrategyWorkspaceVersionConflict("Strategy workspace version is stale")
            if current.decision is not None:
                raise StrategyWorkspaceConflict(
                    "Current strategy workspace version already has a decision"
                )
            now = self._now()
            decision = StrategyDecision(
                id=uuid4(),
                workspace_version=current.version,
                selected_option_id=request.selected_option_id,
                reason=request.reason,
                human_role_id=request.human_role_id,
                approval_receipt_id=approval_receipt_id,
                decided_at=now,
            )
            decided_payload = current.model_dump(mode="json")
            decided_payload["decision"] = decision.model_dump(mode="json")
            try:
                decided = StrategyWorkspaceAssessmentInput.model_validate(decided_payload)
                projection = assess_strategy_workspace(decided)
            except ValueError as exc:
                raise StrategyWorkspaceEvidenceConflict(str(exc)) from exc
            audit = self._audit(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=principal_id,
                action="approve",
                resource_id=str(campaign_id),
                purpose=authorization_purpose,
                approval_receipt_id=approval_receipt_id,
                correlation_id=correlation_id,
                payload={
                    "workspace_id": str(current.id),
                    "workspace_version": current.version,
                    "selected_option_id": str(request.selected_option_id),
                    "human_role_id": str(request.human_role_id),
                    "authorization_grant_id": str(authorization_grant_id),
                    "authority_effect": "INTERNAL_DECISION_ONLY",
                },
                now=now,
            )
            outbox = self._outbox(
                tenant_id=tenant_id,
                topic="strategy.option.decided",
                payload={
                    "campaign_id": str(campaign_id),
                    "workspace_id": str(current.id),
                    "workspace_version": current.version,
                    "decision_id": str(decision.id),
                    "selected_option_id": str(request.selected_option_id),
                },
                now=now,
            )
            response = StrategyDecisionEvidence(
                workspace=projection,
                decision=decision,
                audit_event_id=audit.id,
                outbox_event_id=outbox.id,
            )
            self._workspaces[aggregate_key] = decided
            self.decisions.append(decision)
            self._record_replay(
                tenant_id=tenant_id,
                operation=operation,
                key=idempotency_key,
                digest=digest,
                response=response,
            )
            return response
