"""Application-wide mapping of typed domain exceptions to HTTP responses.

Registered on the app in the factory so any endpoint can simply let a typed exception propagate
(e.g. ``ScanJobStore.get`` raising :class:`ScanJobNotFoundError`) and receive the right status
code without per-endpoint try/except. Request-validation errors keep FastAPI's default 422.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.jobs import DuplicateScanJobError, ScanJobNotFoundError


def _not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


def _conflict_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    """Wire the domain-exception → HTTP-status mapping onto ``app``."""

    app.add_exception_handler(ScanJobNotFoundError, _not_found_handler)
    app.add_exception_handler(DuplicateScanJobError, _conflict_handler)
