#!/usr/bin/env python3
"""Compare live GitHub repository controls with the versioned security policy."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _gh_json(gh: str, endpoint: str) -> dict[str, Any]:
    result = subprocess.run(  # noqa: S603 - absolute gh path; shell is never used.
        [gh, "api", endpoint],
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise RuntimeError(f"GitHub API returned non-object JSON for {endpoint}")
    return value


def _gh_enabled(gh: str, endpoint: str) -> bool:
    result = subprocess.run(  # noqa: S603 - absolute gh path; shell is never used.
        [gh, "api", endpoint, "--silent"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def evaluate(
    policy: dict[str, Any],
    actions: dict[str, Any],
    selected: dict[str, Any],
    protection: dict[str, Any],
    *,
    vulnerability_alerts: bool,
    automated_security_fixes: bool,
) -> dict[str, object]:
    errors: list[str] = []
    expected_checks = set(policy["required_status_checks"])
    actual_checks = set(protection.get("required_status_checks", {}).get("contexts", []))
    expected_patterns = set(policy["allowed_action_patterns"])
    actual_patterns = set(selected.get("patterns_allowed", []))

    comparisons = {
        "actions_enabled": actions.get("enabled") is True,
        "actions_selected_only": actions.get("allowed_actions") == "selected",
        "actions_sha_pinning": actions.get("sha_pinning_required") is True,
        "github_owned_actions": selected.get("github_owned_allowed")
        is policy["github_owned_actions_allowed"],
        "verified_creator_actions": selected.get("verified_allowed")
        is policy["verified_creator_actions_allowed"],
        "selected_action_patterns": actual_patterns == expected_patterns,
        "required_status_checks": actual_checks == expected_checks,
        "strict_status_checks": protection.get("required_status_checks", {}).get("strict") is True,
        "enforce_admins": protection.get("enforce_admins", {}).get("enabled")
        is policy["enforce_admins"],
        "required_approvals": protection.get("required_pull_request_reviews", {}).get(
            "required_approving_review_count"
        )
        == policy["pull_request_reviews_required"],
        "dismiss_stale_reviews": protection.get("required_pull_request_reviews", {}).get(
            "dismiss_stale_reviews"
        )
        is policy["dismiss_stale_reviews"],
        "conversation_resolution": protection.get("required_conversation_resolution", {}).get(
            "enabled"
        )
        is policy["require_conversation_resolution"],
        "linear_history": protection.get("required_linear_history", {}).get("enabled") is True,
        "force_pushes_disabled": protection.get("allow_force_pushes", {}).get("enabled")
        is policy["allow_force_pushes"],
        "deletions_disabled": protection.get("allow_deletions", {}).get("enabled")
        is policy["allow_deletions"],
        "vulnerability_alerts": vulnerability_alerts is policy["vulnerability_alerts_required"],
        "automated_security_fixes": automated_security_fixes,
    }
    for name, passed in comparisons.items():
        if not passed:
            errors.append(f"GitHub security control drift: {name}")
    return {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "comparisons": comparisons,
        "required_status_checks": sorted(actual_checks),
        "allowed_action_patterns": sorted(actual_patterns),
        "production_status": "BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--repository", default="BernydotJar/OS-Electoral")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    gh = shutil.which("gh")
    if gh is None:
        raise RuntimeError("gh is required to verify live repository controls")
    root = args.repo_root.resolve()
    policy = json.loads(
        (root / ".github/campaignos-security-policy.json").read_text(encoding="utf-8")
    )
    base = f"repos/{args.repository}"
    report = evaluate(
        policy,
        _gh_json(gh, f"{base}/actions/permissions"),
        _gh_json(gh, f"{base}/actions/permissions/selected-actions"),
        _gh_json(gh, f"{base}/branches/{policy['default_branch']}/protection"),
        vulnerability_alerts=_gh_enabled(gh, f"{base}/vulnerability-alerts"),
        automated_security_fixes=_gh_enabled(gh, f"{base}/automated-security-fixes"),
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    errors = report["errors"]
    checks = report["required_status_checks"]
    if not isinstance(errors, list) or not isinstance(checks, list):
        raise RuntimeError("GitHub security report has an invalid internal shape")
    if report["result"] != "PASS":
        for error in errors:
            print(f"[ERROR] {error}")
        return 1
    print(
        "[OK] live GitHub security settings match versioned policy; "
        f"required_checks={len(checks)}; production=BLOCKED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
