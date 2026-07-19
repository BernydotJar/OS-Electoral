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
from core.application_service import (
    ReadOnlyApplicationService,
    ApplicationServiceError,
    ApplicationScopeError
)
from core.persistence_audit import event_hash

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class CorruptiblePersistenceStoreRepository(InMemoryPersistenceStoreRepository):
    """Test-only bypass used to model corruption below the repository API."""

    def inject_corruption_for_test(self, tenant_id: str, campaign_id: str, workspace_id: str) -> None:
        key = f"{tenant_id}:{campaign_id}:{workspace_id}"
        self._data[key]["events"][0]["payload_digest"] = "mutated-digest"


class AdversarialIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        # Load Antigua
        self.workspace_raw = load("campaigns/antigua-guatemala/workspace.json")
        self.brand_raw = load("fixtures/candidate-brand/antigua-candidate-brand.json")
        self.ledger_raw = load("fixtures/approval-ledger/antigua.json")
        self.workflow_raw = load("fixtures/daily-workflow/antigua.json")
        self.store_raw = load("fixtures/persistence/antigua-store.json")

        self.t = "tenant:bernydotjar"
        self.c = "campaign:antigua-guatemala-exploratory"
        self.w = "workspace:antigua-2026"
        self.key = f"{self.t}:{self.c}:{self.w}"

        self.workspace_repo = InMemoryWorkspaceRepository({self.key: copy.deepcopy(self.workspace_raw)})
        self.brand_repo = InMemoryCandidateBrandRepository({self.key: copy.deepcopy(self.brand_raw)})
        self.ledger_repo = InMemoryApprovalLedgerRepository({self.key: copy.deepcopy(self.ledger_raw)})
        self.workflow_repo = InMemoryDailyWorkflowRepository({self.key: copy.deepcopy(self.workflow_raw)})
        self.store_repo = CorruptiblePersistenceStoreRepository({self.key: copy.deepcopy(self.store_raw)})

        self.service = ReadOnlyApplicationService(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )

        self.intent_raw = load("fixtures/persistence/antigua-write-intent.json")
        self.auth_raw = load("fixtures/persistence/antigua-authorization.json")

    def test_clean_transaction_is_observed_by_read_model(self) -> None:
        # 1. Run a valid transaction mutating the store
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )

        with uow:
            uow.load_store(self.t, self.c, self.w)
            uow.register_intent(self.intent_raw, self.auth_raw)

        # 2. Query service model to verify integrity
        report = self.service.get_audit_integrity_status(self.t, self.c, self.w)
        self.assertEqual(report["status"], "VALID")
        self.assertEqual(report["events_processed"], 1)

    def test_cross_tenant_scope_access_fails_closed(self) -> None:
        # Adversarial agent attempts to load Antigua resources using a different tenant ID
        bad_tenant = "tenant:malicious-attacker"

        with self.assertRaises(ApplicationServiceError):
            self.service.get_workspace_summary(bad_tenant, self.c, self.w)

        with self.assertRaises(ApplicationServiceError):
            self.service.get_candidate_brand_status(bad_tenant, self.c, self.w)

    def test_cross_scope_write_intent_is_rejected_in_transaction(self) -> None:
        # Attack vector: Modifying tenant/campaign fields inside the write intent to cause cross-scope writes
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )

        cross_intent = copy.deepcopy(self.intent_raw)
        cross_intent["tenant_id"] = "tenant:attacker"

        with self.assertRaises(TransactionError):
            with uow:
                uow.load_store(self.t, self.c, self.w)
                uow.register_intent(cross_intent, self.auth_raw)

        # Confirm store version was not bumped
        self.assertEqual(self.store_repo.get(self.t, self.c, self.w)["aggregate_version"], 0)

    def test_agent_escalation_to_human_authority_fails_closed(self) -> None:
        # Attack vector: An AGENT principal attempts to write to a human-only restricted operation
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )

        escalated_intent = copy.deepcopy(self.intent_raw)
        # Change principal to agent
        escalated_intent["principal_id"] = "agent:untrusted-assistant"
        # Attempt operation restricted to human:
        escalated_intent["required_permission"] = "APPROVE_POLITICAL"

        escalated_auth = copy.deepcopy(self.auth_raw)
        escalated_auth["actor_type"] = "AGENT"
        escalated_auth["principal_id"] = "agent:untrusted-assistant"
        escalated_auth["permission"] = "APPROVE_POLITICAL"

        with self.assertRaises(TransactionError):
            with uow:
                uow.load_store(self.t, self.c, self.w)
                uow.register_intent(escalated_intent, escalated_auth)

        self.assertEqual(self.store_repo.get(self.t, self.c, self.w)["aggregate_version"], 0)

    def test_repository_read_copy_cannot_tamper_with_history(self) -> None:
        # 1. Perform valid write
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )
        with uow:
            uow.load_store(self.t, self.c, self.w)
            uow.register_intent(self.intent_raw, self.auth_raw)

        # 2. Mutating a public repository read changes only the detached copy.
        store = self.store_repo.get(self.t, self.c, self.w)
        store["events"][0]["payload_digest"] = "mutated-digest"

        report = self.service.get_audit_integrity_status(self.t, self.c, self.w)
        self.assertEqual(report["status"], "VALID")

    def test_storage_layer_corruption_marks_observability_as_corrupted(self) -> None:
        uow = UnitOfWork(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )
        with uow:
            uow.load_store(self.t, self.c, self.w)
            uow.register_intent(self.intent_raw, self.auth_raw)

        # Explicit test-only bypass models compromise below the safe repository API.
        self.store_repo.inject_corruption_for_test(self.t, self.c, self.w)

        report = self.service.get_audit_integrity_status(self.t, self.c, self.w)
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("hash mismatch", report["reason"].lower())


if __name__ == "__main__":
    unittest.main()
