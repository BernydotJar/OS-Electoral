from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_alert_rules_cover_api_worker_backup_and_restore_without_sensitive_labels() -> None:
    rules = (ROOT / "operations/alerts/campaignos.rules.yml").read_text(encoding="utf-8")

    for metric in (
        "campaignos_readiness",
        "campaignos_http_requests_total",
        "campaignos_http_request_duration_milliseconds_bucket",
        "campaignos_outbox_events_total",
        "campaignos_backup_last_success_timestamp_seconds",
        "campaignos_restore_verification_last_success_timestamp_seconds",
    ):
        assert metric in rules
    for forbidden in ("tenant_id", "campaign_id", "principal_id", "voter", "citizen"):
        assert forbidden not in rules
    assert "> 0.02" in rules
    assert "> 93600" in rules
    assert "> 691200" in rules
    assert "docs/operations/observability-and-recovery.md" in rules


def test_recovery_ci_is_digest_pinned_isolated_and_retains_evidence() -> None:
    workflow = (ROOT / ".github/workflows/campaignos-ci.yml").read_text(encoding="utf-8")

    assert "operational-recovery:" in workflow
    assert "name: PostgreSQL backup and isolated restore" in workflow
    assert "campaignos_ci_restore_test" in workflow
    assert "postgres:18.3-alpine3.23@sha256:" in workflow
    assert "make recovery-verify" in workflow
    assert "campaignos-postgresql-recovery-evidence" in workflow
    assert 'payload["source_mutation"] == "NONE"' in workflow
    assert 'payload["external_effects"] == "NONE_TEST_RESTORE_ONLY"' in workflow


def test_metrics_configuration_and_recovery_runbook_are_versioned() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    runbook = (ROOT / "docs/operations/observability-and-recovery.md").read_text(encoding="utf-8")

    assert "CAMPAIGNOS_METRICS_BEARER_TOKEN" in compose
    assert "recovery-verify:" in makefile
    assert "*_restore_test" in runbook
    assert "Production remains `BLOCKED`" in runbook
    assert "OTLP" in runbook
