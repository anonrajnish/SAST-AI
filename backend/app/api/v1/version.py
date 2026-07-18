"""Version endpoint: reports the service name, release version, and API version.

Read-only service metadata for clients and diagnostics. It touches no datastore and no
business subsystem (upload / scan / jobs); it only reads static metadata and the injected
settings, demonstrating the dependency-injection pattern future feature routers will reuse.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies import SettingsDep
from app.meta import API_VERSION, APP_NAME, APP_VERSION

router = APIRouter(prefix="/version", tags=["version"])


class VersionResponse(BaseModel):
    """Service metadata returned by ``GET /version``."""

    name: str
    version: str
    api_version: str
    app_env: str


@router.get("", response_model=VersionResponse)
def version(settings: SettingsDep) -> VersionResponse:
    """Report service metadata (name, release version, API version, environment)."""

    return VersionResponse(
        name=APP_NAME,
        version=APP_VERSION,
        api_version=API_VERSION,
        app_env=settings.app_env,
    )
