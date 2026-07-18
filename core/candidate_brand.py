#!/usr/bin/env python3
"""Deterministic, read-only Candidate Brand and Reputation aggregate."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "1.0"
SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
PERSONAL_PATH = re.compile(r"(?:/Users/[^/]+|/home/[^/]+|[A-Za-z]:\\\\Users\\\\[^\\\\]+)")
EVIDENCE_CLASSES = {"OFFICIAL_SOURCE", "CAMPAIGN_RESEARCH", "PERCEPTION", "HYPOTHESIS", "UNKNOWN"}
ENABLING_EVIDENCE = {"ACCEPTED", "VERIFIED", "READY"}
INDEPENDENT_EVIDENCE = {"OFFICIAL_SOURCE", "CAMPAIGN_RESEARCH"}
CLAIM_STATUSES = {"UNKNOWN", "SELF_REPORTED", "UNDER_REVIEW", "EVIDENCE_PARTIAL", "VERIFIED", "REJECTED", "CONTRADICTED"}
BRAND_STATUSES = {"SETUP_REQUIRED", "UNDER_REVIEW", "AWAITING_APPROVAL", "APPROVED", "LOCKED"}
APPROVABLE_SECTIONS = {"identity", "biography", "purpose", "values", "attributes", "reputation"}
PROHIBITED_FIELDS = {"psychological_profile", "persuadability_score", "voter_profile", "voter_id", "microtargeting", "sensitive_targeting", "manipulation_score"}


class CandidateBrandValidationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateBrandValidationError(message)


def _safe(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _require(key.lower() not in PROHIBITED_FIELDS, f"prohibited candidate-brand field: {path}.{key}")
            _safe(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _safe(child, f"{path}[{index}]")
    elif isinstance(value, str):
        _require(not PERSONAL_PATH.search(value), f"personal path is forbidden at {path}")
        _require("../" not in value and "..\\" not in value, f"path traversal is forbidden at {path}")


def _common(record: dict[str, Any], brand: dict[str, Any], label: str) -> None:
    required = {"id", "status", "created_at", "updated_at", "owner", "source_or_provenance", "tenant_id", "campaign_id", "workspace_id", "candidate_id"}
    _require(isinstance(record, dict) and required <= set(record), f"{label} missing common fields")
    _require(SAFE_ID.fullmatch(record["id"]) is not None, f"invalid {label} ID")
    for field in ("tenant_id", "campaign_id", "workspace_id", "candidate_id"):
        _require(record[field] == brand[field], f"cross-scope {label}: {record['id']} ({field})")
    _require(isinstance(record["owner"], str) and record["owner"].strip(), f"missing owner: {record['id']}")
    _require(record["source_or_provenance"] not in (None, ""), f"missing provenance: {record['id']}")


def _evidence_index(workspace: dict[str, Any]) -> dict[str, dict[str, Any]]:
    for field in ("tenant_id", "campaign_id", "workspace_id", "evidence"):
        _require(field in workspace, f"campaign workspace missing {field}")
    index = {}
    for item in workspace["evidence"]:
        for field in ("tenant_id", "campaign_id", "workspace_id"):
            _require(item.get(field) == workspace[field], f"cross-scope campaign evidence: {item.get('id')}")
        _require(item.get("classification") in EVIDENCE_CLASSES, f"invalid campaign evidence class: {item.get('id')}")
        _require(item["id"] not in index, f"duplicate campaign evidence ID: {item['id']}")
        index[item["id"]] = item
    return index


def _refs(record: dict[str, Any], evidence: dict[str, dict[str, Any]], field: str = "evidence_refs") -> list[dict[str, Any]]:
    values = record.get(field)
    _require(isinstance(values, list), f"{field} must be a list on {record.get('id')}")
    resolved = []
    for ref in values:
        _require(ref in evidence, f"unknown or cross-scope evidence reference {ref} from {record.get('id')}")
        resolved.append(evidence[ref])
    return resolved


def _claim(record: dict[str, Any], brand: dict[str, Any], evidence: dict[str, dict[str, Any]], label: str) -> None:
    _common(record, brand, label)
    _require(record.get("status") in CLAIM_STATUSES, f"invalid {label} status: {record['id']}")
    _require(record.get("classification") in EVIDENCE_CLASSES, f"invalid {label} classification: {record['id']}")
    _require(isinstance(record.get("claim"), str) and record["claim"].strip(), f"claim is required: {record['id']}")
    resolved = _refs(record, evidence)
    if record["status"] == "VERIFIED":
        _require(resolved, f"verified claim requires evidence: {record['id']}")
        _require(all(item.get("status") in ENABLING_EVIDENCE for item in resolved), f"verified claim has non-enabling evidence: {record['id']}")
        _require(any(item.get("classification") in INDEPENDENT_EVIDENCE for item in resolved), f"verified claim requires independent evidence: {record['id']}")


def _attribute(record: dict[str, Any], brand: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> None:
    _common(record, brand, "attribute")
    _require(record.get("status") in CLAIM_STATUSES, f"invalid attribute status: {record['id']}")
    _require(record.get("candidate_self_assessment") in {"YES", "NO", "UNKNOWN"}, f"invalid self assessment: {record['id']}")
    _require(record.get("team_assessment") in {"YES", "PARTIAL", "NO", "UNKNOWN"}, f"invalid team assessment: {record['id']}")
    _require(record.get("citizen_evidence") in {"SUPPORTED", "PARTIAL", "UNRESOLVED", "CONTRADICTED"}, f"invalid citizen evidence: {record['id']}")
    resolved = _refs(record, evidence)
    perception = _refs(record, evidence, "perception_refs")
    _refs(record, evidence, "contradiction_refs")
    if record["status"] == "VERIFIED":
        _require(any(item.get("status") in ENABLING_EVIDENCE and item.get("classification") in INDEPENDENT_EVIDENCE for item in resolved), f"self-assessment alone cannot verify attribute: {record['id']}")
    if record["citizen_evidence"] != "UNRESOLVED":
        _require(perception and all(item.get("classification") == "PERCEPTION" for item in perception), f"citizen evidence must use PERCEPTION records: {record['id']}")


def _records(brand: dict[str, Any]) -> list[dict[str, Any]]:
    return [brand["identity"], brand["biography"], brand["purpose"], *brand["values"], *brand["attributes"], *brand["proof_points"], *brand["perception_gaps"], *brand["behavioral_consistency_reviews"], *brand["reputation_risks"], *brand["approvals"]]


def _populated_sections(brand: dict[str, Any]) -> set[str]:
    sections = {"identity", "biography", "purpose"}
    if brand["values"]: sections.add("values")
    if brand["attributes"]: sections.add("attributes")
    if brand["reputation_risks"]: sections.add("reputation")
    return sections


def validate_candidate_brand(brand: dict[str, Any], workspace: dict[str, Any]) -> dict[str, Any]:
    required = {"schema_version", "brand_workspace_id", "tenant_id", "campaign_id", "workspace_id", "candidate_id", "status", "identity", "biography", "purpose", "values", "attributes", "proof_points", "perception_gaps", "behavioral_consistency_reviews", "reputation_risks", "approvals", "metadata"}
    _require(isinstance(brand, dict) and set(brand) == required, f"candidate brand fields mismatch: expected {sorted(required)}")
    _require(brand["schema_version"] == SCHEMA_VERSION, f"unsupported candidate brand schema version: {brand.get('schema_version')}")
    for field in ("brand_workspace_id", "tenant_id", "campaign_id", "workspace_id", "candidate_id"):
        _require(isinstance(brand[field], str) and SAFE_ID.fullmatch(brand[field]) is not None, f"invalid stable ID: {field}")
    _require(brand["status"] in BRAND_STATUSES, "invalid candidate brand status")
    for field in ("tenant_id", "campaign_id", "workspace_id"):
        _require(brand[field] == workspace.get(field), f"candidate brand {field} mismatch")
    evidence = _evidence_index(workspace)
    for key in ("identity", "biography", "purpose"):
        _claim(brand[key], brand, evidence, key)
    for record in [*brand["values"], *brand["proof_points"]]:
        _claim(record, brand, evidence, "brand claim")
    for record in brand["attributes"]:
        _attribute(record, brand, evidence)
    ids = {brand["brand_workspace_id"], brand["candidate_id"], *evidence}
    for record in _records(brand):
        _common(record, brand, "candidate brand record")
        _require(record["id"] not in ids, f"duplicate or colliding candidate brand ID: {record['id']}")
        ids.add(record["id"])
    for gap in brand["perception_gaps"]:
        _require(gap.get("status") in {"UNKNOWN", "UNDER_REVIEW", "DOCUMENTED", "RESOLVED"}, f"invalid perception gap status: {gap['id']}")
        resolved = _refs(gap, evidence)
        if gap["status"] == "DOCUMENTED": _require(resolved and all(item["classification"] == "PERCEPTION" for item in resolved), f"documented perception gap requires PERCEPTION evidence: {gap['id']}")
    for review in brand["behavioral_consistency_reviews"]:
        _require(review.get("assessment") in {"CONSISTENT", "PARTIAL", "CONTRADICTED", "UNRESOLVED"}, f"invalid consistency assessment: {review['id']}")
        _require(review.get("subject_ref") in ids, f"unknown consistency subject: {review['id']}")
        _refs(review, evidence)
        contradictions = _refs(review, evidence, "contradiction_refs")
        if review["assessment"] == "CONTRADICTED": _require(contradictions, f"contradicted review requires contradiction evidence: {review['id']}")
    for risk in brand["reputation_risks"]:
        _require(risk.get("severity") in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}, f"invalid reputation risk severity: {risk['id']}")
        _require(isinstance(risk.get("decision_required"), bool), f"decision_required must be boolean: {risk['id']}")
        _refs(risk, evidence)
    approved_sections = set()
    for approval in brand["approvals"]:
        _require(approval.get("actor_type") == "HUMAN", f"brand approval authority must be human: {approval['id']}")
        sections = approval.get("supports_sections")
        _require(isinstance(sections, list) and sections and len(sections) == len(set(sections)), f"brand approval must bind to unique sections: {approval['id']}")
        _require(all(section in APPROVABLE_SECTIONS for section in sections), f"brand approval references unknown section: {approval['id']}")
        if approval["status"] == "APPROVED": approved_sections.update(sections)
    if brand["status"] == "APPROVED":
        _require(not (_populated_sections(brand) - approved_sections), "approved candidate brand lacks human section approvals")
        _require(all(item["status"] == "VERIFIED" for item in [brand["identity"], brand["biography"], brand["purpose"], *brand["values"], *brand["attributes"]]), "approved candidate brand contains unverified claims")
        _require(not [risk for risk in brand["reputation_risks"] if risk["severity"] in {"CRITICAL", "HIGH"} and risk["status"] not in {"RESOLVED", "CLOSED"}], "approved candidate brand has open critical reputation risks")
    _safe(brand)
    return brand


def build_candidate_brand_assessment(brand: dict[str, Any], workspace: dict[str, Any]) -> dict[str, Any]:
    before_brand, before_workspace = copy.deepcopy(brand), copy.deepcopy(workspace)
    validate_candidate_brand(brand, workspace)
    verified = [item["id"] for item in brand["attributes"] if item["status"] == "VERIFIED"]
    under_review = [item["id"] for item in brand["attributes"] if item["status"] != "VERIFIED"]
    approved_sections = {section for approval in brand["approvals"] if approval["status"] == "APPROVED" for section in approval["supports_sections"]}
    critical = [risk["id"] for risk in brand["reputation_risks"] if risk["severity"] in {"CRITICAL", "HIGH"} and risk["status"] not in {"RESOLVED", "CLOSED"}]
    blocked = any(item["status"] != "VERIFIED" for item in [brand["identity"], brand["biography"], brand["purpose"], *brand["values"], *brand["attributes"]])
    readiness = "SETUP_REQUIRED" if not brand["attributes"] or brand["identity"]["status"] == "UNKNOWN" else "RESEARCH_ONLY" if blocked or critical else "ELIGIBLE_FOR_INTERNAL_BRAND_APPROVAL"
    provenance = sorted({ref for record in _records(brand) for field in ("evidence_refs", "perception_refs", "contradiction_refs") for ref in record.get(field, [])})
    result = {
        "schema_version": SCHEMA_VERSION,
        "brand_workspace_id": brand["brand_workspace_id"], "tenant_id": brand["tenant_id"], "campaign_id": brand["campaign_id"], "workspace_id": brand["workspace_id"], "candidate_id": brand["candidate_id"],
        "state_summary": [f"Candidate brand status: {brand['status']}.", f"Identity evidence status: {brand['identity']['status']}.", f"Verified attributes: {len(verified)}; under review: {len(under_review)}.", f"Open critical/high reputation risks: {len(critical)}.", "Public positioning and political content remain outside this assessment and blocked."],
        "required_artifact": {"count": 1, "artifact_type": "CANDIDATE_BRAND_ASSESSMENT", "title": "Candidate Brand and Reputation Assessment", "status": "DRAFT"},
        "internal_readiness": readiness, "verified_attributes": verified, "under_review_attributes": under_review,
        "approvals_required": sorted(_populated_sections(brand) - approved_sections), "critical_reputation_risks": critical,
        "public_use_status": "BLOCKED", "external_effects": "NONE", "provenance": provenance,
        "warnings": ["Candidate self-assessment is not verified evidence.", "No public positioning is approved by this artifact.", "Political content remains blocked by campaign strategic gates."],
        "next_action": {"action": brand["metadata"].get("next_research_action", "Complete the next evidence-backed candidate-brand research task."), "human_input_required": "Candidate and Campaign Chief review evidence gaps; no public claim is authorized.", "next_station": "candidate-brand-reputation"},
    }
    _require(brand == before_brand and workspace == before_workspace, "candidate brand assessment mutated its inputs")
    return result


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def deterministic_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
