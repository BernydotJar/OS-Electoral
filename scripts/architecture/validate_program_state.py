#!/usr/bin/env python3
"""Validate CampaignOS program truth, delivery gates, and fallback records."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "architecture/program-state.json"
PROGRAM_STATE = ROOT / "program/program-state.json"
TASK_GRAPH = ROOT / "program/task-graph.yaml"
TASK_LEDGER = ROOT / "program/task-ledger.yaml"

ROADMAP_STATUSES = {
    "ACTIVE",
    "BLOCKED_BY_DEPENDENCY",
    "COMPLETE_LOCAL",
    "DEFERRED",
    "EXECUTABLE_NEXT",
    "HUMAN_BLOCKED",
    "MERGED_TO_MAIN",
}
TASK_STATUS_BY_ROADMAP_STATUS = {
    "ACTIVE": "IN_PROGRESS",
    "BLOCKED_BY_DEPENDENCY": "BLOCKED_BY_DEPENDENCY",
    "COMPLETE_LOCAL": "COMPLETE_LOCAL",
    "DEFERRED": "DEFERRED",
    "EXECUTABLE_NEXT": "READY",
    "MERGED_TO_MAIN": "MERGED_TO_MAIN",
}
FINDING_STATUSES = {"OPEN", "REMEDIATION_IN_PROGRESS", "RESOLVED"}
FINDING_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
GATE_STATUSES = {"BLOCKED", "NOT_IMPLEMENTED", "NOT_VERIFIED", "PARTIAL", "PASS"}
STACK_CONCLUSIONS = {"FAILURE", "SUCCESS"}
WORKSTREAM_IDS = {f"WS-{index:02d}" for index in range(1, 16)}
SHA_PATTERN = re.compile(r"[0-9a-f]{40}")

REQUIRED_GATES = {
    "accessibility-review",
    "agent-guardrails",
    "approval-ledger",
    "backups",
    "background-jobs",
    "candidate-workspace",
    "deployment-runbook",
    "dev-staging-prod",
    "documentation-current",
    "explicit-human-production-approval",
    "guided-onboarding",
    "i18n-es-en",
    "incident-response",
    "load-test",
    "migrations",
    "object-storage",
    "observability",
    "postgresql",
    "privacy-review",
    "product-boundaries",
    "rbac",
    "real-authentication",
    "real-session-validation",
    "required-tests-and-evals",
    "restore-test",
    "rollback-runbook",
    "roadmap",
    "security-review",
    "team-builder",
    "tenant-isolation",
    "terraform",
    "threat-model",
    "training-academy",
    "versioned-api",
    "war-room",
    "zero-critical-high-findings",
}
REQUIRED_HUMAN_GATES = {
    "ACTIVATE_FIELD_MOBILIZATION",
    "ACTIVATE_PAID_MEDIA",
    "APPROVE_POSITIONING",
    "APPROVE_PUBLIC_CONTENT",
    "APPROVE_SPENDING",
    "CONTACT_CITIZENS",
    "DEPLOYMENT",
    "MERGE_STACK",
    "SELECT_PRIORITY_SEGMENT",
}
REQUIRED_PROHIBITED_CAPABILITIES = {
    "ASTROTURFING",
    "AUTOMATED_MOBILIZATION",
    "AUTOMATED_PUBLISHING",
    "AUTOMATED_SPENDING",
    "BIOMETRIC_POLITICAL_PERSUASION",
    "CITIZEN_SURVEILLANCE",
    "COORDINATED_HARASSMENT",
    "COVERT_TEAM_SURVEILLANCE",
    "DECEPTIVE_INVOICING",
    "DISINFORMATION",
    "FAKE_ACCOUNTS",
    "FEAR_EXPLOITATION",
    "INDIVIDUAL_PERSUADABILITY_INFERENCE",
    "INDIVIDUAL_VOTE_INTENTION_STORAGE",
    "LEGAL_VIOLATION_COST_OPTIMIZATION",
    "PSYCHOLOGICAL_VULNERABILITY_TARGETING",
    "PUBLIC_RESOURCE_CAMPAIGN_MIXING",
    "PERSUADABILITY_SCORING",
    "SENSITIVE_MICROTARGETING",
    "TROLL_CENTER",
    "UNAUTHORIZED_CONTACT",
    "UNCONSENTED_CONTACT_DATABASE",
    "VOTER_LEVEL_PROFILING",
    "VOTER_LOYALTY_MONITORING",
}
REQUIRED_PROGRAM_ARTIFACTS = {
    "program/autoskills-review.md",
    "program/context7-evidence.md",
    "program/current-state-assessment.md",
    "program/iteration-log.md",
    "program/production-gap-matrix.md",
    "program/program-state.json",
    "program/skill-usage-register.md",
    "program/task-graph.yaml",
    "program/task-ledger.yaml",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"missing program artifact: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"invalid JSON-compatible YAML in {path.relative_to(ROOT)}: {exc}"
        ) from exc
    require(isinstance(value, dict), f"expected object in {path.relative_to(ROOT)}")
    return value


def require_iso_date(value: Any, field: str) -> None:
    require(isinstance(value, str), f"{field} must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise AssertionError(f"{field} must be an ISO date") from exc


def require_unique(values: list[Any], message: str) -> None:
    require(len(values) == len(set(values)), message)


def validate_stack(data: dict[str, Any]) -> set[int]:
    stack = data["stack"]
    require(isinstance(stack, list) and stack, "stack must be a non-empty list")
    stack_ids = [item["id"] for item in stack]
    branches = [item["branch"] for item in stack]
    require_unique(stack_ids, "duplicate stack increment")
    require_unique(branches, "duplicate stack branch")

    previous = "main"
    failed_runs: set[int] = set()
    for item in stack:
        increment_id = item["id"]
        require(item["status"] == "MERGED_TO_MAIN", f"invalid stack status: {increment_id}")
        require(item["base"] == previous, f"stack base mismatch: {increment_id}; expected {previous}")
        require(item["external_effects"] == "NONE_IN_INCREMENT", f"external effects drift: {increment_id}")
        require(isinstance(item["issue"], int) and item["issue"] > 0, f"invalid issue: {increment_id}")
        require(isinstance(item["pr"], int) and item["pr"] > 0, f"invalid PR: {increment_id}")
        require(item["pr_state"] == "MERGED", f"stack PR is not merged: {increment_id}")

        validation = item["validation"]
        run_id = validation["run_id"]
        conclusion = validation["conclusion"]
        require(isinstance(run_id, int) and run_id > 0, f"invalid validation run: {increment_id}")
        require(conclusion in STACK_CONCLUSIONS, f"invalid validation conclusion: {increment_id}")
        require(bool(SHA_PATTERN.fullmatch(validation["head_sha"])), f"invalid validation SHA: {increment_id}")
        if conclusion == "FAILURE":
            failed_runs.add(run_id)
            require(validation["claim"] == "HISTORICAL_FAILURE_RECORDED", f"failure claim drift: {increment_id}")
            require(validation["blocking_for_production"] is True, f"failed run must remain blocking: {increment_id}")
        else:
            require(validation["claim"] == "SUCCESS_AT_RECORDED_SHA", f"success claim drift: {increment_id}")
            require(validation["blocking_for_production"] is False, f"successful run cannot block production: {increment_id}")
        previous = item["branch"]

    known_failed = data["known_failed_validation_runs"]
    require_unique(known_failed, "duplicate known failed validation run")
    require(set(known_failed) == failed_runs, "known failed validation runs do not match stack evidence")
    return failed_runs


def validate_integration_runs(data: dict[str, Any]) -> None:
    run_ids: list[int] = []
    for validation in data["integration_validation"]:
        run_id = validation["run_id"]
        run_ids.append(run_id)
        require(isinstance(run_id, int) and run_id > 0, "invalid integration validation run")
        require(validation["conclusion"] in STACK_CONCLUSIONS, f"invalid integration run conclusion: {run_id}")
        require(bool(SHA_PATTERN.fullmatch(validation["head_sha"])), f"invalid integration SHA: {run_id}")
        require(bool(validation["scope"].strip()), f"missing integration run scope: {run_id}")
    require_unique(run_ids, "duplicate integration validation run")


def validate_contexts(data: dict[str, Any]) -> None:
    context_ids: list[str] = []
    for context in data["bounded_contexts"]:
        context_id = context["id"]
        context_ids.append(context_id)
        require(bool(context["owner"].strip()), f"context lacks owner: {context_id}")
        require(bool(context["maturity"].strip()), f"context lacks maturity: {context_id}")
        require(context["code"] and context["validators"], f"context lacks code or validators: {context_id}")
        for relative in [*context["code"], *context["validators"]]:
            require((ROOT / relative).is_file(), f"missing architecture artifact: {relative}")
    require_unique(context_ids, "duplicate bounded context")


def validate_workstreams_and_roadmap(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    workstreams = data["workstreams"]
    workstream_ids = [item["id"] for item in workstreams]
    require_unique(workstream_ids, "duplicate workstream")
    require(set(workstream_ids) == WORKSTREAM_IDS, "workstream set must be exactly WS-01 through WS-15")

    roadmap = data["roadmap"]
    roadmap_ids = [item["id"] for item in roadmap]
    require_unique(roadmap_ids, "duplicate roadmap item")
    roadmap_by_id = {item["id"]: item for item in roadmap}
    stack_ids = {item["id"] for item in data["stack"]}
    known = stack_ids | set(roadmap_ids)
    graph: dict[str, list[str]] = {}
    for item in roadmap:
        item_id = item["id"]
        require(item["status"] in ROADMAP_STATUSES, f"invalid roadmap status: {item_id}")
        require(item["workstream"] in WORKSTREAM_IDS, f"invalid roadmap workstream: {item_id}")
        graph[item_id] = item["depends_on"]
        for dependency in item["depends_on"]:
            require(dependency in known, f"unknown roadmap dependency {dependency} from {item_id}")

    visiting: set[str] = set()
    complete: set[str] = set()

    def walk(node: str) -> None:
        if node in complete:
            return
        require(node not in visiting, f"roadmap dependency cycle: {node}")
        visiting.add(node)
        for dependency in graph.get(node, []):
            if dependency in graph:
                walk(dependency)
        visiting.remove(node)
        complete.add(node)

    for node in graph:
        walk(node)

    production_action = roadmap_by_id.get("action:production-deployment")
    require(production_action is not None, "production deployment action is missing")
    require(production_action["status"] == "HUMAN_BLOCKED", "production deployment action must be HUMAN_BLOCKED")
    require(
        any(item["status"] in {"ACTIVE", "EXECUTABLE_NEXT"} for item in roadmap),
        "program lacks an active or executable next increment",
    )
    return roadmap_by_id


def validate_findings(data: dict[str, Any]) -> int:
    finding_ids: list[str] = []
    open_counts = {"CRITICAL": 0, "HIGH": 0}
    for finding in data["findings"]:
        finding_id = finding["id"]
        finding_ids.append(finding_id)
        require(finding["severity"] in FINDING_SEVERITIES, f"invalid finding severity: {finding_id}")
        require(finding["status"] in FINDING_STATUSES, f"invalid finding status: {finding_id}")
        require(bool(finding["summary"].strip()), f"finding lacks summary: {finding_id}")
        evidence_path = finding["evidence"].split("#", maxsplit=1)[0]
        require((ROOT / evidence_path).exists(), f"missing finding evidence: {finding_id}")
        if finding["status"] != "RESOLVED" and finding["severity"] in open_counts:
            open_counts[finding["severity"]] += 1
    require_unique(finding_ids, "duplicate finding")

    expected_summary = {
        "critical": open_counts["CRITICAL"],
        "high": open_counts["HIGH"],
        "total_critical_or_high": open_counts["CRITICAL"] + open_counts["HIGH"],
    }
    require(data["open_findings_summary"] == expected_summary, "open CRITICAL/HIGH finding summary drift")
    return expected_summary["total_critical_or_high"]


def validate_deployment_and_gates(
    data: dict[str, Any], failed_runs: set[int], open_critical_high: int
) -> None:
    pages = data["deployment_state"]["github_pages"]
    require(pages["classification"] == "DEMO_NON_PRODUCTION", "Pages must be classified as a demo")
    require(pages["workflow_mode"] == "MANUAL_ONLY", "Pages workflow must be manual-only")
    require(pages["required_confirmation"] == "DEMO_NON_PRODUCTION", "Pages confirmation drift")
    require(pages["counts_as_production_evidence"] is False, "Pages cannot count as production evidence")
    require(pages["live_url"].startswith("https://"), "Pages URL must use HTTPS")

    gates = data["production_gates"]
    gate_ids = [gate["id"] for gate in gates]
    require_unique(gate_ids, "duplicate production gate")
    require(REQUIRED_GATES <= set(gate_ids), "required production gate set is incomplete")
    for gate in gates:
        require(gate["status"] in GATE_STATUSES, f"invalid production gate status: {gate['id']}")

    production_status = data["production_status"]
    production_deployment = data["deployment_state"]["production"]
    require(production_deployment["state"] == production_status, "production status drift between records")
    incomplete_gates = [gate["id"] for gate in gates if gate["status"] != "PASS"]
    if production_status == "READY":
        require(not failed_runs, "READY is forbidden while failed validation evidence is blocking")
        require(open_critical_high == 0, "READY is forbidden with open CRITICAL/HIGH findings")
        require(not incomplete_gates, "READY is forbidden with incomplete production gates")
        require(production_deployment["human_approval_recorded"] is True, "READY requires human approval")
        require(bool(production_deployment["approval_receipt"]), "READY requires an approval receipt")
    else:
        require(production_status == "BLOCKED", "production status must be READY or BLOCKED")
        require(bool(data["production_status_reason"].strip()), "BLOCKED status requires a reason")
        require(
            bool(failed_runs or open_critical_high or incomplete_gates),
            "BLOCKED status requires at least one recorded blocker",
        )
        require(production_deployment["human_approval_recorded"] is False, "blocked production cannot record approval")
        require(production_deployment["approval_receipt"] is None, "blocked production cannot have an approval receipt")


def validate_policy_boundaries(data: dict[str, Any]) -> None:
    prohibited = data["prohibited_capabilities"]
    require_unique(prohibited, "duplicate prohibited capability")
    require(
        REQUIRED_PROHIBITED_CAPABILITIES <= set(prohibited),
        "required prohibited capability set drift",
    )
    human_gates = data["human_gates"]
    require_unique(human_gates, "duplicate human gate")
    require(REQUIRED_HUMAN_GATES <= set(human_gates), "required human gate set drift")

    campaign = data["campaign_state"]
    for field in (
        "public_positioning",
        "budget_ceiling",
        "political_content",
        "paid_media",
        "field_mobilization",
    ):
        require(campaign[field] == "BLOCKED", f"campaign gate unexpectedly opened: {field}")


def validate_fallback_records(
    data: dict[str, Any], roadmap_by_id: dict[str, dict[str, Any]]
) -> None:
    for relative in REQUIRED_PROGRAM_ARTIFACTS:
        require((ROOT / relative).is_file(), f"missing required program artifact: {relative}")

    program_state = load_json(PROGRAM_STATE)
    task_graph = load_json(TASK_GRAPH)
    task_ledger = load_json(TASK_LEDGER)
    for label, record in (
        ("program state", program_state),
        ("task graph", task_graph),
        ("task ledger", task_ledger),
    ):
        require(record["program_id"] == data["program_id"], f"{label} program ID drift")
        require_iso_date(record["updated_at"], f"{label}.updated_at")
        require(record["updated_at"] == data["updated_at"], f"{label} update date drift")
    require(program_state["authoritative_manifest"] == "architecture/program-state.json", "authoritative manifest drift")
    require(program_state["production_status"] == data["production_status"], "fallback production status drift")

    graph_tasks = task_graph["tasks"]
    graph_ids = [task["id"] for task in graph_tasks]
    require_unique(graph_ids, "duplicate fallback task graph ID")
    expected_task_ids = set(roadmap_by_id) - {"action:production-deployment"}
    require(set(graph_ids) == expected_task_ids, "fallback task graph does not match architecture roadmap")
    for task in graph_tasks:
        roadmap_item = roadmap_by_id[task["id"]]
        require(task["workstream"] == roadmap_item["workstream"], f"task workstream drift: {task['id']}")
        require(task["depends_on"] == roadmap_item["depends_on"], f"task dependency drift: {task['id']}")
        expected_status = TASK_STATUS_BY_ROADMAP_STATUS[roadmap_item["status"]]
        require(task["status"] == expected_status, f"task status drift: {task['id']}")

    ledger_entries = task_ledger["entries"]
    ledger_ids = [entry["task_id"] for entry in ledger_entries]
    require_unique(ledger_ids, "duplicate fallback ledger task ID")
    require(set(ledger_ids) == set(graph_ids), "fallback ledger does not match task graph")
    graph_by_id = {task["id"]: task for task in graph_tasks}
    for entry in ledger_entries:
        task_id = entry["task_id"]
        require(entry["status"] == graph_by_id[task_id]["status"], f"ledger status drift: {task_id}")
        require(entry["external_effects"] == "NONE", f"fallback task has external effects: {task_id}")
        for evidence in entry["evidence"]:
            require((ROOT / evidence).is_file(), f"missing task evidence: {task_id}: {evidence}")

    ready_ids = {task["id"] for task in graph_tasks if task["status"] == "READY"}
    require(set(program_state["ready_tasks"]) == ready_ids, "fallback ready task list drift")
    require(program_state["current_increment"] in set(graph_ids), "current increment is absent from task graph")


def main() -> int:
    data = load_json(MANIFEST)
    require(data["schema_version"] == "2.0", "unsupported program-state schema")
    require(data["program_id"] == "program:campaignos-production-readiness", "program ID drift")
    require(data["product_name"] == "CampaignOS", "product name drift")
    require_iso_date(data["updated_at"], "architecture.updated_at")
    require(data["operating_principle"] == "AI recommends; evidence supports; authorized humans decide.", "operating principle drift")

    failed_runs = validate_stack(data)
    validate_integration_runs(data)
    validate_contexts(data)
    roadmap_by_id = validate_workstreams_and_roadmap(data)
    open_critical_high = validate_findings(data)
    validate_deployment_and_gates(data, failed_runs, open_critical_high)
    validate_policy_boundaries(data)
    validate_fallback_records(data, roadmap_by_id)

    print(
        "[OK] CampaignOS program truth validated; "
        f"production={data['production_status']}; "
        f"open_critical_high={open_critical_high}; "
        f"blocking_failed_runs={len(failed_runs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
