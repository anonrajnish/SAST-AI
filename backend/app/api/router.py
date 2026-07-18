"""Top-level API router aggregating versioned routers.

Future feature routers (e.g. scan endpoints) are mounted here alongside the current
health/version routers — this aggregator is the single extension point for the v1 API.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import health, version

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(version.router)
