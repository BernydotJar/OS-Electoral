from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.approval_ledger import ApprovalLedgerValidationError, digest, project_inbox, propose_transition, validate_approval_state

ROOT=Path(__file__).resolve().parents[1]

def load(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))

class ApprovalLedgerTests(unittest.TestCase):
    def setUp(self):
        self.state=load("fixtures/approval-ledger/antigua.json")
        self.command=load("fixtures/approval-ledger/antigua-approve-command.json")

    def test_pending_projection_is_read_only(self):
        before=copy.deepcopy(self.state)
        result=project_inbox(self.state)
        self.assertEqual(result["pending_count"],1)
        self.assertEqual(result["external_effects"],"NONE")
        self.assertEqual(self.state,before)

    def test_approval_proposal_requires_human_and_does_not_mutate(self):
        before=copy.deepcopy(self.state)
        result=propose_transition(self.state,self.command)
        self.assertEqual(result["projected_status"],"APPROVED")
        self.assertEqual(result["external_effects"],"NONE")
        self.assertEqual(self.state,before)

    def test_agent_cannot_approve(self):
        command=copy.deepcopy(self.command); command["actor_type"]="AGENT"
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"human actor"): propose_transition(self.state,command)

    def test_wrong_role_cannot_approve(self):
        command=copy.deepcopy(self.command); command["role"]="paid_media_owner"
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"unauthorized"): propose_transition(self.state,command)

    def test_cross_tenant_command_rejected(self):
        command=copy.deepcopy(self.command); command["tenant_id"]="tenant:other"
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"tenant_id mismatch"): propose_transition(self.state,command)

    def test_replay_rejected(self):
        state=copy.deepcopy(self.state)
        state["ledger"][0]["transition_id"]=self.command["transition_id"]
        state["ledger"][0]["entry_hash"]=self._hash(state["ledger"][0])
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"transition replay"): propose_transition(state,self.command)

    def test_hash_tampering_rejected(self):
        state=copy.deepcopy(self.state); state["ledger"][0]["reason"]="tampered"
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"hash mismatch"): validate_approval_state(state)

    def test_cross_purpose_event_rejected(self):
        state=copy.deepcopy(self.state); state["ledger"][0]["scope_id"]="gate:paid-media"; state["ledger"][0]["entry_hash"]=self._hash(state["ledger"][0])
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"cross-purpose"): validate_approval_state(state)

    def test_status_cannot_disagree_with_ledger(self):
        state=copy.deepcopy(self.state); state["requests"][0]["status"]="APPROVED"
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"disagrees"): validate_approval_state(state)

    def test_approval_requires_valid_option(self):
        command=copy.deepcopy(self.command); command["selected_option_ref"]="option:unknown"
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"valid selected option"): propose_transition(self.state,command)

    def test_expire_can_be_system_but_has_no_effect(self):
        command=copy.deepcopy(self.command); command.update(action="EXPIRE",actor_type="SYSTEM",role="system",selected_option_ref=None)
        result=propose_transition(self.state,command)
        self.assertEqual(result["projected_status"],"EXPIRED")
        self.assertEqual(result["external_effects"],"NONE")

    def test_schema_version_rejected(self):
        state=copy.deepcopy(self.state); state["schema_version"]="9.9"
        with self.assertRaisesRegex(ApprovalLedgerValidationError,"unsupported"): validate_approval_state(state)

    @staticmethod
    def _hash(entry): return digest({key:value for key,value in entry.items() if key!="entry_hash"})

if __name__=="__main__": unittest.main()
