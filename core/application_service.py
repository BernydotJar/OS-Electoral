#!/usr/bin/env python3
"""Bounded context: Read-Only Application Service Facade and Query Contracts."""
from __future__ import annotations

import re
from typing import Any

from core.repository_transaction import (
    WorkspaceRepository,
    CandidateBrandRepository,
    ApprovalLedgerRepository,
    DailyWorkflowRepository,
    PersistenceStoreRepository,
    RepositoryError
)
from core.audit_observability import AuditIntegrityReadModel

SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")


class ApplicationServiceError(ValueError):
    """Raised for service execution failures or missing resources."""
    pass


class ApplicationScopeError(ValueError):
    """Raised for tenant or campaign scope isolation breaches."""
    pass


class ReadOnlyApplicationService:
    def __init__(
        self,
        workspaces: WorkspaceRepository,
        brands: CandidateBrandRepository,
        ledgers: ApprovalLedgerRepository,
        workflows: DailyWorkflowRepository,
        stores: PersistenceStoreRepository
    ) -> None:
        self._workspaces = workspaces
        self._brands = brands
        self._ledgers = ledgers
        self._workflows = workflows
        self._stores = stores

    def _validate_scope(self, tenant_id: str, campaign_id: str, workspace_id: str) -> None:
        """Validate format of ids to prevent malformed queries or traversal attempts."""
        for field, val in [("tenant_id", tenant_id), ("campaign_id", campaign_id), ("workspace_id", workspace_id)]:
            if not isinstance(val, str) or SAFE_ID.fullmatch(val) is None:
                raise ApplicationScopeError(f"Invalid scope format for {field}: {val}")
        if not tenant_id.startswith("tenant:"):
            raise ApplicationScopeError("tenant_id namespace mismatch")
        if not campaign_id.startswith("campaign:"):
            raise ApplicationScopeError("campaign_id namespace mismatch")
        if not workspace_id.startswith("workspace:"):
            raise ApplicationScopeError("workspace_id namespace mismatch")

    def get_workspace_summary(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        self._validate_scope(tenant_id, campaign_id, workspace_id)
        try:
            ws = self._workspaces.get(tenant_id, campaign_id, workspace_id)
        except RepositoryError as exc:
            raise ApplicationServiceError(str(exc)) from exc

        # Cross-check scope inside aggregate
        if ws.get("tenant_id") != tenant_id or ws.get("campaign_id") != campaign_id or ws.get("workspace_id") != workspace_id:
            raise ApplicationScopeError("Cross-scope workspace retrieval rejected")

        return {
            "workspace_id": ws["workspace_id"],
            "name": ws["name"],
            "campaign_stage": ws["campaign_stage"],
            "objectives_count": len(ws.get("political_objectives", [])),
            "segments_count": len(ws.get("segments", [])),
            "evidence_count": len(ws.get("evidence", [])),
            "gate_statuses": {g["id"]: g["status"] for g in ws.get("gates", [])}
        }

    def get_candidate_brand_status(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        self._validate_scope(tenant_id, campaign_id, workspace_id)
        try:
            brand = self._brands.get(tenant_id, campaign_id, workspace_id)
        except RepositoryError as exc:
            raise ApplicationServiceError(str(exc)) from exc

        if brand.get("tenant_id") != tenant_id or brand.get("campaign_id") != campaign_id or brand.get("workspace_id") != workspace_id:
            raise ApplicationScopeError("Cross-scope candidate brand retrieval rejected")

        return {
            "brand_workspace_id": brand.get("brand_workspace_id"),
            "status": brand.get("status"),
            "identity_claim_status": brand.get("identity", {}).get("status", "UNKNOWN"),
            "biography_claim_status": brand.get("biography", {}).get("status", "UNKNOWN"),
            "purpose_claim_status": brand.get("purpose", {}).get("status", "UNKNOWN"),
            "reputation_claim_status": brand.get("reputation", {}).get("status", "UNKNOWN")
        }

    def get_pending_approvals(self, tenant_id: str, campaign_id: str, workspace_id: str) -> list[dict[str, Any]]:
        self._validate_scope(tenant_id, campaign_id, workspace_id)
        try:
            ledger = self._ledgers.get(tenant_id, campaign_id, workspace_id)
        except RepositoryError as exc:
            raise ApplicationServiceError(str(exc)) from exc

        if ledger.get("tenant_id") != tenant_id or ledger.get("campaign_id") != campaign_id or ledger.get("workspace_id") != workspace_id:
            raise ApplicationScopeError("Cross-scope approval ledger retrieval rejected")

        pending = []
        for req in ledger.get("requests", []):
            if req.get("status") == "PENDING":
                pending.append({
                    "id": req["id"],
                    "title": req["title"],
                    "scope_type": req["scope_type"],
                    "scope_id": req["scope_id"],
                    "required_roles": req["required_roles"]
                })
        return pending

    def get_daily_workflow_timeline(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        self._validate_scope(tenant_id, campaign_id, workspace_id)
        try:
            wf = self._workflows.get(tenant_id, campaign_id, workspace_id)
        except RepositoryError as exc:
            raise ApplicationServiceError(str(exc)) from exc

        if wf.get("tenant_id") != tenant_id or wf.get("campaign_id") != campaign_id or wf.get("workspace_id") != workspace_id:
            raise ApplicationScopeError("Cross-scope daily workflow retrieval rejected")

        return {
            "workflow_id": wf.get("workflow_id"),
            "date": wf.get("date"),
            "meetings_count": len(wf.get("meetings", [])),
            "assignments_count": len(wf.get("assignments", [])),
            "blocker_count": len(wf.get("blockers", []))
        }

    def get_audit_integrity_status(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        self._validate_scope(tenant_id, campaign_id, workspace_id)
        try:
            store = self._stores.get(tenant_id, campaign_id, workspace_id)
        except RepositoryError as exc:
            raise ApplicationServiceError(str(exc)) from exc

        if store.get("tenant_id") != tenant_id or store.get("campaign_id") != campaign_id or store.get("workspace_id") != workspace_id:
            raise ApplicationScopeError("Cross-scope persistence store retrieval rejected")

        read_model = AuditIntegrityReadModel(store)
        return read_model.verify_integrity()
