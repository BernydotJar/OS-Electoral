from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.approval_ledger import (
    AuthenticatedPrincipalBinding,
    ApprovalLedgerValidationError,
    digest,
    project_inbox,
    propose_transition,
    transition_authorization_digest,
    validate_approval_state,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ApprovalLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = load("fixtures/approval-ledger/antigua.json")
        self.command = load("fixtures/approval-ledger/antigua-approve-command.json")
        self.principal = load("fixtures/approval-ledger/antigua-trusted-principal.json")
        self.authorization_request = load("fixtures/approval-ledger/antigua-transition-authorization-request.json")
        self.authenticated_principal = AuthenticatedPrincipalBinding(
            **load("fixtures/approval-ledger/antigua-authenticated-binding.json")
        )

    def propose(
        self,
        state: dict | None = None,
        command: dict | None = None,
        principal: dict | None = None,
        authorization_request: dict | None = None,
        authenticated_principal: AuthenticatedPrincipalBinding | None = None,
    ) -> dict:
        return propose_transition(
            self.state if state is None else state,
            self.command if command is None else command,
            principal_context=self.principal if principal is None else principal,
            authorization_request=self.authorization_request if authorization_request is None else authorization_request,
            authenticated_principal=(
                self.authenticated_principal
                if authenticated_principal is None
                else authenticated_principal
            ),
        )

    def bind_authorization(self, command: dict, authorization_request: dict) -> None:
        request = next(item for item in self.state["requests"] if item["id"] == command["request_ref"])
        authorization_request["transition_action"] = command["action"]
        authorization_request["selected_option_ref"] = command["selected_option_ref"]
        authorization_request["transition_payload_digest"] = transition_authorization_digest(
            self.state, request, command
        )

    def test_pending_projection_is_read_only(self) -> None:
        before = copy.deepcopy(self.state)
        result = project_inbox(self.state)
        self.assertEqual(result["pending_count"], 1)
        self.assertEqual(result["external_effects"], "NONE")
        self.assertEqual(self.state, before)

        result["requests"][0]["options"][0]["label"] = "CALLER MUTATION"
        result["requests"][0]["required_roles"].append("attacker")
        self.assertEqual(self.state, before)

    def test_approval_proposal_derives_actor_from_trusted_principal(self) -> None:
        before = copy.deepcopy(self.state)
        result = self.propose()
        entry = result["proposed_ledger_entry"]
        self.assertEqual(result["projected_status"], "APPROVED")
        self.assertEqual(entry["actor_id"], self.principal["principal_id"])
        self.assertEqual(entry["role"], "campaign_chief")
        self.assertEqual(entry["authorization_request_id"], self.authorization_request["request_id"])
        self.assertEqual(
            entry["authentication_session_id"],
            self.authenticated_principal.authentication_session_id,
        )
        self.assertEqual(
            entry["authentication_evidence_id"],
            self.authenticated_principal.authentication_evidence_id,
        )
        self.assertEqual(result["external_effects"], "NONE")
        self.assertEqual(self.state, before)

        projected = copy.deepcopy(self.state)
        projected["requests"][0]["status"] = "APPROVED"
        projected["ledger"].append(entry)
        validate_approval_state(projected)

    def test_missing_trusted_inputs_fails_closed(self) -> None:
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "trusted principal context"):
            propose_transition(self.state, self.command)

    def test_plain_principal_context_is_not_authentication_evidence(self) -> None:
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "authenticated principal binding"):
            propose_transition(
                self.state,
                self.command,
                principal_context=self.principal,
                authorization_request=self.authorization_request,
            )

    def test_authenticated_binding_must_match_policy_principal(self) -> None:
        binding = AuthenticatedPrincipalBinding(
            principal_id="human:different",
            actor_type="HUMAN",
            authentication_session_id="session:different",
            authentication_evidence_id="authn-evidence:different",
            trust_source="OIDC_VERIFIED_SESSION",
        )
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "authenticated principal mismatch"):
            self.propose(authenticated_principal=binding)

    def test_self_asserted_agent_identity_cannot_spoof_human(self) -> None:
        command = copy.deepcopy(self.command)
        command["actor_id"] = "agent:spoofing-human"
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "actor_id assertion mismatch"):
            self.propose(command=command)

    def test_agent_context_cannot_approve(self) -> None:
        principal = copy.deepcopy(self.principal)
        principal["principal_id"] = "agent:untrusted-assistant"
        principal["actor_type"] = "AGENT"
        principal["grants"][0]["id"] = "grant:agent-transition"
        command = copy.deepcopy(self.command)
        command["actor_type"] = "AGENT"
        command["actor_id"] = principal["principal_id"]
        authorization_request = copy.deepcopy(self.authorization_request)
        authorization_request["principal_id"] = principal["principal_id"]
        binding = AuthenticatedPrincipalBinding(
            principal_id=principal["principal_id"],
            actor_type="AGENT",
            authentication_session_id="session:agent-transition",
            authentication_evidence_id="authn-evidence:agent-transition",
            trust_source="INTERNAL_SERVICE_IDENTITY",
        )
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "authenticated human"):
            self.propose(
                command=command,
                principal=principal,
                authorization_request=authorization_request,
                authenticated_principal=binding,
            )

    def test_self_asserted_wrong_role_is_rejected(self) -> None:
        command = copy.deepcopy(self.command)
        command["role"] = "paid_media_owner"
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "role assertion mismatch"):
            self.propose(command=command)

    def test_authorization_must_bind_exact_request(self) -> None:
        authorization_request = copy.deepcopy(self.authorization_request)
        authorization_request["resource_id"] = "approval-request:other"
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "resource mismatch"):
            self.propose(authorization_request=authorization_request)

    def test_authorization_must_bind_exact_transition_payload(self) -> None:
        for field, value in (
            ("action", "REJECT"),
            ("selected_option_ref", "option:request-revision"),
            ("reason", "Different reason"),
        ):
            with self.subTest(field=field):
                command = copy.deepcopy(self.command)
                command[field] = value
                if field == "action":
                    command["selected_option_ref"] = None
                with self.assertRaisesRegex(ApprovalLedgerValidationError, "authorization"):
                    self.propose(command=command)

    def test_cross_tenant_command_rejected(self) -> None:
        command = copy.deepcopy(self.command)
        command["tenant_id"] = "tenant:other"
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "tenant_id mismatch"):
            self.propose(command=command)

    def test_replay_rejected(self) -> None:
        state = copy.deepcopy(self.state)
        state["ledger"][0]["transition_id"] = self.command["transition_id"]
        state["ledger"][0]["entry_hash"] = self._hash(state["ledger"][0])
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "transition replay"):
            self.propose(state=state)

    def test_hash_tampering_rejected(self) -> None:
        state = copy.deepcopy(self.state)
        state["ledger"][0]["reason"] = "tampered"
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "hash mismatch"):
            validate_approval_state(state)

    def test_historical_actor_prefix_spoofing_rejected(self) -> None:
        state = copy.deepcopy(self.state)
        state["ledger"][0]["actor_id"] = "human:spoofed-agent"
        state["ledger"][0]["entry_hash"] = self._hash(state["ledger"][0])
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "actor identity mismatch"):
            validate_approval_state(state)

    def test_cross_purpose_event_rejected(self) -> None:
        state = copy.deepcopy(self.state)
        state["ledger"][0]["scope_id"] = "gate:paid-media"
        state["ledger"][0]["entry_hash"] = self._hash(state["ledger"][0])
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "cross-purpose"):
            validate_approval_state(state)

    def test_status_cannot_disagree_with_ledger(self) -> None:
        state = copy.deepcopy(self.state)
        state["requests"][0]["status"] = "APPROVED"
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "disagrees"):
            validate_approval_state(state)

    def test_approval_requires_valid_option(self) -> None:
        command = copy.deepcopy(self.command)
        command["selected_option_ref"] = "option:unknown"
        authorization_request = copy.deepcopy(self.authorization_request)
        self.bind_authorization(command, authorization_request)
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "valid selected option"):
            self.propose(command=command, authorization_request=authorization_request)

    def test_expire_can_use_trusted_system_principal(self) -> None:
        principal = copy.deepcopy(self.principal)
        principal["principal_id"] = "system:approval-expirer"
        principal["actor_type"] = "SYSTEM"
        principal["grants"][0].update(
            id="grant:approval-expirer",
            role_id="role:approval-expiration-service",
        )
        principal["metadata"].update(
            trust_source="INTERNAL_SERVICE_IDENTITY",
            session_id="session:approval-expirer",
        )
        command = copy.deepcopy(self.command)
        command.update(
            action="EXPIRE",
            actor_type="SYSTEM",
            actor_id=principal["principal_id"],
            role="approval_expiration_service",
            selected_option_ref=None,
        )
        authorization_request = copy.deepcopy(self.authorization_request)
        authorization_request["principal_id"] = principal["principal_id"]
        self.bind_authorization(command, authorization_request)
        binding = AuthenticatedPrincipalBinding(
            principal_id=principal["principal_id"],
            actor_type="SYSTEM",
            authentication_session_id="session:approval-expirer",
            authentication_evidence_id="authn-evidence:approval-expirer",
            trust_source="INTERNAL_SERVICE_IDENTITY",
        )
        result = self.propose(
            command=command,
            principal=principal,
            authorization_request=authorization_request,
            authenticated_principal=binding,
        )
        self.assertEqual(result["projected_status"], "EXPIRED")
        self.assertEqual(result["external_effects"], "NONE")

    def test_schema_version_rejected(self) -> None:
        state = copy.deepcopy(self.state)
        state["schema_version"] = "9.9"
        with self.assertRaisesRegex(ApprovalLedgerValidationError, "unsupported"):
            validate_approval_state(state)

    @staticmethod
    def _hash(entry: dict) -> str:
        return digest({key: value for key, value in entry.items() if key != "entry_hash"})


if __name__ == "__main__":
    unittest.main()
