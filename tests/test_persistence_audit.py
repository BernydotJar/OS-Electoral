from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.persistence_audit import PersistenceContractError, apply_in_memory, event_hash, plan_append, validate_store

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))

class PersistenceAuditTests(unittest.TestCase):
    def setUp(self):
        self.store=load("fixtures/persistence/antigua-store.json")
        self.intent=load("fixtures/persistence/antigua-write-intent.json")
        self.authorization=load("fixtures/persistence/antigua-authorization.json")

    def test_plan_is_read_only_and_non_persistent(self):
        before=copy.deepcopy(self.store); result=plan_append(self.store,self.intent,self.authorization)
        self.assertEqual(result["outcome"],"ACCEPTABLE_FOR_ADAPTER")
        self.assertFalse(result["persistence_performed"])
        self.assertEqual(result["external_effects"],"NONE")
        self.assertEqual(self.store,before)

    def test_in_memory_adapter_returns_new_valid_store(self):
        plan=plan_append(self.store,self.intent,self.authorization)
        projected=apply_in_memory(self.store,plan)
        self.assertEqual(projected["aggregate_version"],1)
        self.assertEqual(len(projected["events"]),1)
        self.assertEqual(self.store["aggregate_version"],0)

    def test_denied_authorization_rejected(self):
        authorization=copy.deepcopy(self.authorization); authorization["decision"]="DENY"
        with self.assertRaisesRegex(PersistenceContractError,"ALLOW"): plan_append(self.store,self.intent,authorization)

    def test_cross_tenant_intent_rejected(self):
        intent=copy.deepcopy(self.intent); intent["tenant_id"]="tenant:other"
        with self.assertRaisesRegex(PersistenceContractError,"tenant_id mismatch"): plan_append(self.store,intent,self.authorization)

    def test_authorization_scope_mismatch_rejected(self):
        authorization=copy.deepcopy(self.authorization); authorization["scope"]["workspace_id"]="workspace:other"
        with self.assertRaisesRegex(PersistenceContractError,"workspace_id mismatch with authorization"): plan_append(self.store,self.intent,authorization)

    def test_stale_version_rejected(self):
        intent=copy.deepcopy(self.intent); intent["expected_version"]=1
        with self.assertRaisesRegex(PersistenceContractError,"stale aggregate version"): plan_append(self.store,intent,self.authorization)

    def test_stale_hash_rejected(self):
        intent=copy.deepcopy(self.intent); intent["expected_previous_hash"]="bad"
        with self.assertRaisesRegex(PersistenceContractError,"stale previous event hash"): plan_append(self.store,intent,self.authorization)

    def test_idempotency_replay_rejected(self):
        store=copy.deepcopy(self.store); store["idempotency_keys"].append(self.intent["idempotency_key"])
        with self.assertRaisesRegex(PersistenceContractError,"idempotency replay"): plan_append(store,self.intent,self.authorization)

    def test_read_only_resource_rejected(self):
        intent=copy.deepcopy(self.intent); intent["resource_type"]="GOVERNANCE_SNAPSHOT"
        with self.assertRaisesRegex(PersistenceContractError,"read-only"): plan_append(self.store,intent,self.authorization)

    def test_prohibited_operation_rejected(self):
        intent=copy.deepcopy(self.intent); intent["operation"]="PUBLISH"
        with self.assertRaisesRegex(PersistenceContractError,"unsupported or prohibited"): plan_append(self.store,intent,self.authorization)

    def test_authorization_principal_mismatch_rejected(self):
        authorization=copy.deepcopy(self.authorization); authorization["principal_id"]="human:other"
        with self.assertRaisesRegex(PersistenceContractError,"principal mismatch"): plan_append(self.store,self.intent,authorization)

    def test_hash_tampering_rejected(self):
        projected=apply_in_memory(self.store,plan_append(self.store,self.intent,self.authorization))
        projected["events"][0]["payload_digest"]="tampered"
        with self.assertRaisesRegex(PersistenceContractError,"hash mismatch"): validate_store(projected)

    def test_adapter_replay_rejected(self):
        plan=plan_append(self.store,self.intent,self.authorization)
        projected=apply_in_memory(self.store,plan)
        with self.assertRaisesRegex(PersistenceContractError,"version mismatch|idempotency replay"): apply_in_memory(projected,plan)

    def test_event_hash_is_deterministic(self):
        event=plan_append(self.store,self.intent,self.authorization)["planned_event"]
        self.assertEqual(event["event_hash"],event_hash(event))

if __name__=="__main__": unittest.main()
