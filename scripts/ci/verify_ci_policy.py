#!/usr/bin/env python3
"""Fail closed when repository CI drifts from the versioned security policy."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path

_SHA_ACTION = re.compile(r"^[^\s@]+@[0-9a-f]{40}$")
_USES = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
_JOB_NAME = re.compile(r"^\s{4}name:\s*(.+?)\s*$", re.MULTILINE)


def _write_report(path: Path | None, report: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _checkout_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    for index, line in enumerate(lines):
        if "uses: actions/checkout@" in line:
            blocks.append("\n".join(lines[index : index + 8]))
    return blocks


def _owner_allowed(reference: str, policy: dict[str, object]) -> bool:
    action = reference.split("@", 1)[0]
    if bool(policy["github_owned_actions_allowed"]) and (
        action.startswith("actions/") or action.startswith("github/")
    ):
        return True
    return any(
        fnmatch.fnmatch(reference, str(pattern))
        for pattern in policy["allowed_action_patterns"]  # type: ignore[union-attr]
    )


def verify(root: Path) -> dict[str, object]:
    policy_path = root / ".github/campaignos-security-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    workflow_dir = root / ".github/workflows"
    workflows = sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")))
    errors: list[str] = []
    action_references: list[str] = []

    required = policy.get("required_status_checks")
    if not isinstance(required, list) or not required or len(required) != len(set(required)):
        errors.append("security policy required_status_checks must be a unique non-empty array")
    if policy.get("production_status") != "BLOCKED":
        errors.append("repository security policy must preserve production_status=BLOCKED")

    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        relative = workflow.relative_to(root).as_posix()
        if "pull_request_target:" in text:
            errors.append(f"{relative}: pull_request_target is forbidden")
        if not re.search(r"^permissions:\s*\n\s{2}contents:\s*read\s*$", text, re.MULTILINE):
            errors.append(f"{relative}: top-level permissions must include contents: read")
        for reference in _USES.findall(text):
            action_references.append(reference)
            if not _SHA_ACTION.fullmatch(reference):
                errors.append(
                    f"{relative}: action is not pinned to a 40-character SHA: {reference}"
                )
            elif not _owner_allowed(reference, policy):
                errors.append(f"{relative}: action owner is not allowed by policy: {reference}")
        for block in _checkout_blocks(text):
            if "persist-credentials: false" not in block:
                errors.append(f"{relative}: checkout must disable persisted credentials")
        for match in re.finditer(r"^\s*image:\s*([^\s#]+)", text, re.MULTILINE):
            image = match.group(1)
            if "@sha256:" not in image:
                errors.append(f"{relative}: service image is not digest pinned: {image}")

    ci_path = workflow_dir / "campaignos-ci.yml"
    ci_text = ci_path.read_text(encoding="utf-8")
    names = set(_JOB_NAME.findall(ci_text))
    for check in required if isinstance(required, list) else []:
        if check not in names:
            errors.append(f"campaignos-ci.yml: missing required status check name: {check}")
    required_fragments = (
        "supply-chain-evidence:",
        "name: Software bill of materials and source provenance",
        "python scripts/ci/verify_ci_policy.py",
        "python scripts/ci/generate_supply_chain_evidence.py",
        "ref: ${{ github.event.pull_request.head.sha || github.sha }}",
        '--revision "${{ github.event.pull_request.head.sha || github.sha }}"',
        "actions/attest-build-provenance@0f67c3f4856b2e3261c31976d6725780e5e4c373",
        "attestations: write",
        "id-token: write",
        "name: campaignos-supply-chain-evidence",
        "path: artifacts/supply-chain/",
        "if-no-files-found: error",
    )
    for fragment in required_fragments:
        if fragment not in ci_text:
            errors.append(f"campaignos-ci.yml: missing supply-chain control: {fragment}")
    if "rhysd/actionlint:1.7.12@sha256:" not in ci_text:
        errors.append("campaignos-ci.yml: actionlint container must be digest pinned")

    deploy_text = (workflow_dir / "deploy-pages.yml").read_text(encoding="utf-8")
    if not re.search(r"^\s{2}workflow_dispatch:\s*$", deploy_text, re.MULTILINE):
        errors.append("deploy-pages.yml: static demo must remain manual workflow_dispatch")
    if re.search(r"^\s{2}(push|pull_request|schedule):\s*$", deploy_text, re.MULTILINE):
        errors.append("deploy-pages.yml: automatic publication triggers are forbidden")
    for fragment in ("DEMO_NON_PRODUCTION", 'if [ "$DISPATCH_REF" != "main" ]'):
        if fragment not in deploy_text:
            errors.append(f"deploy-pages.yml: missing fail-closed publication guard: {fragment}")

    return {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "workflow_count": len(workflows),
        "action_reference_count": len(action_references),
        "required_status_checks": required,
        "sha_pinning_required": policy.get("sha_pinning_required"),
        "production_status": policy.get("production_status"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = verify(args.repo_root.resolve())
    _write_report(args.report, report)
    if report["result"] != "PASS":
        for error in report["errors"]:  # type: ignore[union-attr]
            print(f"[ERROR] {error}")
        return 1
    print(
        "[OK] CI policy verified; "
        f"workflows={report['workflow_count']}; actions={report['action_reference_count']}; "
        f"required_checks={len(report['required_status_checks'])}; production=BLOCKED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
