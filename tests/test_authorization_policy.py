from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.authorization_policy import AuthorizationPolicyError, authorize, validate_principal_context

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))

class AuthorizationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.human=load("fixtures/authorization/antigua-human.json")
        self.request=load("fixtures/authorization/antigua-read-request.json")
        self.agent=load("fixtures/authorization/rio-agent.json")

    def test_exact_active_grant_allows_read_only(self):
        result=authorize(self.human,self.request)
        self.assertEqual(result["decision"],"ALLOW")
        self.assertEqual(result["external_effects"],"NONE")

    def test_cross_tenant_denied(self):
        request=copy.deepcopy(self.request); request["tenant_id"]="tenant:other"
        self.assertEqual(authorize(self.human,request)["decision"],"DENY")

    def test_cross_campaign_denied(self):
        request=copy.deepcopy(self.request); request["campaign_id"]="campaign:other"
        self.assertEqual(authorize(self.human,request)["decision"],"DENY")

    def test_cross_workspace_denied(self):
        request=copy.deepcopy(self.request); request["workspace_id"]="workspace:other"
        self.assertEqual(authorize(self.human,request)["decision"],"DENY")

    def test_missing_permission_denied(self):
        request=copy.deepcopy(self.request); request["permission"]="APPROVE_POLITICAL"
        self.assertEqual(authorize(self.human,request)["decision"],"DENY")

    def test_agent_cannot_receive_human_approval_permission(self):
        context=copy.deepcopy(self.agent); context["grants"][0]["permissions"].append("APPROVE_PUBLICATION")
        with self.assertRaisesRegex(AuthorizationPolicyError,"non-human"): validate_principal_context(context)

    def test_display_name_spoofing_does_not_grant_authority(self):
        self.assertEqual(self.agent["display_name"],"Campaign Chief")
        request=copy.deepcopy(self.request)
        request.update(principal_id=self.agent["principal_id"],tenant_id="tenant:demo-civic-lab",campaign_id="campaign:rio-claro-municipal-demo",workspace_id="workspace:rio-claro-2026-demo",permission="CREATE_DRAFT",resource_id="resource:rio-draft")
        self.assertEqual(authorize(self.agent,request)["decision"],"ALLOW")
        request["permission"]="APPROVE_POLITICAL"
        self.assertEqual(authorize(self.agent,request)["decision"],"DENY")

    def test_revoked_grant_denied(self):
        context=copy.deepcopy(self.human); context["grants"][0]["status"]="REVOKED"
        self.assertEqual(authorize(context,self.request)["decision"],"DENY")

    def test_expired_by_date_denied(self):
        context=copy.deepcopy(self.human); context["grants"][0]["valid_until"]="2026-07-17"
        self.assertEqual(authorize(context,self.request)["decision"],"DENY")

    def test_unknown_permission_rejected(self):
        request=copy.deepcopy(self.request); request["permission"]="ADMIN_ALL"
        with self.assertRaisesRegex(AuthorizationPolicyError,"unknown permission"): authorize(self.human,request)

    def test_principal_mismatch_rejected(self):
        request=copy.deepcopy(self.request); request["principal_id"]="human:other"
        with self.assertRaisesRegex(AuthorizationPolicyError,"principal mismatch"): authorize(self.human,request)

    def test_context_is_immutable(self):
        before=copy.deepcopy(self.human); authorize(self.human,self.request); self.assertEqual(self.human,before)

if __name__=="__main__": unittest.main()
