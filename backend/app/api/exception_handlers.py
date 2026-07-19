"""Application-wide mapping of typed domain exceptions to HTTP responses.

Registered on the app in the factory so any endpoint can simply let a typed exception propagate
(e.g. ``ScanJobStore.get`` raising :class:`ScanJobNotFoundError`) and receive the right status
code without per-endpoint try/except. Request-validation errors keep FastAPI's default 422.
"""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.services.jobs import DuplicateScanJobError, ScanJobNotFoundError


def _not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


def _conflict_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Translate a domain-model ``ValidationError`` (e.g. an invalid ScanConfig built from form
    fields) into HTTP 422, so validation logic can stay transport-agnostic and raise only
    ``ValidationError``."""

    errors = cast(ValidationError, exc).errors()
    detail = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in errors
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": detail}
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire the domain-exception → HTTP-status mapping onto ``app``."""

    app.add_exception_handler(ScanJobNotFoundError, _not_found_handler)
    app.add_exception_handler(DuplicateScanJobError, _conflict_handler)
    app.add_exception_handler(ValidationError, _validation_error_handler)
