"""Static application metadata.

Single source of truth for the service name and version, shared by the FastAPI application
factory (title/version) and the ``/version`` endpoint so the two can never drift.
"""

from __future__ import annotations

APP_NAME = "AI SAST Platform"
APP_VERSION = "0.1.0"
API_VERSION = "v1"
