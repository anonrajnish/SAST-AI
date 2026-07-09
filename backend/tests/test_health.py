"""Tests for the health/liveness/readiness endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app_env" in body


def test_liveness(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_reports_known_status(client: TestClient) -> None:
    # No database is running in the unit-test environment, so readiness reports
    # not_ready/503; with a database it reports ready/200. Both are valid.
    response = client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert body["status"] in ("ready", "not_ready")
    assert body["database"] in ("ok", "unavailable")
