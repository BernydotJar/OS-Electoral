"""Cross-cutting HTTP security and telemetry controls."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

from campaignos.observability import MetricsRegistry, normalize_route_label, resolve_trace_context

CORRELATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


async def request_controls(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    supplied = request.headers.get("x-correlation-id", "")
    request.state.correlation_id = supplied if CORRELATION_ID.fullmatch(supplied) else str(uuid4())
    trace = resolve_trace_context(request.headers.get("traceparent"))
    request.state.trace_id = trace.trace_id
    request.state.span_id = trace.span_id
    metrics: MetricsRegistry = request.app.state.metrics
    metrics.request_started()
    started = perf_counter()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = (perf_counter() - started) * 1000
        status_code = response.status_code if response is not None else 500
        route = normalize_route_label(request.scope.get("route"), request.url.path)
        metrics.request_finished(
            method=request.method,
            route=route,
            status_code=status_code,
            duration_ms=duration_ms,
        )
        request.app.state.logger.info(
            "http_request_completed",
            extra={
                "correlation_id": request.state.correlation_id,
                "trace_id": trace.trace_id,
                "span_id": trace.span_id,
                "method": request.method,
                "route": route,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 3),
            },
        )
        if response is not None:
            response.headers["X-Correlation-ID"] = request.state.correlation_id
            response.headers["traceparent"] = trace.traceparent
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Cache-Control"] = "no-store"
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )
