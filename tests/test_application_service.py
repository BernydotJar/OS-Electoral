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
    InMemoryPersistenceStoreRepository
)
from core.application_service import (
    ReadOnlyApplicationService,
    ApplicationServiceError,
    ApplicationScopeError
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ApplicationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        # Load Antigua fixtures
        self.workspace_raw = load("campaigns/antigua-guatemala/workspace.json")
        self.brand_raw = load("fixtures/candidate-brand/antigua-candidate-brand.json")
        self.ledger_raw = load("fixtures/approval-ledger/antigua.json")
        self.workflow_raw = load("fixtures/daily-workflow/antigua.json")
        self.store_raw = load("fixtures/persistence/antigua-store.json")

        self.t = "tenant:bernydotjar"
        self.c = "campaign:antigua-guatemala-exploratory"
        self.w = "workspace:antigua-2026"
        key = f"{self.t}:{self.c}:{self.w}"

        self.workspace_repo = InMemoryWorkspaceRepository({key: copy.deepcopy(self.workspace_raw)})
        self.brand_repo = InMemoryCandidateBrandRepository({key: copy.deepcopy(self.brand_raw)})
        self.ledger_repo = InMemoryApprovalLedgerRepository({key: copy.deepcopy(self.ledger_raw)})
        self.workflow_repo = InMemoryDailyWorkflowRepository({key: copy.deepcopy(self.workflow_raw)})
        self.store_repo = InMemoryPersistenceStoreRepository({key: copy.deepcopy(self.store_raw)})

        self.service = ReadOnlyApplicationService(
            self.workspace_repo,
            self.brand_repo,
            self.ledger_repo,
            self.workflow_repo,
            self.store_repo
        )

    def test_get_workspace_summary_success(self) -> None:
        summary = self.service.get_workspace_summary(self.t, self.c, self.w)
        self.assertEqual(summary["workspace_id"], self.w)
        self.assertEqual(summary["name"], self.workspace_raw["name"])
        self.assertGreater(summary["objectives_count"], 0)
        self.assertIn("gate:political-content", summary["gate_statuses"])

    def test_get_candidate_brand_status_success(self) -> None:
        status = self.service.get_candidate_brand_status(self.t, self.c, self.w)
        self.assertEqual(status["brand_workspace_id"], self.brand_raw["brand_workspace_id"])
        self.assertEqual(status["status"], self.brand_raw["status"])

    def test_get_pending_approvals_success(self) -> None:
        pending = self.service.get_pending_approvals(self.t, self.c, self.w)
        self.assertIsInstance(pending, list)
        for req in pending:
            self.assertIn("required_roles", req)

    def test_get_daily_workflow_timeline_success(self) -> None:
        timeline = self.service.get_daily_workflow_timeline(self.t, self.c, self.w)
        self.assertEqual(timeline["workflow_id"], self.workflow_raw["workflow_id"])
        self.assertGreaterEqual(timeline["meetings_count"], 0)

    def test_get_audit_integrity_status_success(self) -> None:
        status = self.service.get_audit_integrity_status(self.t, self.c, self.w)
        self.assertEqual(status["status"], "VALID")

    def test_invalid_scope_format_raises_scope_error(self) -> None:
        with self.assertRaises(ApplicationScopeError):
            self.service.get_workspace_summary("invalid-tenant", self.c, self.w)

        with self.assertRaises(ApplicationScopeError):
            self.service.get_workspace_summary(self.t, "invalid-campaign", self.w)

        with self.assertRaises(ApplicationScopeError):
            self.service.get_workspace_summary(self.t, self.c, "invalid-workspace")

    def test_cross_scope_retrieval_is_rejected(self) -> None:
        # Construct a workspace that points to a different campaign internally
        mismatched_ws = copy.deepcopy(self.workspace_raw)
        mismatched_ws["campaign_id"] = "campaign:mismatched"

        # Register this in-memory repo under the Berny key
        key = f"{self.t}:{self.c}:{self.w}"
        # We manually bypass save() validation to insert the mismatch for the test
        self.workspace_repo._data[key] = mismatched_ws

        # Service should reject it due to cross-scope mismatch
        with self.assertRaises(ApplicationScopeError):
            self.service.get_workspace_summary(self.t, self.c, self.w)

    def test_missing_resource_raises_service_error(self) -> None:
        missing_t = "tenant:notfound"
        missing_c = "campaign:notfound"
        missing_w = "workspace:notfound"
        
        with self.assertRaises(ApplicationServiceError):
            self.service.get_workspace_summary(missing_t, missing_c, missing_w)


if __name__ == "__main__":
    unittest.main()
