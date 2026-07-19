#!/usr/bin/env python3
"""Tenant-scoped repositories and fail-closed in-memory unit of work.

Repository reads return detached copies.  Dirty domain aggregates can be
committed only when exactly one authorized write intent is scoped to that
aggregate and carries the exact projected aggregate as its payload.  The
in-memory adapters expose snapshot/restore primitives so a late save failure
cannot leave a partial commit behind.
"""
from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any

from core.approval_ledger import validate_approval_state
from core.campaign_workspace import validate_workspace
from core.candidate_brand import validate_candidate_brand
from core.daily_workflow import validate_daily_workflow
from core.persistence_audit import apply_in_memory, plan_append, validate_store


ScopeKey = tuple[str, str, str]


class RepositoryError(ValueError):
    """Raised for data access violations or missing records."""


class TransactionError(ValueError):
    """Raised for concurrency, authorization, or integrity failures."""


def _scope_key(tenant_id: str, campaign_id: str, workspace_id: str) -> ScopeKey:
    return tenant_id, campaign_id, workspace_id


def _storage_key(tenant_id: str, campaign_id: str, workspace_id: str) -> str:
    return f"{tenant_id}:{campaign_id}:{workspace_id}"


class WorkspaceRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve a detached workspace copy or raise RepositoryError."""

    @abstractmethod
    def save(self, workspace: dict[str, Any]) -> None:
        """Validate and save a workspace."""


class CandidateBrandRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve a detached candidate-brand copy or raise RepositoryError."""

    @abstractmethod
    def save(self, brand: dict[str, Any], workspace: dict[str, Any]) -> None:
        """Validate and save a candidate brand."""


class ApprovalLedgerRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve a detached approval-ledger copy or raise RepositoryError."""

    @abstractmethod
    def save(self, ledger: dict[str, Any]) -> None:
        """Validate and save an approval ledger."""


class DailyWorkflowRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve a detached daily-workflow copy or raise RepositoryError."""

    @abstractmethod
    def save(self, workflow: dict[str, Any]) -> None:
        """Validate and save a daily workflow."""


class PersistenceStoreRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve a detached persistence-store copy or raise RepositoryError."""

    @abstractmethod
    def save(self, store: dict[str, Any]) -> None:
        """Validate and save a persistence audit store."""


class _AtomicInMemoryAdapter:
    """Snapshot support used only by the deterministic in-memory adapters."""

    _data: dict[str, dict[str, Any]]

    def _initialize(self, initial_data: dict[str, dict] | None) -> None:
        self._data = copy.deepcopy(initial_data or {})

    def _get_copy(self, tenant_id: str, campaign_id: str, workspace_id: str, label: str) -> dict[str, Any]:
        key = _storage_key(tenant_id, campaign_id, workspace_id)
        if key not in self._data:
            raise RepositoryError(f"{label} not found: {key}")
        return copy.deepcopy(self._data[key])

    def snapshot_state(self) -> dict[str, dict[str, Any]]:
        return copy.deepcopy(self._data)

    def restore_state(self, snapshot: dict[str, dict[str, Any]]) -> None:
        self._data = copy.deepcopy(snapshot)


class InMemoryWorkspaceRepository(_AtomicInMemoryAdapter, WorkspaceRepository):
    def __init__(self, initial_data: dict[str, dict] | None = None) -> None:
        self._initialize(initial_data)

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        return self._get_copy(tenant_id, campaign_id, workspace_id, "Workspace")

    def save(self, workspace: dict[str, Any]) -> None:
        validate_workspace(workspace)
        key = _storage_key(workspace["tenant_id"], workspace["campaign_id"], workspace["workspace_id"])
        self._data[key] = copy.deepcopy(workspace)


class InMemoryCandidateBrandRepository(_AtomicInMemoryAdapter, CandidateBrandRepository):
    def __init__(self, initial_data: dict[str, dict] | None = None) -> None:
        self._initialize(initial_data)

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        return self._get_copy(tenant_id, campaign_id, workspace_id, "Candidate brand workspace")

    def save(self, brand: dict[str, Any], workspace: dict[str, Any]) -> None:
        validate_candidate_brand(brand, workspace)
        key = _storage_key(brand["tenant_id"], brand["campaign_id"], brand["workspace_id"])
        self._data[key] = copy.deepcopy(brand)


class InMemoryApprovalLedgerRepository(_AtomicInMemoryAdapter, ApprovalLedgerRepository):
    def __init__(self, initial_data: dict[str, dict] | None = None) -> None:
        self._initialize(initial_data)

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        return self._get_copy(tenant_id, campaign_id, workspace_id, "Approval ledger")

    def save(self, ledger: dict[str, Any]) -> None:
        validate_approval_state(ledger)
        key = _storage_key(ledger["tenant_id"], ledger["campaign_id"], ledger["workspace_id"])
        self._data[key] = copy.deepcopy(ledger)


class InMemoryDailyWorkflowRepository(_AtomicInMemoryAdapter, DailyWorkflowRepository):
    def __init__(self, initial_data: dict[str, dict] | None = None) -> None:
        self._initialize(initial_data)

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        return self._get_copy(tenant_id, campaign_id, workspace_id, "Daily workflow")

    def save(self, workflow: dict[str, Any]) -> None:
        validate_daily_workflow(workflow)
        key = _storage_key(workflow["tenant_id"], workflow["campaign_id"], workflow["workspace_id"])
        self._data[key] = copy.deepcopy(workflow)


class InMemoryPersistenceStoreRepository(_AtomicInMemoryAdapter, PersistenceStoreRepository):
    def __init__(self, initial_data: dict[str, dict] | None = None) -> None:
        self._initialize(initial_data)

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        return self._get_copy(tenant_id, campaign_id, workspace_id, "Persistence store")

    def save(self, store: dict[str, Any]) -> None:
        validate_store(store)
        key = _storage_key(store["tenant_id"], store["campaign_id"], store["workspace_id"])
        self._data[key] = copy.deepcopy(store)


class UnitOfWork:
    RESOURCE_TYPES = {
        "workspace": "CAMPAIGN_WORKSPACE",
        "brand": "CANDIDATE_BRAND",
        "ledger": "APPROVAL_LEDGER",
        "workflow": "DAILY_WORKFLOW",
    }

    def __init__(
        self,
        workspaces: WorkspaceRepository,
        brands: CandidateBrandRepository,
        ledgers: ApprovalLedgerRepository,
        workflows: DailyWorkflowRepository,
        stores: PersistenceStoreRepository,
    ) -> None:
        self.workspaces = workspaces
        self.brands = brands
        self.ledgers = ledgers
        self.workflows = workflows
        self.stores = stores
        self._repositories = (workspaces, brands, ledgers, workflows, stores)

        self._loaded_workspaces: dict[ScopeKey, dict[str, Any]] = {}
        self._loaded_brands: dict[ScopeKey, dict[str, Any]] = {}
        self._loaded_ledgers: dict[ScopeKey, dict[str, Any]] = {}
        self._loaded_workflows: dict[ScopeKey, dict[str, Any]] = {}
        self._loaded_stores: dict[ScopeKey, dict[str, Any]] = {}

        self._original_workspaces: dict[ScopeKey, dict[str, Any]] = {}
        self._original_brands: dict[ScopeKey, dict[str, Any]] = {}
        self._original_ledgers: dict[ScopeKey, dict[str, Any]] = {}
        self._original_workflows: dict[ScopeKey, dict[str, Any]] = {}
        self._original_stores: dict[ScopeKey, dict[str, Any]] = {}

        self._intents: list[dict[str, Any]] = []
        self._authorizations: list[dict[str, Any]] = []
        self._committed = False
        self._rolled_back = False

    def load_workspace(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = _scope_key(tenant_id, campaign_id, workspace_id)
        if key not in self._loaded_workspaces:
            value = self.workspaces.get(*key)
            self._loaded_workspaces[key] = value
            self._original_workspaces[key] = copy.deepcopy(value)
        return self._loaded_workspaces[key]

    def load_brand(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = _scope_key(tenant_id, campaign_id, workspace_id)
        if key not in self._loaded_brands:
            value = self.brands.get(*key)
            self._loaded_brands[key] = value
            self._original_brands[key] = copy.deepcopy(value)
        return self._loaded_brands[key]

    def load_ledger(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = _scope_key(tenant_id, campaign_id, workspace_id)
        if key not in self._loaded_ledgers:
            value = self.ledgers.get(*key)
            self._loaded_ledgers[key] = value
            self._original_ledgers[key] = copy.deepcopy(value)
        return self._loaded_ledgers[key]

    def load_workflow(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = _scope_key(tenant_id, campaign_id, workspace_id)
        if key not in self._loaded_workflows:
            value = self.workflows.get(*key)
            self._loaded_workflows[key] = value
            self._original_workflows[key] = copy.deepcopy(value)
        return self._loaded_workflows[key]

    def load_store(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = _scope_key(tenant_id, campaign_id, workspace_id)
        if key not in self._loaded_stores:
            value = self.stores.get(*key)
            self._loaded_stores[key] = value
            self._original_stores[key] = copy.deepcopy(value)
        return self._loaded_stores[key]

    def register_intent(self, intent: dict[str, Any], authorization: dict[str, Any]) -> None:
        """Register one authorization decision with its exact write intent."""
        if not isinstance(intent, dict) or not isinstance(authorization, dict):
            raise TransactionError("write intent and authorization must be objects")
        self._intents.append(copy.deepcopy(intent))
        self._authorizations.append(copy.deepcopy(authorization))

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            self.rollback()
            return False
        if not self._committed and not self._rolled_back:
            self.commit()
        return False

    def _dirty_bindings(self) -> list[dict[str, Any]]:
        bindings: list[dict[str, Any]] = []
        collections = (
            ("workspace", self._loaded_workspaces, self._original_workspaces, "workspace_id"),
            ("brand", self._loaded_brands, self._original_brands, "brand_workspace_id"),
            ("ledger", self._loaded_ledgers, self._original_ledgers, "inbox_id"),
            ("workflow", self._loaded_workflows, self._original_workflows, "workflow_id"),
        )
        for kind, loaded, originals, id_field in collections:
            for key, aggregate in loaded.items():
                if aggregate != originals[key]:
                    bindings.append({
                        "kind": kind,
                        "scope": key,
                        "resource_type": self.RESOURCE_TYPES[kind],
                        "resource_id": aggregate[id_field],
                        "payload": aggregate,
                    })
        return bindings

    def _validate_loaded_identity_bindings(self) -> None:
        """Prevent a loaded aggregate from changing the key that authorized it."""
        collections = (
            ("workspace", self._loaded_workspaces, self._original_workspaces, "workspace_id"),
            ("brand", self._loaded_brands, self._original_brands, "brand_workspace_id"),
            ("ledger", self._loaded_ledgers, self._original_ledgers, "inbox_id"),
            ("workflow", self._loaded_workflows, self._original_workflows, "workflow_id"),
            ("store", self._loaded_stores, self._original_stores, "store_id"),
        )
        for kind, loaded, originals, id_field in collections:
            for key, aggregate in loaded.items():
                original = originals[key]
                aggregate_scope = _scope_key(
                    aggregate.get("tenant_id", ""),
                    aggregate.get("campaign_id", ""),
                    aggregate.get("workspace_id", ""),
                )
                original_scope = _scope_key(
                    original.get("tenant_id", ""),
                    original.get("campaign_id", ""),
                    original.get("workspace_id", ""),
                )
                if aggregate_scope != key or original_scope != key:
                    raise TransactionError(f"loaded {kind} scope identity does not match repository key")
                if aggregate.get(id_field) != original.get(id_field):
                    raise TransactionError(f"loaded {kind} resource identity is immutable")

    def _validate_dirty_intent_bindings(self, bindings: list[dict[str, Any]]) -> None:
        matched_indices: set[int] = set()
        for binding in bindings:
            matches = [
                index
                for index, intent in enumerate(self._intents)
                if _scope_key(
                    intent.get("tenant_id", ""),
                    intent.get("campaign_id", ""),
                    intent.get("workspace_id", ""),
                ) == binding["scope"]
                and intent.get("resource_type") == binding["resource_type"]
                and intent.get("resource_id") == binding["resource_id"]
            ]
            if len(matches) != 1:
                raise TransactionError(
                    f"dirty {binding['kind']} requires exactly one scoped authorization/write intent"
                )
            index = matches[0]
            intent = self._intents[index]
            if intent.get("operation") != "UPDATE_PROJECTION":
                raise TransactionError(f"dirty {binding['kind']} requires UPDATE_PROJECTION intent")
            if intent.get("payload") != binding["payload"]:
                raise TransactionError(f"dirty {binding['kind']} intent payload does not match projected aggregate")
            matched_indices.add(index)

        for index, intent in enumerate(self._intents):
            if intent.get("operation") == "UPDATE_PROJECTION" and index not in matched_indices:
                raise TransactionError("UPDATE_PROJECTION intent does not match exactly one dirty aggregate")

    def _validate_loaded_aggregates(self) -> None:
        for workspace in self._loaded_workspaces.values():
            validate_workspace(workspace)
        for workflow in self._loaded_workflows.values():
            validate_daily_workflow(workflow)
        for ledger in self._loaded_ledgers.values():
            validate_approval_state(ledger)
        for key, brand in self._loaded_brands.items():
            workspace = self._loaded_workspaces.get(key)
            if workspace is None:
                workspace = self.workspaces.get(*key)
            validate_candidate_brand(brand, workspace)

    def _snapshot_repositories(self) -> list[tuple[Any, Any]]:
        snapshots: list[tuple[Any, Any]] = []
        for repository in self._repositories:
            snapshot = getattr(repository, "snapshot_state", None)
            restore = getattr(repository, "restore_state", None)
            if not callable(snapshot) or not callable(restore):
                raise TransactionError("repository adapter lacks atomic snapshot/restore support")
            snapshots.append((repository, snapshot()))
        return snapshots

    @staticmethod
    def _restore_repositories(snapshots: list[tuple[Any, Any]]) -> list[str]:
        failures: list[str] = []
        for repository, snapshot in reversed(snapshots):
            try:
                repository.restore_state(snapshot)
            except Exception as exc:  # pragma: no cover - catastrophic adapter failure
                failures.append(f"{type(repository).__name__}: {exc}")
        return failures

    def commit(self) -> None:
        if self._committed:
            raise TransactionError("Transaction already committed")
        if self._rolled_back:
            raise TransactionError("Transaction already rolled back")

        snapshots: list[tuple[Any, Any]] = []
        try:
            self._validate_loaded_identity_bindings()
            for key, store in self._loaded_stores.items():
                if store != self._original_stores[key]:
                    raise TransactionError("persistence audit store cannot be modified directly")

            bindings = self._dirty_bindings()
            self._validate_loaded_aggregates()
            self._validate_dirty_intent_bindings(bindings)

            if len(self._intents) != len(self._authorizations):
                raise TransactionError("write intent and authorization registration count mismatch")
            for intent, authorization in zip(self._intents, self._authorizations):
                key = _scope_key(intent["tenant_id"], intent["campaign_id"], intent["workspace_id"])
                store = self.load_store(*key)
                plan = plan_append(store, intent, authorization)
                projected = apply_in_memory(store, plan)
                store.clear()
                store.update(projected)

            for store in self._loaded_stores.values():
                validate_store(store)

            snapshots = self._snapshot_repositories()
            for key, workspace in self._loaded_workspaces.items():
                if workspace != self._original_workspaces[key]:
                    self.workspaces.save(workspace)
            for key, brand in self._loaded_brands.items():
                if brand != self._original_brands[key]:
                    workspace = self._loaded_workspaces.get(key)
                    if workspace is None:
                        workspace = self.workspaces.get(*key)
                    self.brands.save(brand, workspace)
            for key, ledger in self._loaded_ledgers.items():
                if ledger != self._original_ledgers[key]:
                    self.ledgers.save(ledger)
            for key, workflow in self._loaded_workflows.items():
                if workflow != self._original_workflows[key]:
                    self.workflows.save(workflow)
            for key, store in self._loaded_stores.items():
                if store != self._original_stores[key]:
                    self.stores.save(store)

            self._committed = True
        except Exception as exc:
            restore_failures = self._restore_repositories(snapshots) if snapshots else []
            self.rollback()
            detail = f"; repository restore failures: {restore_failures}" if restore_failures else ""
            if isinstance(exc, TransactionError):
                raise TransactionError(f"Commit failed, transaction rolled back: {exc}{detail}") from exc
            raise TransactionError(f"Commit failed, transaction rolled back: {exc}{detail}") from exc

    def rollback(self) -> None:
        if self._committed or self._rolled_back:
            return
        collections = (
            (self._loaded_workspaces, self._original_workspaces),
            (self._loaded_brands, self._original_brands),
            (self._loaded_ledgers, self._original_ledgers),
            (self._loaded_workflows, self._original_workflows),
            (self._loaded_stores, self._original_stores),
        )
        for loaded, originals in collections:
            for key, value in loaded.items():
                value.clear()
                value.update(copy.deepcopy(originals[key]))
        self._rolled_back = True
