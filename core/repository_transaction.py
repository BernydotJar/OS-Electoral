#!/usr/bin/env python3
"""Bounded context: Tenant-scoped Repository Interfaces and Unit of Work Transaction Boundary."""
from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any

from core.campaign_workspace import validate_workspace
from core.candidate_brand import validate_candidate_brand
from core.approval_ledger import validate_approval_state
from core.daily_workflow import validate_daily_workflow
from core.persistence_audit import plan_append, apply_in_memory, validate_store


class RepositoryError(ValueError):
    """Raised for data access violations or missing records."""
    pass


class TransactionError(ValueError):
    """Raised for concurrency, authorization, or integrity errors during transaction commit."""
    pass


# --- Repository Interfaces ---

class WorkspaceRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve workspace. Must raise RepositoryError if not found."""
        pass

    @abstractmethod
    def save(self, workspace: dict[str, Any]) -> None:
        """Save workspace. Must run validate_workspace beforehand."""
        pass


class CandidateBrandRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve candidate brand. Must raise RepositoryError if not found."""
        pass

    @abstractmethod
    def save(self, brand: dict[str, Any], workspace: dict[str, Any]) -> None:
        """Save candidate brand. Must run validate_candidate_brand beforehand."""
        pass


class ApprovalLedgerRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve approval ledger. Must raise RepositoryError if not found."""
        pass

    @abstractmethod
    def save(self, ledger: dict[str, Any]) -> None:
        """Save approval ledger. Must run validate_approval_state beforehand."""
        pass


class DailyWorkflowRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve daily operating workflow. Must raise RepositoryError if not found."""
        pass

    @abstractmethod
    def save(self, workflow: dict[str, Any]) -> None:
        """Save daily workflow. Must run validate_daily_workflow beforehand."""
        pass


class PersistenceStoreRepository(ABC):
    @abstractmethod
    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        """Retrieve persistence audit store. Must raise RepositoryError if not found."""
        pass

    @abstractmethod
    def save(self, store: dict[str, Any]) -> None:
        """Save persistence audit store. Must run validate_store beforehand."""
        pass


# --- Concrete In-Memory Implementations ---

class InMemoryWorkspaceRepository(WorkspaceRepository):
    def __init__(self, initial_data: dict[str, dict] = None) -> None:
        self._data = initial_data or {}

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._data:
            raise RepositoryError(f"Workspace not found: {key}")
        return self._data[key]

    def save(self, workspace: dict[str, Any]) -> None:
        validate_workspace(workspace)
        key = f"{workspace['tenant_id']}:{workspace['campaign_id']}:{workspace['workspace_id']}"
        self._data[key] = copy.deepcopy(workspace)


class InMemoryCandidateBrandRepository(CandidateBrandRepository):
    def __init__(self, initial_data: dict[str, dict] = None) -> None:
        self._data = initial_data or {}

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._data:
            raise RepositoryError(f"Candidate brand workspace not found: {key}")
        return self._data[key]

    def save(self, brand: dict[str, Any], workspace: dict[str, Any]) -> None:
        validate_candidate_brand(brand, workspace)
        key = f"{brand['tenant_id']}:{brand['campaign_id']}:{brand['workspace_id']}"
        self._data[key] = copy.deepcopy(brand)


class InMemoryApprovalLedgerRepository(ApprovalLedgerRepository):
    def __init__(self, initial_data: dict[str, dict] = None) -> None:
        self._data = initial_data or {}

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._data:
            raise RepositoryError(f"Approval ledger not found: {key}")
        return self._data[key]

    def save(self, ledger: dict[str, Any]) -> None:
        validate_approval_state(ledger)
        key = f"{ledger['tenant_id']}:{ledger['campaign_id']}:{ledger['workspace_id']}"
        self._data[key] = copy.deepcopy(ledger)


class InMemoryDailyWorkflowRepository(DailyWorkflowRepository):
    def __init__(self, initial_data: dict[str, dict] = None) -> None:
        self._data = initial_data or {}

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._data:
            raise RepositoryError(f"Daily workflow not found: {key}")
        return self._data[key]

    def save(self, workflow: dict[str, Any]) -> None:
        validate_daily_workflow(workflow)
        key = f"{workflow['tenant_id']}:{workflow['campaign_id']}:{workflow['workspace_id']}"
        self._data[key] = copy.deepcopy(workflow)


class InMemoryPersistenceStoreRepository(PersistenceStoreRepository):
    def __init__(self, initial_data: dict[str, dict] = None) -> None:
        self._data = initial_data or {}

    def get(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._data:
            raise RepositoryError(f"Persistence store not found: {key}")
        return self._data[key]

    def save(self, store: dict[str, Any]) -> None:
        validate_store(store)
        key = f"{store['tenant_id']}:{store['campaign_id']}:{store['workspace_id']}"
        self._data[key] = copy.deepcopy(store)


# --- Unit of Work Context Manager ---

class UnitOfWork:
    def __init__(
        self,
        workspaces: WorkspaceRepository,
        brands: CandidateBrandRepository,
        ledgers: ApprovalLedgerRepository,
        workflows: DailyWorkflowRepository,
        stores: PersistenceStoreRepository
    ) -> None:
        self.workspaces = workspaces
        self.brands = brands
        self.ledgers = ledgers
        self.workflows = workflows
        self.stores = stores

        self._loaded_workspaces: dict[str, dict] = {}
        self._loaded_brands: dict[str, dict] = {}
        self._loaded_ledgers: dict[str, dict] = {}
        self._loaded_workflows: dict[str, dict] = {}
        self._loaded_stores: dict[str, dict] = {}

        self._original_workspaces: dict[str, dict] = {}
        self._original_brands: dict[str, dict] = {}
        self._original_ledgers: dict[str, dict] = {}
        self._original_workflows: dict[str, dict] = {}
        self._original_stores: dict[str, dict] = {}

        self._intents: list[dict] = []
        self._authorizations: list[dict] = []
        self._committed = False
        self._rolled_back = False

    def load_workspace(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._loaded_workspaces:
            ws = self.workspaces.get(tenant_id, campaign_id, workspace_id)
            self._loaded_workspaces[key] = ws
            self._original_workspaces[key] = copy.deepcopy(ws)
        return self._loaded_workspaces[key]

    def load_brand(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._loaded_brands:
            brand = self.brands.get(tenant_id, campaign_id, workspace_id)
            self._loaded_brands[key] = brand
            self._original_brands[key] = copy.deepcopy(brand)
        return self._loaded_brands[key]

    def load_ledger(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._loaded_ledgers:
            ledger = self.ledgers.get(tenant_id, campaign_id, workspace_id)
            self._loaded_ledgers[key] = ledger
            self._original_ledgers[key] = copy.deepcopy(ledger)
        return self._loaded_ledgers[key]

    def load_workflow(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._loaded_workflows:
            wf = self.workflows.get(tenant_id, campaign_id, workspace_id)
            self._loaded_workflows[key] = wf
            self._original_workflows[key] = copy.deepcopy(wf)
        return self._loaded_workflows[key]

    def load_store(self, tenant_id: str, campaign_id: str, workspace_id: str) -> dict[str, Any]:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        if key not in self._loaded_stores:
            store = self.stores.get(tenant_id, campaign_id, workspace_id)
            self._loaded_stores[key] = store
            self._original_stores[key] = copy.deepcopy(store)
        return self._loaded_stores[key]

    def register_intent(self, intent: dict, authorization: dict) -> None:
        """Register a write intent and authorization to back any modifications during commit."""
        self._intents.append(copy.deepcopy(intent))
        self._authorizations.append(copy.deepcopy(authorization))

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            self.rollback()
            return False  # Propagate exception
        if not self._committed and not self._rolled_back:
            self.commit()
        return True

    def commit(self) -> None:
        if self._committed:
            raise TransactionError("Transaction already committed")
        if self._rolled_back:
            raise TransactionError("Transaction already rolled back")

        try:
            # 1. Process and apply all registered write intents
            for intent, auth in zip(self._intents, self._authorizations):
                tenant = intent["tenant_id"]
                campaign = intent["campaign_id"]
                workspace = intent["workspace_id"]
                store = self.load_store(tenant, campaign, workspace)

                # Validate and plan via pure persistence boundary
                plan = plan_append(store, intent, auth)
                projected = apply_in_memory(store, plan)

                # Apply mutations in-place to the store reference
                store.clear()
                store.update(projected)

            # 2. Validate all modified aggregates (including cross-aggregate checks)
            # Validate workspaces
            for ws in self._loaded_workspaces.values():
                validate_workspace(ws)

            # Validate daily workflows
            for wf in self._loaded_workflows.values():
                validate_daily_workflow(wf)

            # Validate approval ledgers
            for ledger in self._loaded_ledgers.values():
                validate_approval_state(ledger)

            # Validate candidate brands (requires cross-aggregate checks with workspaces)
            for key, brand in self._loaded_brands.items():
                ws = self._loaded_workspaces.get(key)
                if ws is None:
                    tenant, campaign, workspace = key.split(":")
                    ws = self.workspaces.get(tenant, campaign, workspace)
                validate_candidate_brand(brand, ws)

            # Validate stores
            for store in self._loaded_stores.values():
                validate_store(store)

            # 3. Save all updated aggregates back to repositories
            for key, ws in self._loaded_workspaces.items():
                if ws != self._original_workspaces[key]:
                    self.workspaces.save(ws)

            for key, brand in self._loaded_brands.items():
                if brand != self._original_brands[key]:
                    # Find corresponding workspace
                    ws = self._loaded_workspaces.get(key)
                    if ws is None:
                        tenant, campaign, workspace = key.split(":")
                        ws = self.workspaces.get(tenant, campaign, workspace)
                    self.brands.save(brand, ws)

            for key, ledger in self._loaded_ledgers.items():
                if ledger != self._original_ledgers[key]:
                    self.ledgers.save(ledger)

            for key, wf in self._loaded_workflows.items():
                if wf != self._original_workflows[key]:
                    self.workflows.save(wf)

            for key, store in self._loaded_stores.items():
                if store != self._original_stores[key]:
                    self.stores.save(store)

            self._committed = True
        except Exception as exc:
            self.rollback()
            raise TransactionError(f"Commit failed, transaction rolled back: {exc}") from exc

    def rollback(self) -> None:
        if self._committed or self._rolled_back:
            return

        # Restore all in-memory loaded dictionaries to their pre-transaction states
        for key, ws in self._loaded_workspaces.items():
            ws.clear()
            ws.update(self._original_workspaces[key])
        for key, brand in self._loaded_brands.items():
            brand.clear()
            brand.update(self._original_brands[key])
        for key, ledger in self._loaded_ledgers.items():
            ledger.clear()
            ledger.update(self._original_ledgers[key])
        for key, wf in self._loaded_workflows.items():
            wf.clear()
            wf.update(self._original_workflows[key])
        for key, store in self._loaded_stores.items():
            store.clear()
            store.update(self._original_stores[key])

        self._rolled_back = True
