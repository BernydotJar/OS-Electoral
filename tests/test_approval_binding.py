from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from core.campaign_workspace import WorkspaceValidationError, evaluate_gates

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def approval_for(workspace, approval_id: str, role: str, gates: list[str]):
    return {
        "id": approval_id,
        "status": "APPROVED",
        "actor_type": "HUMAN",
        "role": role,
        "supports_gates": gates,
        "created_at": None,
        "updated_at": "2026-07-18",
        "owner": "Demo Human Owner",
        "source_or_provenance": "synthetic adversarial fixture",
        "tenant_id": workspace["tenant_id"],
        "campaign_id": workspace["campaign_id"],
        "workspace_id": workspace["workspace_id"],
    }


class ApprovalBindingTests(unittest.TestCase):
    def setUp(self):
        self.synthetic = load("fixtures/workspaces/rio-claro-demo.json")

    def test_unrelated_role_approval_cannot_substitute_across_gates(self):
        workspace = copy.deepcopy(self.synthetic)
        workspace["metadata"]["gate_signals"].update({
            "geographic_priority_approved": {"value": True, "source_refs": ["decision:rio-territory-priority"]},
            "responsible_owner_assigned": {"value": True, "source_refs": ["decision:rio-field-owner"]},
            "field_objective_approved": {"value": True, "source_refs": ["decision:rio-field-objective"]},
            "performance_evidence_exists": {"value": True, "source_refs": ["evidence:rio-claro-demo-001"]},
        })
        workspace["decisions"].extend([
            self._decision(workspace, "decision:rio-territory-priority", "geographic_priority_approved"),
            self._decision(workspace, "decision:rio-field-owner", "responsible_owner_assigned"),
            self._decision(workspace, "decision:rio-field-objective", "field_objective_approved"),
        ])
        workspace["evidence"][0]["supports_signals"] = ["performance_evidence_exists"]
        workspace["approvals"] = [approval_for(
            workspace,
            "approval:rio-narrative-chief",
            "campaign_chief",
            ["gate:narrative-change"],
        )]

        gates = {gate["gate_id"]: gate for gate in evaluate_gates(workspace)}

        self.assertEqual(gates["gate:narrative-change"]["status"], "ELIGIBLE_FOR_HUMAN_APPROVAL")
        self.assertEqual(gates["gate:field-mobilization"]["status"], "CLOSED")
        self.assertIn(
            "human_approval:campaign_chief",
            gates["gate:field-mobilization"]["missing_prerequisites"],
        )

    def test_correct_gate_binding_satisfies_only_that_gate(self):
        workspace = copy.deepcopy(self.synthetic)
        workspace["metadata"]["gate_signals"].update({
            "geographic_priority_approved": {"value": True, "source_refs": ["decision:rio-territory-priority"]},
            "responsible_owner_assigned": {"value": True, "source_refs": ["decision:rio-field-owner"]},
            "field_objective_approved": {"value": True, "source_refs": ["decision:rio-field-objective"]},
        })
        workspace["decisions"].extend([
            self._decision(workspace, "decision:rio-territory-priority", "geographic_priority_approved"),
            self._decision(workspace, "decision:rio-field-owner", "responsible_owner_assigned"),
            self._decision(workspace, "decision:rio-field-objective", "field_objective_approved"),
        ])
        workspace["approvals"] = [approval_for(
            workspace,
            "approval:rio-field-chief",
            "campaign_chief",
            ["gate:field-mobilization"],
        )]

        gates = {gate["gate_id"]: gate for gate in evaluate_gates(workspace)}

        self.assertEqual(gates["gate:field-mobilization"]["status"], "ELIGIBLE_FOR_HUMAN_APPROVAL")
        self.assertIn("human_approval:campaign_chief", gates["gate:narrative-change"]["missing_prerequisites"])

    def test_approval_without_gate_binding_is_rejected(self):
        workspace = copy.deepcopy(self.synthetic)
        approval = approval_for(workspace, "approval:rio-unbound", "campaign_chief", ["gate:narrative-change"])
        del approval["supports_gates"]
        workspace["approvals"] = [approval]

        with self.assertRaisesRegex(WorkspaceValidationError, "bind to at least one gate"):
            evaluate_gates(workspace)

    def test_unknown_gate_binding_is_rejected(self):
        workspace = copy.deepcopy(self.synthetic)
        workspace["approvals"] = [approval_for(
            workspace,
            "approval:rio-unknown",
            "campaign_chief",
            ["gate:unknown"],
        )]

        with self.assertRaisesRegex(WorkspaceValidationError, "unknown gate"):
            evaluate_gates(workspace)

    @staticmethod
    def _decision(workspace, decision_id: str, signal: str):
        return {
            "id": decision_id,
            "status": "APPROVED",
            "topic": signal,
            "supports_signals": [signal],
            "created_at": None,
            "updated_at": "2026-07-18",
            "owner": "Demo Human Owner",
            "source_or_provenance": "synthetic adversarial fixture",
            "tenant_id": workspace["tenant_id"],
            "campaign_id": workspace["campaign_id"],
            "workspace_id": workspace["workspace_id"],
        }


if __name__ == "__main__":
    unittest.main()
