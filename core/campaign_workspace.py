#!/usr/bin/env python3
"""Versioned Campaign Workspace validation and deterministic governed loop.

The module intentionally uses only the Python standard library.  It is a pure
domain boundary: loading and writing files belong to adapters such as the CLI.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
EVIDENCE_CLASSES = {
    "OFFICIAL_SOURCE", "CAMPAIGN_RESEARCH", "PERCEPTION", "HYPOTHESIS", "UNKNOWN"
}
DECISION_STATUSES = {"APPROVED", "PENDING", "UNDER_RESEARCH", "BLOCKED", "REJECTED"}
APPROVAL_STATUSES = {"APPROVED", "PENDING", "BLOCKED", "REJECTED"}
STATION_STATUSES = {"ACTIVE", "RESEARCH_ONLY", "BLOCKED", "AWAITING_APPROVAL", "INACTIVE"}
CANONICAL_STATIONS = {
    "station:campaign-chief", "station:electoral-research", "station:digital-strategy",
    "station:territory-mobilization", "station:political-content", "station:paid-media",
    "station:storytelling-media-training", "station:tracking-risk-learning",
}
GATE_RESULTS = {"CLOSED", "ELIGIBLE_FOR_HUMAN_APPROVAL"}
SENSITIVE_REQUEST_FIELDS = {"approved", "authorized", "published", "funded", "activated"}
PERSONAL_PATH = re.compile(r"(?:/Users/[^/]+|/home/[^/]+|[A-Za-z]:\\\\Users\\\\[^\\\\]+)")
SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")


class WorkspaceValidationError(ValueError):
    """A stable, user-facing validation failure."""


@dataclass(frozen=True)
class GateRule:
    gate_id: str
    prerequisites: tuple[str, ...]
    approvals: tuple[str, ...] = ()
    any_of: tuple[str, ...] = ()


GATE_RULES = (
    GateRule("gate:political-content", ("objective_approved", "priority_segment_approved", "positioning_approved")),
    GateRule("gate:public-content-publication", ("content_draft_exists", "factual_review_approved", "political_review_approved")),
    GateRule("gate:paid-media", ("priority_segment_approved", "geographic_priority_approved", "conversion_event_approved", "budget_ceiling_approved"), ("campaign_chief", "paid_media_owner")),
    GateRule("gate:field-mobilization", ("geographic_priority_approved", "responsible_owner_assigned", "field_objective_approved"), ("campaign_chief",)),
    GateRule("gate:public-proposal", ("supporting_evidence_accepted", "viability_review_approved", "political_review_approved")),
    GateRule("gate:crisis-response", ("verified_facts_available", "spokesperson_assigned", "position_approved")),
    GateRule("gate:narrative-change", (), ("campaign_chief",), ("performance_evidence_exists", "documented_strategic_change_exists")),
)
CANONICAL_GATES = {rule.gate_id for rule in GATE_RULES}


def _objects(workspace: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for key in ("political_objectives", "territories", "segments", "evidence", "decisions", "approvals", "gates", "stations", "agents", "cycle_runs", "artifacts", "risks", "blockers", "learning_records"):
        yield from workspace.get(key, [])


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkspaceValidationError(message)


def _assert_no_sensitive_paths(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_no_sensitive_paths(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_sensitive_paths(child, f"{path}[{index}]")
    elif isinstance(value, str):
        _require(not PERSONAL_PATH.search(value), f"personal path is forbidden at {path}")
        _require("../" not in value and "..\\" not in value, f"path traversal string is forbidden at {path}")


def validate_workspace(workspace: dict[str, Any]) -> dict[str, Any]:
    """Validate schema-level and cross-object domain invariants, fail closed."""
    _require(isinstance(workspace, dict), "workspace must be an object")
    required = {
        "schema_version", "workspace_id", "tenant_id", "campaign_id", "name", "jurisdiction",
        "mandate", "campaign_stage", "political_objectives", "territories", "segments", "evidence",
        "decisions", "approvals", "gates", "stations", "agents", "cycle_runs", "artifacts",
        "risks", "blockers", "learning_records", "metadata",
    }
    _require(set(workspace) == required, f"workspace fields mismatch: expected {sorted(required)}")
    _require(workspace["schema_version"] == SCHEMA_VERSION, f"unsupported schema version: {workspace.get('schema_version')}")
    for key in ("workspace_id", "tenant_id", "campaign_id"):
        _require(isinstance(workspace[key], str) and SAFE_ID.fullmatch(workspace[key]) is not None, f"invalid stable ID: {key}")
    _require(workspace["workspace_id"].startswith("workspace:"), "workspace_id namespace mismatch")
    _require(workspace["tenant_id"].startswith("tenant:"), "tenant_id namespace mismatch")
    _require(workspace["campaign_id"].startswith("campaign:"), "campaign_id namespace mismatch")
    _require(isinstance(workspace["name"], str) and workspace["name"].strip(), "name is required")
    _require(isinstance(workspace["jurisdiction"], dict), "jurisdiction must be an object")
    collection_fields = ("political_objectives", "territories", "segments", "evidence", "decisions", "approvals", "gates", "stations", "agents", "cycle_runs", "artifacts", "risks", "blockers", "learning_records")
    for field in collection_fields:
        _require(isinstance(workspace[field], list), f"{field} must be a list")
    for singleton in ("mandate", "campaign_stage"):
        item = workspace[singleton]
        _require(isinstance(item, dict), f"{singleton} must be an object")
        _validate_common(item, singleton, workspace)
        _require(item.get("status") in DECISION_STATUSES, f"invalid {singleton} status")
    ids: set[str] = {workspace["tenant_id"], workspace["campaign_id"], workspace["workspace_id"]}
    for item in _objects(workspace):
        _validate_common(item, "domain object", workspace)
        item_id = item["id"]
        _require(item_id not in ids, f"duplicate ID: {item_id}")
        ids.add(item_id)
    for evidence in workspace["evidence"]:
        _require(evidence.get("classification") in EVIDENCE_CLASSES, f"missing or invalid evidence class: {evidence.get('id')}")
    for decision in workspace["decisions"]:
        _require(decision.get("status") in DECISION_STATUSES, f"invalid decision status: {decision.get('id')}")
        _require(not (decision.get("status") == "APPROVED" and decision.get("blocked") is True), f"contradictory decision state: {decision.get('id')}")
    for approval in workspace["approvals"]:
        _require(approval.get("status") in APPROVAL_STATUSES, f"invalid approval status: {approval.get('id')}")
        _require(approval.get("actor_type") == "HUMAN", f"approval authority must be human: {approval.get('id')}")
        _require(isinstance(approval.get("role"), str) and approval["role"].strip(), f"approval role is required: {approval.get('id')}")
        _require(isinstance(approval.get("supports_gates"), list) and approval["supports_gates"], f"approval must bind to at least one gate: {approval.get('id')}")
        for gate_id in approval["supports_gates"]:
            _require(gate_id in CANONICAL_GATES, f"approval references unknown gate {gate_id}: {approval.get('id')}")
    for station in workspace["stations"]:
        _require(station.get("status") in STATION_STATUSES, f"invalid station status: {station.get('id')}")
        for field in ("mode", "mission", "required_inputs", "blocked_by", "approval_owner", "autonomy_level", "review_date"):
            _require(field in station, f"station {station.get('id')} missing {field}")
    _require({station["id"] for station in workspace["stations"]} == CANONICAL_STATIONS, "workspace must configure exactly the eight canonical stations")
    _require({gate["id"] for gate in workspace["gates"]} == CANONICAL_GATES, "workspace must configure exactly the seven canonical gates")
    for gate in workspace["gates"]:
        _require(gate["status"] in {"BLOCKED", "AWAITING_APPROVAL", "INACTIVE"}, f"invalid configured gate status: {gate['id']}")
    _validate_references(workspace, ids)
    _assert_no_sensitive_paths(workspace)
    return workspace


def _validate_common(item: dict[str, Any], label: str, workspace: dict[str, Any]) -> None:
    _require(isinstance(item, dict), f"{label} must contain objects")
    for field in ("id", "status", "created_at", "updated_at", "owner", "source_or_provenance"):
        _require(field in item, f"{label} missing {field}")
    _require(isinstance(item["id"], str) and SAFE_ID.fullmatch(item["id"]) is not None, f"invalid object ID: {item.get('id')}")
    _require(item.get("tenant_id") == workspace["tenant_id"], f"cross-tenant object: {item.get('id')}")
    _require(item.get("campaign_id") == workspace["campaign_id"], f"cross-campaign object: {item.get('id')}")
    _require(item.get("workspace_id") == workspace["workspace_id"], f"cross-workspace object: {item.get('id')}")
    _require(isinstance(item.get("owner"), str) and item["owner"].strip(), f"missing owner: {item.get('id')}")
    _require(item.get("source_or_provenance") not in (None, ""), f"missing provenance: {item.get('id')}")


def _validate_references(workspace: dict[str, Any], ids: set[str]) -> None:
    for item in _objects(workspace):
        for key, value in item.items():
            if key.endswith("_ref") and value is not None:
                _require(value in ids, f"unknown reference {value} from {item['id']}")
            if key.endswith("_refs"):
                _require(isinstance(value, list), f"{key} must be a list on {item['id']}")
                for ref in value:
                    _require(ref in ids, f"unknown reference {ref} from {item['id']}")


def evaluate_gates(workspace: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate every canonical strategic gate from explicit workspace signals."""
    validate_workspace(workspace)
    signals = _validated_gate_signals(workspace)
    approval_roles_by_gate: dict[str, set[str]] = {gate_id: set() for gate_id in CANONICAL_GATES}
    for approval in workspace["approvals"]:
        if approval.get("status") != "APPROVED":
            continue
        for gate_id in approval["supports_gates"]:
            approval_roles_by_gate[gate_id].add(approval["role"])
    results = []
    for rule in GATE_RULES:
        missing = [name for name in rule.prerequisites if signals.get(name) is not True]
        if rule.any_of and not any(signals.get(name) is True for name in rule.any_of):
            missing.append("one_of:" + "|".join(rule.any_of))
        missing.extend(
            f"human_approval:{role}"
            for role in rule.approvals
            if role not in approval_roles_by_gate[rule.gate_id]
        )
        results.append({
            "gate_id": rule.gate_id,
            "status": "CLOSED" if missing else "ELIGIBLE_FOR_HUMAN_APPROVAL",
            "missing_prerequisites": missing,
            "external_effect": "NONE",
        })
    return results


def _validated_gate_signals(workspace: dict[str, Any]) -> dict[str, bool]:
    """Accept a true signal only when local, status-bearing sources support it."""
    declarations = workspace["metadata"].get("gate_signals", {})
    _require(isinstance(declarations, dict), "metadata.gate_signals must be an object")
    index = {item["id"]: item for item in _objects(workspace)}
    values: dict[str, bool] = {}
    enabling = {"APPROVED", "ACCEPTED", "VERIFIED", "READY"}
    for name, declaration in declarations.items():
        _require(isinstance(declaration, dict) and set(declaration) == {"value", "source_refs"}, f"invalid gate signal declaration: {name}")
        _require(isinstance(declaration["value"], bool), f"gate signal value must be boolean: {name}")
        _require(isinstance(declaration["source_refs"], list), f"gate signal source_refs must be a list: {name}")
        if declaration["value"]:
            _require(declaration["source_refs"], f"true gate signal lacks sources: {name}")
            for ref in declaration["source_refs"]:
                _require(ref in index, f"unknown gate signal source: {ref}")
                _require(index[ref].get("status") in enabling, f"contradictory gate signal {name}: {ref} is {index[ref].get('status')}")
                _require(name in index[ref].get("supports_signals", []), f"gate signal source {ref} does not support {name}")
        values[name] = declaration["value"]
    return values


def validate_cycle_request(request: dict[str, Any], workspace: dict[str, Any]) -> None:
    _require(isinstance(request, dict), "cycle request must be an object")
    allowed = {"schema_version", "cycle_id", "tenant_id", "campaign_id", "workspace_id", "diagnosis_category", "question", "requested_artifact", "evidence_refs"}
    _require(set(request) == allowed, f"cycle request fields mismatch: {sorted(set(request) - allowed)}")
    _require(request.get("schema_version") == SCHEMA_VERSION, "unsupported cycle request schema version")
    for key in ("tenant_id", "campaign_id", "workspace_id"):
        _require(request.get(key) == workspace[key], f"cycle request {key} mismatch")
    _require(isinstance(request.get("cycle_id"), str) and request["cycle_id"].startswith("cycle:"), "invalid cycle_id")
    _require(request.get("requested_artifact") in {"EVIDENCE_PRIORITY_DECISION_BRIEF", "RESEARCH_GAP_BRIEF", "RISK_REVIEW_BRIEF"}, "unsupported requested artifact")
    expected_category = {
        "EVIDENCE_PRIORITY_DECISION_BRIEF": "ELECTORAL_RESEARCH",
        "RESEARCH_GAP_BRIEF": "ELECTORAL_RESEARCH",
        "RISK_REVIEW_BRIEF": "TRACKING_RISK_LEARNING",
    }[request["requested_artifact"]]
    _require(request.get("diagnosis_category") == expected_category, f"diagnosis category must be {expected_category} for requested artifact")
    _require(isinstance(request.get("question"), str) and 0 < len(request["question"].strip()) <= 2000, "question must contain 1 to 2000 characters")
    _require(isinstance(request.get("evidence_refs"), list), "evidence_refs must be a list")
    evidence_ids = {item["id"] for item in workspace["evidence"]}
    for ref in request["evidence_refs"]:
        _require(ref in evidence_ids, f"unknown or cross-tenant evidence reference: {ref}")
    _assert_no_sensitive_request_fields(request)
    _assert_no_sensitive_paths(request)


def _assert_no_sensitive_request_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require(key.lower() not in SENSITIVE_REQUEST_FIELDS, f"cycle request cannot set authority field: {path}.{key}")
            _assert_no_sensitive_request_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_sensitive_request_fields(child, f"{path}[{index}]")


def run_governed_cycle(workspace: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Pure evaluation: validated inputs to one deterministic, governed result."""
    before = copy.deepcopy(workspace)
    validate_workspace(workspace)
    validate_cycle_request(request, workspace)
    gates = evaluate_gates(workspace)
    gate_by_id = {gate["gate_id"]: gate for gate in gates}
    signals = _validated_gate_signals(workspace)
    active = [s["id"] for s in workspace["stations"] if s["status"] in {"ACTIVE", "RESEARCH_ONLY"}]
    blocked = [s["id"] for s in workspace["stations"] if s["status"] == "BLOCKED"]
    artifact_type = request["requested_artifact"]
    route = _route_for(request)
    cycle_copy = _cycle_copy(artifact_type)
    result = {
        "schema_version": SCHEMA_VERSION,
        "tenant_id": workspace["tenant_id"],
        "campaign_id": workspace["campaign_id"],
        "workspace_id": workspace["workspace_id"],
        "cycle_id": request["cycle_id"],
        "state_summary": _state_summary(workspace),
        "diagnosis": {"category": request["diagnosis_category"], "reason": request["question"], "evidence_refs": request["evidence_refs"]},
        "active_stations": active,
        "blocked_stations": blocked,
        "agent_assignments": [{
            "agent_id": _assigned_agent(workspace, route),
            "station_id": route,
            "diagnosis": cycle_copy["diagnosis"],
            "critical_questions": cycle_copy["critical_questions"],
            "artifact": {"artifact_type": artifact_type, "title": _artifact_title(artifact_type), "status": "DRAFT"},
            "risk": cycle_copy["risk"],
            "next_step": cycle_copy["next_step"],
        }],
        "required_artifact": {"count": 1, "artifact_type": artifact_type, "title": _artifact_title(artifact_type), "approval_status": "NOT_APPROVED"},
        "risk_review": {"political": ["Human authority remains required."], "message": ([] if signals.get("positioning_approved", False) else ["Public positioning remains blocked."]), "operational": ["No external effects are authorized."], "evidence_gaps": list(workspace["metadata"].get("evidence_gaps", []))},
        "gates": gates,
        "approvals_required": sorted({item for gate in gates for item in gate["missing_prerequisites"] if item.startswith("human_approval:")}),
        "next_action": {"action": cycle_copy["action"], "human_input_required": cycle_copy["human_input_required"], "next_station": route},
        "provenance": request["evidence_refs"],
        "warnings": _gate_warnings(signals, gate_by_id),
    }
    _require(len(result["state_summary"]) <= 5, "state_summary exceeds five lines")
    _require(result["required_artifact"]["count"] == 1 and len(result["agent_assignments"]) == 1, "cycle must require exactly one primary artifact")
    _require(workspace == before, "workspace mutated during pure evaluation")
    return result


def _state_summary(workspace: dict[str, Any]) -> list[str]:
    return [
        f"Stage: {workspace['campaign_stage'].get('value', 'UNKNOWN')} ({workspace['campaign_stage']['status']}).",
        f"Mandate: {workspace['mandate'].get('value', 'UNKNOWN')} ({workspace['mandate']['status']}).",
        f"Active/research stations: {sum(s['status'] in {'ACTIVE', 'RESEARCH_ONLY'} for s in workspace['stations'])}.",
        f"Blocked stations: {sum(s['status'] == 'BLOCKED' for s in workspace['stations'])}.",
        "Tactical action remains gated pending evidence and human decisions.",
    ]


def _route_for(request: dict[str, Any]) -> str:
    return {
        "EVIDENCE_PRIORITY_DECISION_BRIEF": "station:electoral-research",
        "RESEARCH_GAP_BRIEF": "station:electoral-research",
        "RISK_REVIEW_BRIEF": "station:tracking-risk-learning",
    }[request["requested_artifact"]]


def _assigned_agent(workspace: dict[str, Any], station_id: str) -> str:
    candidates = [a["id"] for a in workspace["agents"] if a.get("station_ref") == station_id]
    _require(len(candidates) == 1, f"exactly one agent assignment is required for {station_id}")
    return candidates[0]


def _artifact_title(artifact_type: str) -> str:
    return {
        "EVIDENCE_PRIORITY_DECISION_BRIEF": "Evidence Extraction Priority Decision Brief",
        "RESEARCH_GAP_BRIEF": "Research Gap Brief",
        "RISK_REVIEW_BRIEF": "Campaign Risk Review Brief",
    }[artifact_type]


def _gate_warnings(signals: dict[str, bool], gate_by_id: dict[str, dict[str, Any]]) -> list[str]:
    warnings = []
    if not signals.get("priority_segment_approved", False):
        warnings.append("Segment selection remains blocked.")
    if not signals.get("positioning_approved", False):
        warnings.append("Public positioning remains blocked.")
    if gate_by_id["gate:political-content"]["status"] == "CLOSED":
        warnings.append("Content remains blocked.")
    if gate_by_id["gate:paid-media"]["status"] == "CLOSED":
        warnings.append("Paid media remains blocked.")
    if gate_by_id["gate:field-mobilization"]["status"] == "CLOSED":
        warnings.append("Mobilization remains blocked.")
    return warnings


def _cycle_copy(artifact_type: str) -> dict[str, Any]:
    return {
        "EVIDENCE_PRIORITY_DECISION_BRIEF": {
            "diagnosis": "Evidence gaps must be reconciled before strategic selection.",
            "critical_questions": ["Which source has the highest decision impact and verification gap?", "What is the risk if its claims are incorrect?"],
            "risk": "Premature strategic selection from incomplete evidence.",
            "next_step": "Prepare the internal brief for human review; do not select a segment.",
            "action": "Prioritize extraction, verification, and reconciliation of evidence.",
            "human_input_required": "Campaign Chief reviews the brief and chooses the next research priority.",
        },
        "RESEARCH_GAP_BRIEF": {
            "diagnosis": "A documented research gap requires a bounded evidence plan.",
            "critical_questions": ["Which decision is blocked by the gap?", "What is the minimum trustworthy source needed?"],
            "risk": "Synthetic or incomplete evidence could be mistaken for an approved fact.",
            "next_step": "Prepare a research gap brief for human prioritization.",
            "action": "Document the next evidence gap and verification method.",
            "human_input_required": "A human owner prioritizes or rejects the proposed research task.",
        },
        "RISK_REVIEW_BRIEF": {
            "diagnosis": "An internal risk requires governed review before further action.",
            "critical_questions": ["What evidence establishes severity?", "Which human owner accepts or mitigates the risk?"],
            "risk": "Unreviewed risk could invalidate the next campaign decision.",
            "next_step": "Prepare a risk review brief without executing mitigation.",
            "action": "Document risk evidence, options and owner for human review.",
            "human_input_required": "The authorized human owner selects a mitigation or accepts the risk.",
        },
    }[artifact_type]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def deterministic_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
