"""Low-cardinality operational telemetry for the API and internal worker.

The module intentionally emits no tenant, campaign, principal, token, request-body,
or arbitrary URL labels. Correlation and W3C trace identifiers are operational
metadata only and are never treated as authorization evidence.
"""

from __future__ import annotations

import json
import logging
import re
import secrets
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from time import time
from typing import Final

from campaignos.config import Settings

TRACEPARENT = re.compile(
    r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$",
    re.IGNORECASE,
)
ZERO_TRACE_ID: Final = "0" * 32
ZERO_SPAN_ID: Final = "0" * 16
HTTP_DURATION_BUCKETS_MS: Final = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000)
SAFE_LOG_FIELDS: Final = {
    "service",
    "version",
    "environment",
    "correlation_id",
    "trace_id",
    "span_id",
    "method",
    "route",
    "status_code",
    "duration_ms",
    "ready",
    "dependency",
    "signal",
    "claimed",
    "delivered",
    "retried",
    "dead_lettered",
    "worker_id",
}


class JsonLogFormatter(logging.Formatter):
    """Render deterministic, sanitized JSON log events."""

    def __init__(self, *, service: str, version: str, environment: str) -> None:
        super().__init__()
        self._base = {
            "service": service,
            "version": version,
            "environment": environment,
        }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "event": record.getMessage(),
            "logger": record.name,
            **self._base,
        }
        for field in SAFE_LOG_FIELDS:
            if field in self._base:
                continue
            value = getattr(record, field, None)
            if isinstance(value, (str, int, float, bool)):
                payload[field] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def configure_json_logger(settings: Settings, logger_name: str) -> logging.Logger:
    """Configure one named logger without mutating global or test handlers."""

    logger = logging.getLogger(logger_name)
    logger.setLevel(settings.log_level.upper())
    logger.propagate = False
    for handler in tuple(logger.handlers):
        if getattr(handler, "campaignos_json_handler", False):
            handler.setFormatter(
                JsonLogFormatter(
                    service=settings.service_name,
                    version=settings.service_version,
                    environment=settings.environment.value,
                )
            )
            return logger
    handler = logging.StreamHandler(sys.stdout)
    handler.campaignos_json_handler = True  # type: ignore[attr-defined]
    handler.setFormatter(
        JsonLogFormatter(
            service=settings.service_name,
            version=settings.service_version,
            environment=settings.environment.value,
        )
    )
    logger.addHandler(handler)
    return logger


class TraceContext:
    """Validated W3C trace context with a server span identifier."""

    __slots__ = ("trace_id", "span_id", "flags")

    def __init__(self, trace_id: str, span_id: str, flags: str) -> None:
        self.trace_id = trace_id
        self.span_id = span_id
        self.flags = flags

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{self.flags}"


def resolve_trace_context(value: str | None) -> TraceContext:
    """Continue a valid version-00 trace or create a new one.

    The incoming parent span is deliberately not reflected. CampaignOS emits a
    fresh server span while retaining only the validated trace ID and flags.
    """

    trace_id = secrets.token_hex(16)
    flags = "01"
    if value:
        matched = TRACEPARENT.fullmatch(value.strip())
        if matched and matched.group(1) != ZERO_TRACE_ID and matched.group(2) != ZERO_SPAN_ID:
            trace_id = matched.group(1).lower()
            flags = matched.group(3).lower()
    return TraceContext(trace_id=trace_id, span_id=secrets.token_hex(8), flags=flags)


def normalize_route_label(route: object, request_path: str) -> str:
    """Return one bounded route-template label and never a raw identifier path."""

    template = getattr(route, "path", None)
    if isinstance(template, str) and template.startswith("/") and len(template) <= 180:
        return template
    if request_path in {"/api/v1/health", "/api/v1/ready", "/api/v1/metrics"}:
        return request_path
    return "__unmatched__"


class MetricsRegistry:
    """Thread-safe, process-local Prometheus registry with bounded labels."""

    def __init__(self, *, started_at: float | None = None) -> None:
        self.started_at = started_at if started_at is not None else time()
        self._lock = Lock()
        self._active_requests = 0
        self._requests: Counter[tuple[str, str, str]] = Counter()
        self._duration_count: Counter[tuple[str, str]] = Counter()
        self._duration_sum_ms: defaultdict[tuple[str, str], float] = defaultdict(float)
        self._duration_buckets: Counter[tuple[str, str, int]] = Counter()
        self._readiness: dict[str, bool] = {}

    def request_started(self) -> None:
        with self._lock:
            self._active_requests += 1

    def request_finished(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        bounded_method = (
            method.upper()
            if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
            else "OTHER"
        )
        status = str(status_code)
        duration = max(duration_ms, 0.0)
        with self._lock:
            self._active_requests = max(self._active_requests - 1, 0)
            self._requests[(bounded_method, route, status)] += 1
            self._duration_count[(bounded_method, route)] += 1
            self._duration_sum_ms[(bounded_method, route)] += duration
            for bucket in HTTP_DURATION_BUCKETS_MS:
                if duration <= bucket:
                    self._duration_buckets[(bounded_method, route, bucket)] += 1

    def set_readiness(self, dependency: str, ready: bool) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", dependency):
            raise ValueError("dependency must be a bounded metric label")
        with self._lock:
            self._readiness[dependency] = ready

    def render_prometheus(
        self,
        *,
        service: str,
        version: str,
        database_pool: dict[str, int] | None = None,
    ) -> str:
        with self._lock:
            active = self._active_requests
            requests = dict(self._requests)
            duration_count = dict(self._duration_count)
            duration_sum = dict(self._duration_sum_ms)
            duration_buckets = dict(self._duration_buckets)
            readiness = dict(self._readiness)
        lines = [
            "# HELP campaignos_build_info Static service build information.",
            "# TYPE campaignos_build_info gauge",
            (
                "campaignos_build_info"
                f'{{service="{_escape_label(service)}",version="{_escape_label(version)}"}} 1'
            ),
            (
                "# HELP campaignos_process_start_time_seconds "
                "Unix timestamp when this process registry started."
            ),
            "# TYPE campaignos_process_start_time_seconds gauge",
            f"campaignos_process_start_time_seconds {self.started_at:.3f}",
            "# HELP campaignos_http_active_requests Current in-flight HTTP requests.",
            "# TYPE campaignos_http_active_requests gauge",
            f"campaignos_http_active_requests {active}",
            (
                "# HELP campaignos_http_requests_total "
                "Completed HTTP requests by bounded route template."
            ),
            "# TYPE campaignos_http_requests_total counter",
        ]
        for (method, route, status), count in sorted(requests.items()):
            lines.append(
                "campaignos_http_requests_total"
                f'{{method="{method}",route="{_escape_label(route)}",status="{status}"}} {count}'
            )
        lines.extend(
            [
                (
                    "# HELP campaignos_http_request_duration_milliseconds "
                    "HTTP request duration histogram."
                ),
                "# TYPE campaignos_http_request_duration_milliseconds histogram",
            ]
        )
        for method, route in sorted(duration_count):
            labels = f'method="{method}",route="{_escape_label(route)}"'
            for bucket in HTTP_DURATION_BUCKETS_MS:
                count = duration_buckets.get((method, route, bucket), 0)
                lines.append(
                    "campaignos_http_request_duration_milliseconds_bucket"
                    f'{{{labels},le="{bucket}"}} {count}'
                )
            lines.append(
                "campaignos_http_request_duration_milliseconds_bucket"
                f'{{{labels},le="+Inf"}} {duration_count[(method, route)]}'
            )
            lines.append(
                "campaignos_http_request_duration_milliseconds_sum"
                f"{{{labels}}} {duration_sum[(method, route)]:.3f}"
            )
            lines.append(
                "campaignos_http_request_duration_milliseconds_count"
                f"{{{labels}}} {duration_count[(method, route)]}"
            )
        lines.extend(
            [
                "# HELP campaignos_readiness Dependency readiness where 1 is ready.",
                "# TYPE campaignos_readiness gauge",
            ]
        )
        for dependency, ready in sorted(readiness.items()):
            lines.append(f'campaignos_readiness{{dependency="{dependency}"}} {1 if ready else 0}')
        if database_pool:
            lines.extend(
                [
                    (
                        "# HELP campaignos_database_pool_connections "
                        "SQLAlchemy pool connections by state."
                    ),
                    "# TYPE campaignos_database_pool_connections gauge",
                ]
            )
            for state, value in sorted(database_pool.items()):
                if re.fullmatch(r"[a-z][a-z0-9_]{0,31}", state):
                    lines.append(
                        f'campaignos_database_pool_connections{{state="{state}"}} {max(value, 0)}'
                    )
        return "\n".join(lines) + "\n"


def write_worker_metrics(
    path: Path, *, totals: dict[str, int], timestamp: float | None = None
) -> None:
    """Atomically publish one Prometheus textfile snapshot for the outbox worker."""

    allowed = ("claimed", "delivered", "retried", "dead_lettered")
    if set(totals) != set(allowed) or any(value < 0 for value in totals.values()):
        raise ValueError("worker totals must contain four non-negative counters")
    generated_at = timestamp if timestamp is not None else time()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    lines = [
        "# HELP campaignos_outbox_last_pass_timestamp_seconds Last completed outbox pass.",
        "# TYPE campaignos_outbox_last_pass_timestamp_seconds gauge",
        f"campaignos_outbox_last_pass_timestamp_seconds {generated_at:.3f}",
        "# HELP campaignos_outbox_events_total Events observed by the current worker process.",
        "# TYPE campaignos_outbox_events_total counter",
    ]
    for outcome in allowed:
        lines.append(f'campaignos_outbox_events_total{{outcome="{outcome}"}} {totals[outcome]}')
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
