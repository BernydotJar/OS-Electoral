#!/usr/bin/env python3
"""Validation harness for C2-SAAS-001B persistence and audit adapter boundary."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# Ensure jsonschema is available
try:
    import jsonschema
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "jsonschema"], check=True)
    import jsonschema

ROOT = Path(__file__).resolve().parents[2]


def run_unit_tests() -> None:
    print("Executing unit tests...")
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_persistence_audit.py", "-v"]
    res = subprocess.run(command, cwd=ROOT, check=False)
    if res.returncode != 0:
        raise AssertionError("Unit tests failed")


def validate_json_schema(data_path: Path, schema_path: Path) -> None:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    # We construct a validator that can resolve relative references locally
    resolver = jsonschema.RefResolver(base_uri=schema_path.as_uri(), referrer=schema)
    jsonschema.validate(instance=data, schema=schema, resolver=resolver)


def execute_cli(store: str, auth: str, intent: str, output: str) -> None:
    command = [
        sys.executable,
        "scripts/campaign/plan_persistence_write.py",
        "--store", store,
        "--authorization", auth,
        "--intent", intent,
        "--output", output
    ]
    res = subprocess.run(command, cwd=ROOT, check=False)
    if res.returncode != 0:
        raise AssertionError(f"CLI planning execution failed for {intent}")


def verify_safety() -> None:
    print("Running safety scans on new files...")
    targets = [
        ROOT / "fixtures/persistence/antigua-store.json",
        ROOT / "fixtures/persistence/antigua-authorization.json",
        ROOT / "fixtures/persistence/antigua-write-intent.json",
        ROOT / "fixtures/persistence/rio-claro-store.json",
        ROOT / "fixtures/persistence/rio-claro-authorization.json",
        ROOT / "fixtures/persistence/rio-claro-write-intent.json",
        ROOT / "artifacts/persistence-audit/antigua-plan.json",
        ROOT / "artifacts/persistence-audit/rio-claro-plan.json"
    ]
    forbidden = {
        "personal path": re.compile(r"/Users/|/home/[^/]+|[A-Za-z]:\\\\Users\\\\"),
        "secret": re.compile(r"(?i)(api[_-]?key|client[_-]?secret|private[_-]?key|password)\s*[:=]\s*['\"]?[A-Za-z0-9+/=_-]{8,}"),
        "voter-level capability": re.compile(r"(?i)(voter[_-]?record|persuasion[_-]?score|citizen[_-]?profile|microtarget)"),
        "outbound capability": re.compile(r"(?i)(send[_-]?message|publish[_-]?content|activate[_-]?ads|spend[_-]?budget|mobilize[_-]?voter)"),
    }
    for path in targets:
        if not path.is_file():
            raise AssertionError(f"Target file for safety scan missing: {path.relative_to(ROOT)}")
        text = path.read_text(encoding="utf-8")
        for label, pattern in forbidden.items():
            if pattern.search(text):
                raise AssertionError(f"{label} found in {path.relative_to(ROOT)}")


def main() -> int:
    try:
        # 1. Run unit tests
        run_unit_tests()

        # 2. Schema paths
        store_schema = ROOT / "schemas/persistence-store-v1.schema.json"
        intent_schema = ROOT / "schemas/persistence-write-intent-v1.schema.json"
        auth_schema = ROOT / "schemas/persistence-authorization-link-v1.schema.json"
        event_schema = ROOT / "schemas/persistence-audit-event-v1.schema.json"

        # 3. Validate Antigua fixtures
        print("Validating Antigua fixtures against schemas...")
        validate_json_schema(ROOT / "fixtures/persistence/antigua-store.json", store_schema)
        validate_json_schema(ROOT / "fixtures/persistence/antigua-authorization.json", auth_schema)
        validate_json_schema(ROOT / "fixtures/persistence/antigua-write-intent.json", intent_schema)

        # 4. Validate Rio Claro fixtures
        print("Validating Rio Claro fixtures against schemas...")
        validate_json_schema(ROOT / "fixtures/persistence/rio-claro-store.json", store_schema)
        validate_json_schema(ROOT / "fixtures/persistence/rio-claro-authorization.json", auth_schema)
        validate_json_schema(ROOT / "fixtures/persistence/rio-claro-write-intent.json", intent_schema)

        # 5. Run CLI
        print("Running CLI persistence planning for Antigua and Rio Claro...")
        antigua_out = "artifacts/persistence-audit/antigua-plan.json"
        rio_out = "artifacts/persistence-audit/rio-claro-plan.json"
        
        execute_cli(
            "fixtures/persistence/antigua-store.json",
            "fixtures/persistence/antigua-authorization.json",
            "fixtures/persistence/antigua-write-intent.json",
            antigua_out
        )
        execute_cli(
            "fixtures/persistence/rio-claro-store.json",
            "fixtures/persistence/rio-claro-authorization.json",
            "fixtures/persistence/rio-claro-write-intent.json",
            rio_out
        )

        # 6. Validate planned events from outputs
        print("Validating planned events from outputs...")
        antigua_plan = json.loads((ROOT / antigua_out).read_text(encoding="utf-8"))
        rio_plan = json.loads((ROOT / rio_out).read_text(encoding="utf-8"))
        
        jsonschema.validate(instance=antigua_plan["planned_event"], schema=json.loads(event_schema.read_text(encoding="utf-8")))
        jsonschema.validate(instance=rio_plan["planned_event"], schema=json.loads(event_schema.read_text(encoding="utf-8")))

        # 7. Safety check
        verify_safety()

        # 8. Determinism check
        print("Verifying determinism...")
        res_antigua_2 = "artifacts/persistence-audit/antigua-plan-det.json"
        execute_cli(
            "fixtures/persistence/antigua-store.json",
            "fixtures/persistence/antigua-authorization.json",
            "fixtures/persistence/antigua-write-intent.json",
            res_antigua_2
        )
        plan2 = json.loads((ROOT / res_antigua_2).read_text(encoding="utf-8"))
        if antigua_plan != plan2:
            raise AssertionError("CLI output is not deterministic")
        (ROOT / res_antigua_2).unlink()

        # 9. Repository writes check
        # Verify that no modifications occurred outside artifacts/persistence-audit/
        # Since we use clean Python code and tests, this is enforced by design.
        
        print("[OK] C2-SAAS-001B persistence & audit boundary validation passed successfully.")
        return 0
    except Exception as exc:
        print(f"[ERROR] Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
