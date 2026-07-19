from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.repository_transaction import (
    InMemoryApprovalLedgerRepository,
    InMemoryCandidateBrandRepository,
    InMemoryDailyWorkflowRepository,
    InMemoryPersistenceStoreRepository,
    InMemoryWorkspaceRepository,
    RepositoryError,
    TransactionError,
    UnitOfWork,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class FailingPersistenceStoreRepository(InMemoryPersistenceStoreRepository):
    """Inject a late adapter failure after domain repositories have saved."""

    def save(self, store: dict) -> None:
        raise RuntimeError("injected late persistence-store failure")


class RepositoryTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace_raw = load("campaigns/antigua-guatemala/workspace.json")
        self.brand_raw = load("fixtures/candidate-brand/antigua-candidate-brand.json")
        self.ledger_raw = load("fixtures/approval-ledger/antigua.json")
        self.workflow_raw = load("fixtures/daily-workflow/antigua.json")
        self.store_raw = load("fixtures/persistence/antigua-store.json")
        self.intent_raw = load("fixtures/persistence/antigua-write-intent.json")
        self.auth_raw = load("fixtures/persistence/antigua-authorization.json")
        self.t = "tenant:bernydotjar"
        self.c = "campaign:antigua-guatemala-exploratory"
        self.w = "workspace:antigua-2026"
        self.key = f"{self.t}:{self.c}:{self.w}"
        self._make_repositories()

    def _make_repositories(self, store_type=InMemoryPersistenceStoreRepository) -> None:
        self.workspace_repo = InMemoryWorkspaceRepository({self.key: self.workspace_raw})
        self.brand_repo = InMemoryCandidateBrandRepository({self.key: self.brand_raw})
        self.ledger_repo = InMemoryApprovalLedgerRepository({self.key: self.ledger_raw})
        self.workflow_repo = InMemoryDailyWorkflowRepository({self.key: self.workflow_raw})
        self.store_repo = store_type({self.key: self.store_raw})

    def uow(self) -> UnitOfWork:
        return UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo,
        )

    def linked_write(self, aggregate: dict, resource_type: str, resource_id: str, suffix: str) -> tuple[dict, dict]:
        intent = copy.deepcopy(self.intent_raw)
        request_id = f"auth-request:{suffix}"
        intent.update(
            intent_id=f"write-intent:{suffix}",
            idempotency_key=f"idem:{suffix}",
            authorization_request_id=request_id,
            operation="UPDATE_PROJECTION",
            required_permission="UPDATE_INTERNAL_PROJECTION",
            resource_type=resource_type,
            resource_id=resource_id,
            payload=copy.deepcopy(aggregate),
        )
        authorization = copy.deepcopy(self.auth_raw)
        authorization.update(request_id=request_id)
        authorization["permission"] = "UPDATE_INTERNAL_PROJECTION"
        authorization["resource"] = {"type": resource_type, "id": resource_id}
        return intent, authorization

    def test_repository_get_and_save_success(self) -> None:
        workspace = self.workspace_repo.get(self.t, self.c, self.w)
        workspace["name"] = "Modified Antigua Name"
        self.workspace_repo.save(workspace)
        self.assertEqual(self.workspace_repo.get(self.t, self.c, self.w)["name"], "Modified Antigua Name")

    def test_repository_get_returns_detached_copy(self) -> None:
        workspace = self.workspace_repo.get(self.t, self.c, self.w)
        workspace["name"] = "MUTATED OUTSIDE REPOSITORY"
        persisted = self.workspace_repo.get(self.t, self.c, self.w)
        self.assertEqual(persisted["name"], self.workspace_raw["name"])

        store = self.store_repo.get(self.t, self.c, self.w)
        store["metadata"]["tampered"] = True
        self.assertNotIn("tampered", self.store_repo.get(self.t, self.c, self.w)["metadata"])

    def test_repository_initial_data_is_detached_from_caller(self) -> None:
        self.workspace_raw["name"] = "CALLER MUTATION"
        self.assertNotEqual(self.workspace_repo.get(self.t, self.c, self.w)["name"], "CALLER MUTATION")

    def test_repository_get_not_found_raises_repository_error(self) -> None:
        with self.assertRaises(RepositoryError):
            self.workspace_repo.get("tenant:other", "campaign:other", "workspace:other")

    def test_standalone_authorized_intent_is_audited(self) -> None:
        with self.uow() as unit:
            self.assertEqual(unit.load_store(self.t, self.c, self.w)["aggregate_version"], 0)
            unit.register_intent(self.intent_raw, self.auth_raw)

        persisted = self.store_repo.get(self.t, self.c, self.w)
        self.assertEqual(persisted["aggregate_version"], 1)
        self.assertEqual(len(persisted["events"]), 1)
        self.assertEqual(persisted["idempotency_keys"], [self.intent_raw["idempotency_key"]])

    def test_dirty_aggregate_without_intent_is_rejected_and_not_audited(self) -> None:
        unit = self.uow()
        unit.load_workspace(self.t, self.c, self.w)["name"] = "UNAUTHORIZED-BUT-COMMITTED"
        with self.assertRaisesRegex(TransactionError, "exactly one scoped authorization/write intent"):
            unit.commit()
        self.assertEqual(self.workspace_repo.get(self.t, self.c, self.w)["name"], self.workspace_raw["name"])
        self.assertEqual(self.store_repo.get(self.t, self.c, self.w)["aggregate_version"], 0)

    def test_dirty_aggregate_requires_exact_payload_binding(self) -> None:
        unit = self.uow()
        workspace = unit.load_workspace(self.t, self.c, self.w)
        workspace["name"] = "Projected Name"
        stale_payload = copy.deepcopy(workspace)
        stale_payload["name"] = "Different Payload"
        intent, authorization = self.linked_write(
            stale_payload,
            "CAMPAIGN_WORKSPACE",
            self.w,
            "workspace-payload-mismatch",
        )
        unit.register_intent(intent, authorization)
        with self.assertRaisesRegex(TransactionError, "payload does not match"):
            unit.commit()
        self.assertEqual(self.workspace_repo.get(self.t, self.c, self.w)["name"], self.workspace_raw["name"])

    def test_loaded_scope_and_resource_identity_are_immutable(self) -> None:
        mutations = (
            ("tenant_id", "tenant:other", "scope identity"),
            ("campaign_id", "campaign:other", "scope identity"),
            ("workspace_id", "workspace:other", "scope identity"),
        )
        for field, value, message in mutations:
            with self.subTest(field=field):
                unit = self.uow()
                workspace = unit.load_workspace(self.t, self.c, self.w)
                workspace[field] = value
                with self.assertRaisesRegex(TransactionError, message):
                    unit.commit()

        unit = self.uow()
        brand = unit.load_brand(self.t, self.c, self.w)
        brand["brand_workspace_id"] = "brand-workspace:different"
        with self.assertRaisesRegex(TransactionError, "resource identity is immutable"):
            unit.commit()

    def test_update_projection_requires_operation_specific_permission(self) -> None:
        unit = self.uow()
        workspace = unit.load_workspace(self.t, self.c, self.w)
        workspace["name"] = "Permission-bound update"
        intent, authorization = self.linked_write(
            workspace,
            "CAMPAIGN_WORKSPACE",
            self.w,
            "workspace-wrong-permission",
        )
        intent["required_permission"] = "CREATE_DRAFT"
        authorization["permission"] = "CREATE_DRAFT"
        unit.register_intent(intent, authorization)
        with self.assertRaisesRegex(TransactionError, "permission does not match operation"):
            unit.commit()

    def test_authorized_workspace_projection_commits_with_audit(self) -> None:
        unit = self.uow()
        workspace = unit.load_workspace(self.t, self.c, self.w)
        workspace["name"] = "Authorized Projected Name"
        intent, authorization = self.linked_write(
            workspace,
            "CAMPAIGN_WORKSPACE",
            self.w,
            "workspace-authorized-update",
        )
        unit.register_intent(intent, authorization)
        unit.commit()
        self.assertEqual(self.workspace_repo.get(self.t, self.c, self.w)["name"], "Authorized Projected Name")
        event = self.store_repo.get(self.t, self.c, self.w)["events"][0]
        self.assertEqual(event["resource_type"], "CAMPAIGN_WORKSPACE")
        self.assertEqual(event["resource_id"], self.w)

    def test_brand_only_commit_handles_namespaced_scope_ids(self) -> None:
        unit = self.uow()
        brand = unit.load_brand(self.t, self.c, self.w)
        brand["status"] = "UNDER_REVIEW"
        intent, authorization = self.linked_write(
            brand,
            "CANDIDATE_BRAND",
            brand["brand_workspace_id"],
            "brand-only-update",
        )
        unit.register_intent(intent, authorization)
        unit.commit()
        self.assertEqual(self.brand_repo.get(self.t, self.c, self.w)["status"], "UNDER_REVIEW")
        self.assertEqual(self.store_repo.get(self.t, self.c, self.w)["aggregate_version"], 1)

    def test_late_save_failure_restores_every_repository_atomically(self) -> None:
        self._make_repositories(FailingPersistenceStoreRepository)
        unit = self.uow()
        workspace = unit.load_workspace(self.t, self.c, self.w)
        workspace["name"] = "PARTIAL-COMMIT-MUST-NOT-SURVIVE"
        intent, authorization = self.linked_write(
            workspace,
            "CAMPAIGN_WORKSPACE",
            self.w,
            "atomic-late-failure",
        )
        unit.register_intent(intent, authorization)
        with self.assertRaisesRegex(TransactionError, "injected late persistence-store failure"):
            unit.commit()
        self.assertEqual(self.workspace_repo.get(self.t, self.c, self.w)["name"], self.workspace_raw["name"])
        self.assertEqual(self.store_repo.get(self.t, self.c, self.w)["aggregate_version"], 0)

    def test_direct_audit_store_mutation_is_rejected(self) -> None:
        unit = self.uow()
        unit.load_store(self.t, self.c, self.w)["metadata"]["tampered"] = True
        with self.assertRaisesRegex(TransactionError, "cannot be modified directly"):
            unit.commit()
        self.assertNotIn("tampered", self.store_repo.get(self.t, self.c, self.w)["metadata"])

    def test_transaction_rollback_on_exception(self) -> None:
        try:
            with self.uow() as unit:
                unit.load_workspace(self.t, self.c, self.w)["name"] = "Mutated inside UOW"
                raise RuntimeError("Force failure")
        except RuntimeError:
            pass
        self.assertEqual(self.workspace_repo.get(self.t, self.c, self.w)["name"], self.workspace_raw["name"])

    def test_transaction_cross_aggregate_validation_failure(self) -> None:
        unit = self.uow()
        brand = unit.load_brand(self.t, self.c, self.w)
        brand["identity"]["psychological_profile"] = "illegal"
        intent, authorization = self.linked_write(
            brand,
            "CANDIDATE_BRAND",
            brand["brand_workspace_id"],
            "invalid-brand-update",
        )
        unit.register_intent(intent, authorization)
        with self.assertRaises(TransactionError):
            unit.commit()
        self.assertNotIn(
            "psychological_profile",
            self.brand_repo.get(self.t, self.c, self.w)["identity"],
        )

    def test_transaction_double_commit_raises_transaction_error(self) -> None:
        unit = self.uow()
        unit.commit()
        with self.assertRaisesRegex(TransactionError, "already committed"):
            unit.commit()


if __name__ == "__main__":
    unittest.main()
