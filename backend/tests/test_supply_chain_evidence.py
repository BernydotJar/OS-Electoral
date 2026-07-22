from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/ci/generate_supply_chain_evidence.py"
VERIFIER = ROOT / "scripts/ci/verify_ci_policy.py"
REVISION = "8d6c491a6681ea2395e2f81800dda294e41b69bb"
EPOCH = 1_784_678_400


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed Python executable and repository scripts.
        [sys.executable, *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def generate(output: Path) -> None:
    run(
        str(GENERATOR),
        "--repo-root",
        str(ROOT),
        "--output-dir",
        str(output),
        "--revision",
        REVISION,
        "--source-date-epoch",
        str(EPOCH),
    )


def copy_policy_tree(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".github").mkdir(parents=True)
    shutil.copy2(
        ROOT / ".github/campaignos-security-policy.json",
        root / ".github/campaignos-security-policy.json",
    )
    shutil.copytree(ROOT / ".github/workflows", root / ".github/workflows")
    return root


def verify(root: Path) -> subprocess.CompletedProcess[str]:
    return run(str(VERIFIER), "--repo-root", str(root), check=False)


def test_supply_chain_evidence_is_byte_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate(first)
    generate(second)

    assert {item.name for item in first.iterdir()} == {
        "SHA256SUMS",
        "cyclonedx-sbom.json",
        "evidence-report.json",
        "provenance.intoto.json",
        "source-manifest.json",
    }
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()


def test_sbom_contains_every_locked_python_and_npm_package(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    generate(output)
    sbom = json.loads((output / "cyclonedx-sbom.json").read_text())
    components = {
        (item["properties"][0]["value"], item["name"], item["version"])
        for item in sbom["components"]
    }

    uv = tomllib.loads((ROOT / "uv.lock").read_text())
    expected_python = {
        ("python", str(item["name"]), str(item["version"])) for item in uv["package"]
    }
    npm = json.loads((ROOT / "frontend/package-lock.json").read_text())
    expected_npm: set[tuple[str, str, str]] = set()
    for package_path, item in npm["packages"].items():
        if not package_path or not item.get("version"):
            continue
        marker = "node_modules/"
        name = str(item.get("name") or package_path.rsplit(marker, 1)[-1])
        expected_npm.add(("npm", name, str(item["version"])))

    assert expected_python <= components
    assert expected_npm <= components
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"


def test_manifest_provenance_and_checksums_are_self_consistent(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    generate(output)
    manifest_path = output / "source-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    provenance = json.loads((output / "provenance.intoto.json").read_text())
    report = json.loads((output / "evidence-report.json").read_text())

    tracked = (
        subprocess.run(  # noqa: S603 - fixed git executable and arguments.
            [shutil.which("git") or "git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .split("\0")
    )
    expected_paths = {item for item in tracked if item and (ROOT / item).is_file()}
    recorded = {item["path"]: item for item in manifest["files"]}
    assert set(recorded) == expected_paths
    for relative, entry in recorded.items():
        data = (ROOT / relative).read_bytes()
        assert entry["sha256"] == hashlib.sha256(data).hexdigest()
        assert entry["size"] == len(data)

    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert provenance["subject"][0]["digest"]["sha256"] == manifest_digest
    materials = {
        item["uri"]: item["digest"]["sha256"]
        for item in provenance["predicate"]["buildDefinition"]["resolvedDependencies"]
    }
    assert materials["uv.lock"] == hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    assert report["embedded_signature_status"] == "UNSIGNED"
    assert report["github_keyless_attestation"] == "REQUESTED_BY_CAMPAIGNOS_CI"
    assert report["signature_claim"] is False
    assert report["production_status"] == "BLOCKED"

    checksum_lines = (output / "SHA256SUMS").read_text().splitlines()
    for line in checksum_lines:
        digest, filename = line.split("  ", 1)
        assert digest == hashlib.sha256((output / filename).read_bytes()).hexdigest()


def test_current_ci_policy_passes() -> None:
    result = verify(ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "production=BLOCKED" in result.stdout


@pytest.mark.parametrize(
    ("filename", "old", "new", "error"),
    [
        (
            "campaignos-ci.yml",
            "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0",
            "actions/checkout@v7",
            "not pinned",
        ),
        (
            "campaignos-ci.yml",
            "  pull_request:\n",
            "  pull_request_target:\n",
            "pull_request_target is forbidden",
        ),
        (
            "campaignos-ci.yml",
            "          persist-credentials: false\n",
            "          persist-credentials: true\n",
            "disable persisted credentials",
        ),
        (
            "campaignos-ci.yml",
            "    name: Software bill of materials and source provenance\n",
            "    name: Removed supply chain job\n",
            "missing required status check",
        ),
        (
            "deploy-pages.yml",
            "  workflow_dispatch:\n",
            "  workflow_dispatch:\n  push:\n",
            "automatic publication triggers are forbidden",
        ),
    ],
)
def test_ci_policy_rejects_security_regressions(
    tmp_path: Path,
    filename: str,
    old: str,
    new: str,
    error: str,
) -> None:
    root = copy_policy_tree(tmp_path)
    path = root / ".github/workflows" / filename
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))

    result = verify(root)
    assert result.returncode == 1
    assert error in result.stdout


def test_live_settings_evaluator_detects_drift() -> None:
    from scripts.ci.verify_github_security_settings import evaluate

    policy = json.loads((ROOT / ".github/campaignos-security-policy.json").read_text())
    actions = {"enabled": True, "allowed_actions": "selected", "sha_pinning_required": True}
    selected = {
        "github_owned_allowed": True,
        "verified_allowed": False,
        "patterns_allowed": policy["allowed_action_patterns"],
    }
    protection = {
        "required_status_checks": {
            "strict": True,
            "contexts": policy["required_status_checks"],
        },
        "enforce_admins": {"enabled": True},
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True,
        },
        "required_conversation_resolution": {"enabled": True},
        "required_linear_history": {"enabled": True},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
    }
    passing = evaluate(
        policy,
        actions,
        selected,
        protection,
        vulnerability_alerts=True,
        automated_security_fixes=True,
    )
    assert passing["result"] == "PASS"

    actions["sha_pinning_required"] = False
    failing = evaluate(
        policy,
        actions,
        selected,
        protection,
        vulnerability_alerts=True,
        automated_security_fixes=True,
    )
    assert failing["result"] == "FAIL"
    errors = failing["errors"]
    assert isinstance(errors, list)
    assert "GitHub security control drift: actions_sha_pinning" in errors
