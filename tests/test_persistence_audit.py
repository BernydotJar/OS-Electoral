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

    def test_missing_authorization_rejected(self):
        with self.assertRaises(PersistenceContractError): plan_append(self.store,self.intent,{})

    def test_authorization_permission_mismatch_rejected(self):
        auth=copy.deepcopy(self.authorization)
        auth["permission"]="READ_WORKSPACE"
        with self.assertRaisesRegex(PersistenceContractError,"permission mismatch"): plan_append(self.store,self.intent,auth)

    def test_actor_mismatch_rejected(self):
        auth=copy.deepcopy(self.authorization)
        auth["actor_type"]="AGENT"
        with self.assertRaisesRegex(PersistenceContractError,"prefix mismatch"): plan_append(self.store,self.intent,auth)

    def test_agent_cannot_acquire_human_authority(self):
        intent=copy.deepcopy(self.intent)
        intent["required_permission"]="APPROVE_POLITICAL"
        intent["principal_id"]="agent:validator"
        auth=copy.deepcopy(self.authorization)
        auth["permission"]="APPROVE_POLITICAL"
        auth["actor_type"]="AGENT"
        auth["principal_id"]="agent:validator"
        with self.assertRaisesRegex(PersistenceContractError,"cannot acquire human authority"): plan_append(self.store,intent,auth)

    def test_cross_campaign_rejected(self):
        intent=copy.deepcopy(self.intent)
        intent["campaign_id"]="campaign:other"
        with self.assertRaisesRegex(PersistenceContractError,"campaign_id mismatch"): plan_append(self.store,intent,self.authorization)

    def test_cross_workspace_rejected(self):
        intent=copy.deepcopy(self.intent)
        intent["workspace_id"]="workspace:other"
        with self.assertRaisesRegex(PersistenceContractError,"workspace_id mismatch"): plan_append(self.store,intent,self.authorization)

    def test_resource_mismatch_id_rejected(self):
        auth=copy.deepcopy(self.authorization)
        auth["resource"]["id"]="artifact:other"
        with self.assertRaisesRegex(PersistenceContractError,"resource mismatch"): plan_append(self.store,self.intent,auth)

    def test_resource_mismatch_type_rejected(self):
        auth=copy.deepcopy(self.authorization)
        auth["resource"]["type"]="OTHER_TYPE"
        with self.assertRaisesRegex(PersistenceContractError,"resource type mismatch"): plan_append(self.store,self.intent,auth)

    def test_malformed_event_fields_rejected(self):
        store=copy.deepcopy(self.store)
        plan=plan_append(store,self.intent,self.authorization)
        event=plan["planned_event"]
        del event["idempotency_key"]
        store["events"].append(event)
        store["aggregate_version"]=1
        with self.assertRaises(PersistenceContractError): validate_store(store)

    def test_duplicate_event_id_rejected(self):
        # We simulate broken versions or sequences
        store=copy.deepcopy(self.store)
        plan=plan_append(store,self.intent,self.authorization)
        projected=apply_in_memory(store,plan)
        event=copy.deepcopy(projected["events"][0])
        projected["events"].append(event)
        with self.assertRaises(PersistenceContractError): validate_store(projected)

    def test_reordered_history_rejected(self):
        store=copy.deepcopy(self.store)
        plan1=plan_append(store,self.intent,self.authorization)
        store=apply_in_memory(store,plan1)
        intent2=copy.deepcopy(self.intent)
        intent2["intent_id"]="write-intent:other"
        intent2["idempotency_key"]="idem:other"
        intent2["expected_version"]=1
        intent2["expected_previous_hash"]=store["last_event_hash"]
        plan2=plan_append(store,intent2,self.authorization)
        store=apply_in_memory(store,plan2)
        store["events"][0],store["events"][1]=store["events"][1],store["events"][0]
        with self.assertRaises(PersistenceContractError): validate_store(store)

    def test_deleted_middle_event_rejected(self):
        store=copy.deepcopy(self.store)
        plan1=plan_append(store,self.intent,self.authorization)
        store=apply_in_memory(store,plan1)
        intent2=copy.deepcopy(self.intent)
        intent2["intent_id"]="write-intent:other"
        intent2["idempotency_key"]="idem:other"
        intent2["expected_version"]=1
        intent2["expected_previous_hash"]=store["last_event_hash"]
        plan2=plan_append(store,intent2,self.authorization)
        store=apply_in_memory(store,plan2)
        store["events"].pop(0)
        store["aggregate_version"]=1
        with self.assertRaises(PersistenceContractError): validate_store(store)

    def test_changed_historical_payload_rejected(self):
        store=copy.deepcopy(self.store)
        plan=plan_append(store,self.intent,self.authorization)
        store=apply_in_memory(store,plan)
        store["events"][0]["payload_digest"]="differentdigest"
        with self.assertRaises(PersistenceContractError): validate_store(store)

    def test_mutation_detection(self):
        store=copy.deepcopy(self.store)
        intent=copy.deepcopy(self.intent)
        auth=copy.deepcopy(self.authorization)
        plan_append(store,intent,auth)
        self.assertEqual(store,self.store)
        self.assertEqual(intent,self.intent)
        self.assertEqual(auth,self.authorization)

    def test_deterministic_output(self):
        plan1=plan_append(self.store,self.intent,self.authorization)
        plan2=plan_append(self.store,self.intent,self.authorization)
        self.assertEqual(plan1["planned_event"]["event_hash"],plan2["planned_event"]["event_hash"])

    def test_isolation_between_antigua_and_rio_claro(self):
        rio_store=load("fixtures/persistence/rio-claro-store.json")
        with self.assertRaises(PersistenceContractError): plan_append(rio_store,self.intent,self.authorization)
        rio_auth=load("fixtures/persistence/rio-claro-authorization.json")
        with self.assertRaises(PersistenceContractError): plan_append(self.store,self.intent,rio_auth)

if __name__=="__main__": unittest.main()
