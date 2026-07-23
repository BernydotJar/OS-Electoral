from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.config import Environment, Settings
from campaignos.observability import (
    JsonLogFormatter,
    MetricsRegistry,
    resolve_trace_context,
    write_worker_metrics,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def test_json_logs_are_structured_and_ignore_unapproved_sensitive_fields() -> None:
    formatter = JsonLogFormatter(service="campaignos-api", version="0.2.0", environment="test")
    record = logging.LogRecord(
        name="campaignos-api",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="http_request_completed",
        args=(),
        exc_info=None,
    )
    record.correlation_id = "correlation-1"
    record.trace_id = "1" * 32
    record.status_code = 200
    record.authorization = "Bearer secret"  # type: ignore[attr-defined]
    record.request_body = {"political_data": "secret"}  # type: ignore[attr-defined]

    payload = json.loads(formatter.format(record))

    assert payload["event"] == "http_request_completed"
    assert payload["correlation_id"] == "correlation-1"
    assert payload["trace_id"] == "1" * 32
    assert payload["status_code"] == 200
    assert "authorization" not in payload
    assert "request_body" not in payload
    assert "secret" not in json.dumps(payload)


def test_trace_context_continues_valid_trace_and_rejects_zero_or_malformed_parents() -> None:
    incoming = "00-11111111111111111111111111111111-2222222222222222-00"
    continued = resolve_trace_context(incoming)
    zero = resolve_trace_context("00-00000000000000000000000000000000-2222222222222222-01")
    malformed = resolve_trace_context("not-a-traceparent")

    assert continued.trace_id == "1" * 32
    assert continued.flags == "00"
    assert continued.span_id != "2" * 16
    assert zero.trace_id != "0" * 32
    assert malformed.traceparent.startswith("00-")


def test_http_metrics_use_route_templates_and_propagate_operational_trace_headers() -> None:
    registry = MetricsRegistry(started_at=1000.0)
    incoming = "00-11111111111111111111111111111111-2222222222222222-01"
    with TestClient(create_app(settings(), metrics_registry=registry)) as client:
        denied = client.get(
            f"/api/v1/tenants/{TENANT_ID}/me",
            headers={"traceparent": incoming, "X-Correlation-ID": "obs-test"},
        )
        metrics = client.get("/api/v1/metrics")

    assert denied.status_code == 401
    assert denied.headers["x-correlation-id"] == "obs-test"
    returned_trace = denied.headers["traceparent"]
    assert returned_trace.startswith("00-11111111111111111111111111111111-")
    assert returned_trace != incoming
    assert metrics.status_code == 200
    assert metrics.headers["content-type"].startswith("text/plain")
    payload = metrics.text
    assert "/tenants/{tenant_id}/me" in payload
    assert str(TENANT_ID) not in payload
    assert 'status="401"' in payload
    assert "campaignos_http_request_duration_milliseconds_bucket" in payload
    assert "campaignos_http_active_requests" in payload


def test_readiness_metrics_fail_closed_without_runtime_dependencies() -> None:
    with TestClient(create_app(settings())) as client:
        ready = client.get("/api/v1/ready")
        metrics = client.get("/api/v1/metrics")

    assert ready.status_code == 503
    assert 'campaignos_readiness{dependency="identity"} 0' in metrics.text
    assert 'campaignos_readiness{dependency="database"} 0' in metrics.text


def test_worker_metrics_are_atomic_and_bounded(tmp_path: Path) -> None:
    target = tmp_path / "outbox.prom"
    write_worker_metrics(
        target,
        totals={"claimed": 5, "delivered": 4, "retried": 1, "dead_lettered": 0},
        timestamp=1234.5,
    )

    payload = target.read_text(encoding="utf-8")
    assert "campaignos_outbox_last_pass_timestamp_seconds 1234.500" in payload
    assert 'campaignos_outbox_events_total{outcome="delivered"} 4' in payload
    assert not target.with_suffix(".prom.tmp").exists()


def test_metrics_endpoint_requires_configured_bearer_token() -> None:
    token = "campaignos-metrics-test-token"  # noqa: S105 - deterministic test fixture.
    protected = Settings(
        environment=Environment.TEST,
        expose_api_docs=True,
        metrics_bearer_token=token,
    )
    with TestClient(create_app(protected)) as client:
        missing = client.get("/api/v1/metrics")
        invalid = client.get("/api/v1/metrics", headers={"Authorization": "Bearer invalid-token"})
        accepted = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {token}"})

    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert invalid.status_code == 401
    assert accepted.status_code == 200
    assert "campaignos_build_info" in accepted.text


def test_metrics_endpoint_can_be_disabled() -> None:
    disabled = Settings(environment=Environment.TEST, expose_api_docs=True, metrics_enabled=False)
    with TestClient(create_app(disabled)) as client:
        response = client.get("/api/v1/metrics")

    assert response.status_code == 404
