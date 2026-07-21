"""RFC 9457-compatible structured API errors."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict


class ProblemException(Exception):
    """Raise one sanitized structured problem with a stable application code."""

    def __init__(
        self,
        *,
        status: int,
        title: str,
        detail: str,
        code: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.code = code
        self.headers = headers


class ProblemDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: str
    correlation_id: str
    errors: list[dict[str, Any]] | None = None


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    payload = ProblemDetail(
        type=f"https://campaignos.example/problems/{code.lower()}",
        title=title,
        status=status,
        detail=detail,
        instance=request.url.path,
        code=code,
        correlation_id=_correlation_id(request),
        errors=errors,
    )
    return JSONResponse(
        status_code=status,
        content=payload.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProblemException)
    async def handle_problem_exception(request: Request, exc: ProblemException) -> JSONResponse:
        response = problem_response(
            request,
            status=exc.status,
            title=exc.title,
            detail=exc.detail,
            code=exc.code,
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        campaign_collection_create = (
            request.method == "POST"
            and request.url.path.startswith("/api/v1/tenants/")
            and request.url.path.endswith("/campaigns")
        )
        missing_idempotency_header = any(
            error.get("type") == "missing"
            and tuple(str(part).lower() for part in error.get("loc", ()))
            == ("header", "idempotency-key")
            for error in exc.errors()
        )
        if campaign_collection_create and missing_idempotency_header:
            return problem_response(
                request,
                status=status.HTTP_428_PRECONDITION_REQUIRED,
                title="Precondition required",
                detail="Idempotency-Key is required for campaign creation",
                code="PRECONDITION_REQUIRED",
            )
        safe_errors = [
            {"location": list(item["loc"]), "message": item["msg"], "type": item["type"]}
            for item in exc.errors()
        ]
        return problem_response(
            request,
            status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Validation failed",
            detail="One or more request fields are invalid",
            code="VALIDATION_ERROR",
            errors=safe_errors,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request rejected"
        error_metadata = {
            400: ("Invalid request", "INVALID_REQUEST"),
            401: ("Authentication required", "AUTHENTICATION_REQUIRED"),
            403: ("Authorization denied", "AUTHORIZATION_DENIED"),
            404: ("Resource not found", "RESOURCE_NOT_FOUND"),
            409: ("Request conflict", "IDEMPOTENCY_CONFLICT"),
            412: ("Precondition failed", "VERSION_CONFLICT"),
            428: ("Precondition required", "VERSION_REQUIRED"),
            503: ("Service unavailable", "AUTHORIZATION_UNAVAILABLE"),
        }
        title, code = error_metadata.get(
            exc.status_code,
            ("Request rejected", "HTTP_ERROR"),
        )
        response = problem_response(
            request,
            status=exc.status_code,
            title=title,
            detail=detail,
            code=code,
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request.app.state.logger.exception(
            "unhandled_request_error",
            extra={"correlation_id": _correlation_id(request)},
            exc_info=exc,
        )
        return problem_response(
            request,
            status=500,
            title="Internal server error",
            detail="The request could not be completed",
            code="INTERNAL_ERROR",
        )
