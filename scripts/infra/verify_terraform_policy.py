#!/usr/bin/env python3
"""Fail closed on unsafe or non-reproducible Terraform repository policy."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXACT_TERRAFORM_VERSION = "1.15.8"
EXACT_AWS_PROVIDER_VERSION = "6.55.0"
FORBIDDEN_EXECUTION = re.compile(
    r"\bterraform\s+(?:apply|destroy|import|state|taint|untaint|force-unlock)\b|"
    r"\btofu\s+(?:apply|destroy|import|state|taint|untaint|force-unlock)\b|"
    r"-auto-approve\b",
    re.IGNORECASE,
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def verify(root: Path) -> dict[str, object]:
    errors: list[str] = []
    terraform_root = root / "infra/terraform"
    source_files = sorted(terraform_root.rglob("*.tf"))
    test_files = sorted(terraform_root.rglob("*.tftest.hcl"))
    lock_files = sorted(terraform_root.rglob(".terraform.lock.hcl"))

    _require(bool(source_files), errors, "Terraform source files are required")
    _require(len(test_files) >= 2, errors, "bootstrap and platform mock plan tests are required")
    _require(len(lock_files) == 2, errors, "both Terraform roots require dependency lock files")

    version_pin = _text(root / ".terraform-version").strip()
    _require(
        version_pin == EXACT_TERRAFORM_VERSION,
        errors,
        f".terraform-version must equal {EXACT_TERRAFORM_VERSION}",
    )

    for path in source_files:
        relative = path.relative_to(root).as_posix()
        text = _text(path)
        if "required_version" in text:
            _require(
                f'required_version = "= {EXACT_TERRAFORM_VERSION}"' in text,
                errors,
                f"{relative}: Terraform version must be exact",
            )
        if "hashicorp/aws" in text:
            _require(
                f'version = "= {EXACT_AWS_PROVIDER_VERSION}"' in text,
                errors,
                f"{relative}: AWS provider version must be exact",
            )
        if re.search(r"(?i)\b(access_key|secret_key|token)\s*=", text):
            errors.append(f"{relative}: static provider credentials are forbidden")

    for path in lock_files:
        relative = path.relative_to(root).as_posix()
        text = _text(path)
        _require(
            f'version     = "{EXACT_AWS_PROVIDER_VERSION}"' in text
            and f'constraints = "{EXACT_AWS_PROVIDER_VERSION}"' in text,
            errors,
            f"{relative}: AWS provider lock must match exact constraint",
        )
        _require("zh:" in text and "h1:" in text, errors, f"{relative}: checksums are required")

    executable_paths = [root / "Makefile", *sorted((root / ".github/workflows").glob("*.y*ml"))]
    executable_paths.extend(sorted((root / "scripts").rglob("*.sh")))
    executable_paths.extend(sorted((root / "scripts").rglob("*.py")))
    for path in executable_paths:
        if (
            not path.is_file()
            or path.relative_to(root).as_posix() == "scripts/infra/verify_terraform_policy.py"
        ):
            continue
        match = FORBIDDEN_EXECUTION.search(_text(path))
        if match:
            relative = path.relative_to(root).as_posix()
            errors.append(f"{relative}: forbidden Terraform mutation command: {match.group(0)}")

    all_hcl = "\n".join(_text(path) for path in source_files)
    required_fragments = {
        'backend "s3"': "partial S3 backend is required",
        "use_lockfile = true": "S3 lockfile support is required",
        "encrypt      = true": "backend encryption is required",
        "publicly_accessible    = false": "RDS must remain private",
        "storage_encrypted     = true": "RDS storage encryption is required",
        "deletion_protection                 = var.database_deletion_protection": (
            "RDS deletion protection must be wired"
        ),
        "manage_master_user_password   = true": "RDS managed credentials are required",
        'ecr_tag_mutability     = "IMMUTABLE"': "ECR immutable tags are required",
        "ecr_scan_on_push       = true": "ECR scan on push is required",
        "image_tag_mutability = local.ecr_tag_mutability": "ECR mutability policy must be wired",
        "scan_on_push = local.ecr_scan_on_push": "ECR scan policy must be wired",
        "readonlyRootFilesystem = true": "read-only ECS root filesystem is required",
        'user                   = "10001:10001"': "non-root ECS user is required",
        "task_privileged        = false": "privileged ECS containers are forbidden",
        "privileged             = local.task_privileged": "ECS privilege policy must be wired",
        "assign_public_ip = false": "ECS tasks must not receive public IP addresses",
        "block_public_policy     = true": "S3 public policies must be blocked",
    }
    for fragment, message in required_fragments.items():
        _require(fragment in all_hcl, errors, message)
    required_patterns = {
        r"enable_execute_command\s*=\s*false": "ECS Exec must remain disabled",
        r"assign_public_ip\s*=\s*false": "ECS tasks must not receive public IP addresses",
        r"publicly_accessible\s*=\s*false": "RDS must remain private",
        r"storage_encrypted\s*=\s*true": "RDS storage encryption is required",
    }
    for pattern, message in required_patterns.items():
        _require(re.search(pattern, all_hcl) is not None, errors, message)
    _require('resource "aws_nat_gateway"' not in all_hcl, errors, "NAT gateways are forbidden")

    ignored = _text(root / ".gitignore")
    for pattern in (".terraform/", "*.tfstate", "*.tfstate.*", "crash.log"):
        _require(pattern in ignored, errors, f".gitignore must ignore {pattern}")

    forbidden_artifacts = [
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and (path.name.endswith(".tfstate") or ".tfstate." in path.name or path.name == "crash.log")
    ]
    _require(not forbidden_artifacts, errors, "local Terraform state/crash artifacts are forbidden")

    return {
        "schema_version": 1,
        "result": "PASS" if not errors else "FAIL",
        "errors": errors,
        "terraform_version": version_pin,
        "aws_provider_version": EXACT_AWS_PROVIDER_VERSION,
        "source_files": len(source_files),
        "test_files": len(test_files),
        "lock_files": len(lock_files),
        "execution_mode": "PLAN_ONLY_NO_APPLY",
        "cost_authorization": "PROHIBITED",
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
        errors = report.get("errors")
        if isinstance(errors, list):
            for error in errors:
                print(f"[ERROR] {error}")
        return 1
    print(
        "[OK] Terraform policy verified; "
        f"sources={report['source_files']}; tests={report['test_files']}; "
        "mode=PLAN_ONLY_NO_APPLY; production=BLOCKED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
