"""Tests for the /version endpoint and the REST API architecture (Slice 1)."""

from __future__ import annotations

from app.meta import API_VERSION, APP_NAME, APP_VERSION
from fastapi.testclient import TestClient


def test_version_endpoint_returns_metadata(client: TestClient) -> None:
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == APP_NAME
    assert body["version"] == APP_VERSION
    assert body["api_version"] == API_VERSION
    assert "app_env" in body


def test_version_response_shape_is_exact(client: TestClient) -> None:
    body = client.get("/api/v1/version").json()

    assert set(body) == {"name", "version", "api_version", "app_env"}


def test_version_matches_openapi_app_version(client: TestClient) -> None:
    # The app factory and the /version endpoint share app.meta, so they cannot drift.
    reported = client.get("/api/v1/version").json()["version"]
    openapi_version = client.get("/openapi.json").json()["info"]["version"]

    assert reported == openapi_version == APP_VERSION


def test_health_endpoints_still_available(client: TestClient) -> None:
    # Slice 1 adds /version without disturbing the foundation's health routes.
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health/live").status_code == 200


def test_only_expected_route_prefixes_are_mounted(client: TestClient) -> None:
    paths = set(client.get("/openapi.json").json()["paths"])

    assert paths == {
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/api/v1/version",
        "/api/v1/scans",
        "/api/v1/scans/{job_id}",
    }
