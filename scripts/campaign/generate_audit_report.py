#!/usr/bin/env python3
"""CLI utility to generate a cryptographic audit integrity report from a persistence store."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.audit_observability import AuditIntegrityReadModel


def validate_safe_path(base_dir: Path, target_path: Path) -> Path:
    """Ensure path is resolved and resides strictly within base_dir (defend against path traversal)."""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = target_path.resolve()
        # Verify target is inside base
        resolved_target.relative_to(resolved_base)
        return resolved_target
    except ValueError as exc:
        raise PermissionError(f"Directory traversal detected or invalid directory path: {target_path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CampaignOS persistence store audit integrity report.")
    parser.add_argument("--store", required=True, help="Path to the persistence store JSON file.")
    parser.add_argument("--output-dir", default="artifacts/persistence-audit", help="Directory where markdown report will be saved.")
    args = parser.parse_args()

    try:
        store_path = Path(args.store)
        if not store_path.is_file():
            print(f"[ERROR] Store file not found: {args.store}", file=sys.stderr)
            return 1

        # Defend against path traversal for the output directory
        base_allowed = ROOT
        requested_output = Path(args.output_dir)
        if not requested_output.is_absolute():
            requested_output = ROOT / requested_output
        output_dir = validate_safe_path(base_allowed, requested_output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load store data
        with store_path.open("r", encoding="utf-8") as f:
            store = json.load(f)

        # Instantiate read model
        read_model = AuditIntegrityReadModel(store)
        report = read_model.verify_integrity()

        # Format markdown output
        workspace_id = store.get("workspace_id", "unknown").split(":", 1)[-1]
        report_file = output_dir / f"audit-report-{workspace_id}.md"

        status_emoji = "✅ VALID" if report["status"] == "VALID" else "❌ CORRUPTED"

        md = []
        md.append(f"# Bounded Context Audit Integrity Report — Workspace {workspace_id}\n")
        md.append("## Store Metadata\n")
        md.append("| Property | Value |")
        md.append("| --- | --- |")
        md.append(f"| Store ID | `{store.get('store_id')}` |")
        md.append(f"| Tenant ID | `{store.get('tenant_id')}` |")
        md.append(f"| Campaign ID | `{store.get('campaign_id')}` |")
        md.append(f"| Workspace ID | `{store.get('workspace_id')}` |")
        md.append(f"| Aggregate Version | `{store.get('aggregate_version')}` |")
        md.append(f"| Last Event Hash | `{store.get('last_event_hash')}` |\n")

        md.append("## Verification Integrity Status\n")
        md.append(f"**Integrity Status**: **{status_emoji}**\n")
        if report["status"] == "VALID":
            md.append(f"Processed **{report['events_processed']}** events successfully. No tampering, gaps, or reorderings detected.")
        else:
            md.append(f"**Error Reason**: {report['reason']}")
            md.append(f"**Mismatched Aggregate Version**: {report['mismatched_version']}")
        md.append("\n## Event Trail Audit Log\n")

        events = store.get("events", [])
        if not events:
            md.append("*No events recorded in this audit store.*")
        else:
            md.append("| Seq | Event ID | Operation | Resource Type | Resource ID | Principal | Occurred At |")
            md.append("| --- | --- | --- | --- | --- | --- | --- |")
            for e in events:
                md.append(f"| {e.get('aggregate_version')} | `{e.get('id')}` | `{e.get('operation')}` | `{e.get('resource_type')}` | `{e.get('resource_id')}` | `{e.get('principal_id')}` | {e.get('occurred_at')} |")

        # Write file
        report_file.write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"[OK] Audit integrity report generated successfully at: {report_file.relative_to(ROOT)}")
        return 0

    except Exception as exc:
        print(f"[ERROR] Failed to generate audit report: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
