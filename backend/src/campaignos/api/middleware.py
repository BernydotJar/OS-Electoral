"""Cross-cutting HTTP controls."""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

CORRELATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


async def request_controls(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    supplied = request.headers.get("x-correlation-id", "")
    request.state.correlation_id = supplied if CORRELATION_ID.fullmatch(supplied) else str(uuid4())
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response
