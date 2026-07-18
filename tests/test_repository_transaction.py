from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.repository_transaction import (
    InMemoryWorkspaceRepository,
    InMemoryCandidateBrandRepository,
    InMemoryApprovalLedgerRepository,
    InMemoryDailyWorkflowRepository,
    InMemoryPersistenceStoreRepository,
    UnitOfWork,
    RepositoryError,
    TransactionError
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class RepositoryTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        # Load Antigua fixtures
        self.workspace_raw = load("campaigns/antigua-guatemala/workspace.json")
        self.brand_raw = load("fixtures/candidate-brand/antigua-candidate-brand.json")
        self.ledger_raw = load("fixtures/approval-ledger/antigua.json")
        self.workflow_raw = load("fixtures/daily-workflow/antigua.json")
        self.store_raw = load("fixtures/persistence/antigua-store.json")
        self.intent_raw = load("fixtures/persistence/antigua-write-intent.json")
        self.auth_raw = load("fixtures/persistence/antigua-authorization.json")

        # Initialize repositories with Antigua data
        t, c, w = "tenant:bernydotjar", "campaign:antigua-guatemala-exploratory", "workspace:antigua-2026"
        key = f"{t}:{c}:{w}"
        
        self.workspace_repo = InMemoryWorkspaceRepository({key: copy.deepcopy(self.workspace_raw)})
        self.brand_repo = InMemoryCandidateBrandRepository({key: copy.deepcopy(self.brand_raw)})
        self.ledger_repo = InMemoryApprovalLedgerRepository({key: copy.deepcopy(self.ledger_raw)})
        self.workflow_repo = InMemoryDailyWorkflowRepository({key: copy.deepcopy(self.workflow_raw)})
        self.store_repo = InMemoryPersistenceStoreRepository({key: copy.deepcopy(self.store_raw)})

    def test_repository_get_and_save_success(self) -> None:
        t, c, w = "tenant:bernydotjar", "campaign:antigua-guatemala-exploratory", "workspace:antigua-2026"
        ws = self.workspace_repo.get(t, c, w)
        self.assertEqual(ws["workspace_id"], w)

        ws_mod = copy.deepcopy(ws)
        ws_mod["name"] = "Modified Antigua Name"
        self.workspace_repo.save(ws_mod)
        self.assertEqual(self.workspace_repo.get(t, c, w)["name"], "Modified Antigua Name")

    def test_repository_get_not_found_raises_repository_error(self) -> None:
        with self.assertRaises(RepositoryError):
            self.workspace_repo.get("tenant:other", "campaign:other", "workspace:other")

    def test_transaction_commit_success(self) -> None:
        t, c, w = "tenant:bernydotjar", "campaign:antigua-guatemala-exploratory", "workspace:antigua-2026"
        
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )
        
        with uow:
            # Load store and register intent
            store = uow.load_store(t, c, w)
            self.assertEqual(store["aggregate_version"], 0)
            uow.register_intent(self.intent_raw, self.auth_raw)
            # Commit will automatically plan and apply the write intent in memory
            
        # Verify the changes are persisted in the repository's store
        persisted_store = self.store_repo.get(t, c, w)
        self.assertEqual(persisted_store["aggregate_version"], 1)
        self.assertEqual(len(persisted_store["events"]), 1)
        self.assertEqual(persisted_store["idempotency_keys"], [self.intent_raw["idempotency_key"]])

    def test_transaction_rollback_on_exception(self) -> None:
        t, c, w = "tenant:bernydotjar", "campaign:antigua-guatemala-exploratory", "workspace:antigua-2026"
        
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )
        
        ws = self.workspace_repo.get(t, c, w)
        original_name = ws["name"]

        try:
            with uow:
                ws_loaded = uow.load_workspace(t, c, w)
                ws_loaded["name"] = "Mutated name inside UOW"
                raise RuntimeError("Force failure")
        except RuntimeError:
            pass

        # Verify that UOW rolled back and did not modify the repository data
        self.assertEqual(self.workspace_repo.get(t, c, w)["name"], original_name)
        # Verify the in-memory loaded reference was restored
        self.assertEqual(ws["name"], original_name)

    def test_transaction_cross_aggregate_validation_failure(self) -> None:
        t, c, w = "tenant:bernydotjar", "campaign:antigua-guatemala-exploratory", "workspace:antigua-2026"
        
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )

        with self.assertRaises(TransactionError):
            with uow:
                brand = uow.load_brand(t, c, w)
                # Introduce prohibited field into brand to fail validate_candidate_brand
                brand["identity"]["psychological_profile"] = "illegal"

        # Verify that changes were rolled back and the brand was restored
        restored_brand = self.brand_repo.get(t, c, w)
        self.assertNotIn("psychological_profile", restored_brand["identity"])

    def test_transaction_double_commit_raises_transaction_error(self) -> None:
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )
        uow.commit()
        with self.assertRaisesRegex(TransactionError, "already committed"):
            uow.commit()


if __name__ == "__main__":
    unittest.main()
