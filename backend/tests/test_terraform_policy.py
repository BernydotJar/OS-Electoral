from __future__ import annotations

import shutil
from pathlib import Path

from scripts.infra.verify_terraform_policy import verify

ROOT = Path(__file__).resolve().parents[2]


def copy_policy_tree(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    for name in (".terraform-version", ".gitignore", "Makefile"):
        shutil.copy2(ROOT / name, root / name)
    shutil.copytree(ROOT / "infra", root / "infra")
    shutil.copytree(ROOT / ".github/workflows", root / ".github/workflows")
    return root


def assert_failed(root: Path, expected: str) -> None:
    report = verify(root)
    assert report["result"] == "FAIL"
    errors = report["errors"]
    assert isinstance(errors, list)
    assert any(expected in str(error) for error in errors)


def test_current_terraform_policy_passes() -> None:
    report = verify(ROOT)
    assert report["result"] == "PASS", report["errors"]
    assert report["execution_mode"] == "PLAN_ONLY_NO_APPLY"
    assert report["production_status"] == "BLOCKED"


def test_terraform_policy_rejects_mutation_command(tmp_path: Path) -> None:
    root = copy_policy_tree(tmp_path)
    workflow = root / ".github/workflows/campaignos-ci.yml"
    workflow.write_text(workflow.read_text() + "\n# terraform apply -auto-approve\n")
    assert_failed(root, "forbidden Terraform mutation command")


def test_terraform_policy_rejects_mutable_provider(tmp_path: Path) -> None:
    root = copy_policy_tree(tmp_path)
    versions = root / "infra/terraform/stacks/platform/versions.tf"
    versions.write_text(versions.read_text().replace('version = "= 6.55.0"', 'version = ">= 6.0"'))
    assert_failed(root, "AWS provider version must be exact")


def test_terraform_policy_rejects_public_database(tmp_path: Path) -> None:
    root = copy_policy_tree(tmp_path)
    data = root / "infra/terraform/modules/data/main.tf"
    data.write_text(
        data.read_text().replace("publicly_accessible    = false", "publicly_accessible    = true")
    )
    assert_failed(root, "RDS must remain private")


def test_terraform_policy_rejects_ecs_exec(tmp_path: Path) -> None:
    root = copy_policy_tree(tmp_path)
    runtime = root / "infra/terraform/modules/runtime/main.tf"
    runtime.write_text(
        runtime.read_text().replace(
            "enable_execute_command             = false",
            "enable_execute_command             = true",
        )
    )
    assert_failed(root, "ECS Exec must remain disabled")


def test_terraform_policy_rejects_local_state_file(tmp_path: Path) -> None:
    root = copy_policy_tree(tmp_path)
    (root / "infra/terraform/stacks/platform/local.tfstate").write_text("{}")
    assert_failed(root, "local Terraform state/crash artifacts are forbidden")
