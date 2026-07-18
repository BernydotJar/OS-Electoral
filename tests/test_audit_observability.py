from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.audit_observability import AuditIntegrityReadModel
from core.persistence_audit import event_hash

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class AuditObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.antigua = load("fixtures/persistence/antigua-store.json")
        self.rio_claro = load("fixtures/persistence/rio-claro-store.json")

        # Construct a valid, populated mock store
        t, c, w = "tenant:bernydotjar", "campaign:antigua-guatemala-exploratory", "workspace:antigua-2026"
        self.populated = {
            "schema_version": "1.0",
            "store_id": "audit-store:antigua-governance",
            "tenant_id": t,
            "campaign_id": c,
            "workspace_id": w,
            "aggregate_version": 2,
            "last_event_hash": "GENESIS",
            "events": [],
            "idempotency_keys": [],
            "metadata": {"adapter": "IN_MEMORY_TEST_ONLY", "production_persistence": False}
        }

        # Event 1
        e1 = {
            "id": "audit-event:1",
            "intent_id": "write-intent:1",
            "idempotency_key": "idem-1",
            "operation": "MUTATE_WORKSPACE",
            "resource_type": "campaign-workspace",
            "resource_id": w,
            "principal_id": "human:owner",
            "authorization_request_id": "auth-req:1",
            "aggregate_version": 1,
            "occurred_at": "2026-07-18T20:00:00Z",
            "payload_digest": "digest-1",
            "previous_hash": "GENESIS",
            "tenant_id": t,
            "campaign_id": c,
            "workspace_id": w
        }
        e1["event_hash"] = event_hash(e1)
        self.populated["events"].append(e1)
        self.populated["idempotency_keys"].append("idem-1")

        # Event 2
        e2 = {
            "id": "audit-event:2",
            "intent_id": "write-intent:2",
            "idempotency_key": "idem-2",
            "operation": "MUTATE_BRAND",
            "resource_type": "candidate-brand",
            "resource_id": "brand:antigua",
            "principal_id": "human:owner",
            "authorization_request_id": "auth-req:2",
            "aggregate_version": 2,
            "occurred_at": "2026-07-18T20:05:00Z",
            "payload_digest": "digest-2",
            "previous_hash": e1["event_hash"],
            "tenant_id": t,
            "campaign_id": c,
            "workspace_id": w
        }
        e2["event_hash"] = event_hash(e2)
        self.populated["events"].append(e2)
        self.populated["idempotency_keys"].append("idem-2")

        # Update last_event_hash in store
        self.populated["last_event_hash"] = e2["event_hash"]

    def test_verify_empty_stores_are_valid(self) -> None:
        model_antigua = AuditIntegrityReadModel(self.antigua)
        report_antigua = model_antigua.verify_integrity()
        self.assertEqual(report_antigua["status"], "VALID")
        self.assertEqual(report_antigua["events_processed"], 0)

        model_rio = AuditIntegrityReadModel(self.rio_claro)
        report_rio = model_rio.verify_integrity()
        self.assertEqual(report_rio["status"], "VALID")
        self.assertEqual(report_rio["events_processed"], 0)

    def test_verify_populated_store_is_valid(self) -> None:
        model = AuditIntegrityReadModel(self.populated)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "VALID")
        self.assertEqual(report["events_processed"], 2)

    def test_tampering_event_payload_is_detected(self) -> None:
        tampered = copy.deepcopy(self.populated)
        # Modify a field inside event 1 to invalidate its hash
        tampered["events"][0]["payload_digest"] = "tampered-digest"

        model = AuditIntegrityReadModel(tampered)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("hash mismatch", report["reason"])

    def test_tampering_reordered_events_is_detected(self) -> None:
        tampered = copy.deepcopy(self.populated)
        # Swap events
        tampered["events"][0], tampered["events"][1] = tampered["events"][1], tampered["events"][0]

        model = AuditIntegrityReadModel(tampered)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("version sequence broken", report["reason"].lower())

    def test_tampering_broken_chain_hash_is_detected(self) -> None:
        tampered = copy.deepcopy(self.populated)
        # Modify previous_hash of event 2
        tampered["events"][1]["previous_hash"] = "fake-previous"
        # Recalculate event 2 hash so it doesn't fail on self-hash check
        tampered["events"][1]["event_hash"] = event_hash(tampered["events"][1])
        tampered["last_event_hash"] = tampered["events"][1]["event_hash"]

        model = AuditIntegrityReadModel(tampered)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("hash chain broken", report["reason"].lower())

    def test_tampering_mismatched_store_last_hash_is_detected(self) -> None:
        tampered = copy.deepcopy(self.populated)
        tampered["last_event_hash"] = "fake-last-hash"

        model = AuditIntegrityReadModel(tampered)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("last_event_hash", report["reason"])

    def test_tampering_mismatched_store_version_is_detected(self) -> None:
        tampered = copy.deepcopy(self.populated)
        tampered["aggregate_version"] = 99

        model = AuditIntegrityReadModel(tampered)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("aggregate version", report["reason"].lower())

    def test_tampering_duplicate_idempotency_key_is_detected(self) -> None:
        tampered = copy.deepcopy(self.populated)
        # Set event 2 idempotency_key to match event 1
        tampered["events"][1]["idempotency_key"] = "idem-1"
        # Recompute hash of event 2 so it doesn't fail on self-hash check
        tampered["events"][1]["event_hash"] = event_hash(tampered["events"][1])
        tampered["last_event_hash"] = tampered["events"][1]["event_hash"]

        model = AuditIntegrityReadModel(tampered)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("Duplicate idempotency key", report["reason"])

    def test_tampering_duplicate_event_id_is_detected(self) -> None:
        tampered = copy.deepcopy(self.populated)
        # Set event 2 ID to match event 1
        tampered["events"][1]["id"] = "audit-event:1"
        # Recompute hash
        tampered["events"][1]["event_hash"] = event_hash(tampered["events"][1])
        tampered["last_event_hash"] = tampered["events"][1]["event_hash"]

        model = AuditIntegrityReadModel(tampered)
        report = model.verify_integrity()
        self.assertEqual(report["status"], "CORRUPTED")
        self.assertIn("Duplicate event ID", report["reason"])

    def test_query_filter_exact_match(self) -> None:
        model = AuditIntegrityReadModel(self.populated)

        # Filter by principal_id
        res = model.query(principal_id="human:owner")
        self.assertEqual(len(res), 2)

        # Filter by resource_type
        res = model.query(resource_type="campaign-workspace")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "audit-event:1")

        # Filter by operation
        res = model.query(operation="MUTATE_BRAND")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], "audit-event:2")


if __name__ == "__main__":
    unittest.main()
