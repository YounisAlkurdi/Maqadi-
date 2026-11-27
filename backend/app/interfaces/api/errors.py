"""Centralized mapping from domain errors and validation errors to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import (
    DomainError,
    DuplicateItemError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    RateLimitedError,
    UnauthorizedError,
    ValidationError,
)


def _error_payload(code: str, message: str, *, existing_item_id: str | None = None) -> dict:
    detail: dict[str, str] = {"code": code, "message": message}
    if existing_item_id is not None:
        detail["existing_item_id"] = existing_item_id
    return {"error": detail}


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(DomainError)
    async def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        status_code = 400
        existing_id: str | None = None

        if isinstance(exc, UnauthorizedError):
            status_code = 401
        elif isinstance(exc, ForbiddenError):
            status_code = 403
        elif isinstance(exc, NotFoundError):
            status_code = 404
        elif isinstance(exc, DuplicateItemError):
            status_code = 409
            existing_id = exc.existing_item_id
        elif isinstance(exc, (InvalidTransitionError, ValidationError)):
            status_code = 422
        elif isinstance(exc, RateLimitedError):
            status_code = 429

        return JSONResponse(
            status_code=status_code,
            content=_error_payload(exc.code, exc.message, existing_item_id=existing_id),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first_err = exc.errors()[0] if exc.errors() else {}
        msg = str(first_err.get("msg", "Invalid request"))
        return JSONResponse(
            status_code=422,
            content=_error_payload("validation_error", msg),
        )
