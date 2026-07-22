#!/usr/bin/env python3
"""Validate CampaignOS security/privacy and append-only declarations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CLASSIFICATIONS = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "PROHIBITED"}
RETENTION = {
    "EPHEMERAL",
    "TENANT_LIFECYCLE_REVIEW_REQUIRED",
    "CAMPAIGN_LIFECYCLE_REVIEW_REQUIRED",
    "SECURITY_EVIDENCE_REVIEW_REQUIRED",
    "PROHIBITED",
}
RECORD_TYPES = {
    "identity_principal",
    "membership_authority",
    "identity_lifecycle",
    "campaign_workspace",
    "candidate_evidence",
    "team_operations",
    "strategy_decision",
    "agent_run",
    "audit_evidence",
    "object_attachment",
    "terraform_state",
    "secret_or_token",
}
PROHIBITIONS = {
    "INDIVIDUAL_VOTE_INTENTION",
    "PERSUADABILITY_SCORE",
    "PSYCHOLOGICAL_VULNERABILITY_TARGETING",
    "BIOMETRIC_PERSUASION",
    "COVERT_LOCATION_OR_LOYALTY_TRACKING",
    "NONCONSENSUAL_POLITICAL_CONTACT_DATABASE",
    "SECRET_OR_TOKEN_IN_APPLICATION_RECORD",
}
APPEND_ONLY_TABLES = {
    "audit_events",
    "idempotency_records",
    "candidate_section_approvals",
    "war_room_snapshots",
    "strategy_decision_receipts",
    "agent_runs",
}
PROCESSOR_BOUNDARIES = {
    "APPLICATION_DATABASE_ONLY",
    "NO_LIVE_AI_PROVIDER",
    "OBJECT_STORAGE_DISABLED",
    "REMOTE_STATE_NOT_CREATED",
    "SECRET_STORE_REFERENCE_ONLY",
}
DELETION_MODES = {
    "CONTROLLED_ANONYMIZATION_OR_LEGAL_HOLD",
    "REVOKE_AND_PRESERVE_ATTRIBUTABLE_RECEIPT",
    "ARCHIVE_THEN_REVIEW_DELETE_OR_LEGAL_HOLD",
    "CORRECT_OR_RESTRICT_WITH_RECEIPT",
    "APPEND_CORRECTION_AND_LEGAL_HOLD_REVIEW",
    "APPEND_CORRECTION_OWNER_BREAK_GLASS_ONLY",
    "FEATURE_DISABLED_NO_OBJECT_ADMISSION",
    "OWNER_BREAK_GLASS_AND_ENVIRONMENT_RETIREMENT_REVIEW",
    "PROHIBITED_STORAGE_ROTATE_IF_DETECTED",
}


def load_policy(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("security data policy must be a JSON object")
    return value


def string_set(value: object) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return set()
    return set(value)


def verify(repo_root: Path, policy: dict[str, Any] | None = None) -> dict[str, object]:
    errors: list[str] = []
    value = policy or load_policy(repo_root / "docs/security/data-policy.json")

    exact_values = {
        "schema_version": 1,
        "status": "DRAFT_TECHNICAL_CONTROLS",
        "production_status": "BLOCKED",
        "independent_privacy_approval": "NOT_RECORDED",
        "jurisdictional_legal_review": "REQUIRED",
    }
    for key, expected in exact_values.items():
        if value.get(key) != expected:
            errors.append(f"{key} must equal {expected}")

    if string_set(value.get("classifications")) != CLASSIFICATIONS:
        errors.append("classification inventory mismatch")
    if string_set(value.get("retention_postures")) != RETENTION:
        errors.append("retention posture inventory mismatch")
    if string_set(value.get("required_record_types")) != RECORD_TYPES:
        errors.append("required record type inventory mismatch")
    prohibited = string_set(value.get("prohibited_fields"))
    if not PROHIBITIONS <= prohibited:
        errors.append("required political-data prohibition is missing")

    processors = value.get("live_processors")
    if (
        not isinstance(processors, dict)
        or not processors
        or set(processors.values()) != {"DISABLED"}
    ):
        errors.append("all live processors must remain disabled")

    raw_records = value.get("record_types")
    records = raw_records if isinstance(raw_records, list) else []
    if not isinstance(raw_records, list):
        errors.append("record_types must be an array")
    record_ids: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for item in records:
        if not isinstance(item, dict):
            errors.append("every record type must be an object")
            continue
        record_id = item.get("id")
        if not isinstance(record_id, str) or not record_id:
            errors.append("every record type requires an id")
            continue
        record_ids.append(record_id)
        by_id[record_id] = item
        if item.get("classification") not in CLASSIFICATIONS:
            errors.append(f"{record_id}: unknown classification")
        if item.get("retention_posture") not in RETENTION:
            errors.append(f"{record_id}: unknown retention posture")
        if item.get("processor_boundary") not in PROCESSOR_BOUNDARIES:
            errors.append(f"{record_id}: unapproved processor boundary")
        if item.get("deletion_mode") not in DELETION_MODES:
            errors.append(f"{record_id}: unknown deletion mode")
        owner = item.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            errors.append(f"{record_id}: owner is required")
        purposes = item.get("purposes")
        if (
            not isinstance(purposes, list)
            or not purposes
            or not all(isinstance(purpose, str) and purpose.strip() for purpose in purposes)
        ):
            errors.append(f"{record_id}: at least one purpose is required")
        if item.get("legal_review") != "REQUIRED":
            errors.append(f"{record_id}: legal review must remain required")
        if item.get("production_ready") is not False:
            errors.append(f"{record_id}: production_ready must remain false")

    if len(record_ids) != len(set(record_ids)):
        errors.append("record type ids must be unique")
    if set(record_ids) != RECORD_TYPES:
        errors.append("record type definitions do not match required inventory")

    agent = by_id.get("agent_run", {})
    if agent.get("processor_boundary") != "NO_LIVE_AI_PROVIDER":
        errors.append("agent_run must keep live AI providers disabled")
    secret = by_id.get("secret_or_token", {})
    if (
        secret.get("classification") != "PROHIBITED"
        or secret.get("retention_posture") != "PROHIBITED"
        or secret.get("feature_state") != "PROHIBITED"
    ):
        errors.append("secret_or_token storage must remain prohibited")

    migration_path = repo_root / "backend/migrations/versions/20260721_0011_append_only_security.py"
    migration = migration_path.read_text(encoding="utf-8")
    for table in APPEND_ONLY_TABLES:
        if f'"{table}"' not in migration:
            errors.append(f"append-only migration is missing {table}")
    for control in (
        "SECURITY DEFINER",
        "SET search_path = pg_catalog",
        "session_user",
        "pg_has_role",
        "BEFORE UPDATE OR DELETE",
        "ERRCODE = '42501'",
    ):
        if control not in migration:
            errors.append(f"append-only migration is missing control: {control}")

    privacy = (repo_root / "docs/security/privacy.md").read_text(encoding="utf-8")
    threat_model = (repo_root / "docs/security/threat-model.md").read_text(encoding="utf-8")
    if "data-policy.json" not in privacy:
        errors.append("privacy plan must link executable data policy")
    if not all(threat in threat_model for threat in ("TM-07", "TM-12", "TM-13")):
        errors.append("threat model must retain privacy/audit/export threats")
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    if "backend/tests/test_security_postgres.py" not in makefile:
        errors.append("PostgreSQL security test must be part of test-postgres")

    return {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "record_types": len(record_ids),
        "prohibited_fields": len(prohibited),
        "append_only_tables": len(APPEND_ONLY_TABLES),
        "live_processors": "DISABLED",
        "independent_approval": "NOT_RECORDED",
        "production_status": "BLOCKED",
        "external_effects": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = verify(args.repo_root.resolve())
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if report["result"] != "PASS":
        report_errors = report.get("errors")
        if isinstance(report_errors, list):
            for error in report_errors:
                print(f"[ERROR] {error}")
        return 1
    print(
        "[OK] Security/privacy policy verified; "
        f"records={report['record_types']}; prohibitions={report['prohibited_fields']}; "
        f"append_only_tables={report['append_only_tables']}; production=BLOCKED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
