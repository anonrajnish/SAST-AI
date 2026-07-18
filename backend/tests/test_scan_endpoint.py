"""Tests for the scan endpoints (REST API — scan endpoint Slices 1-2).

Slice 1: POST /api/v1/scans (write side). Slice 2: GET /api/v1/scans and
GET /api/v1/scans/{job_id} (read side) + typed-exception status mapping.
"""

from __future__ import annotations

import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.config import Settings
from app.dependencies import get_scan_job_store
from app.main import create_app
from app.services.jobs import ScanJob, ScanJobStatus, ScanJobStore, create_scan_job
from app.services.scan import ScanExecutionError
from fastapi.testclient import TestClient

_MD5_PY = "import hashlib\nx = hashlib.md5(d)\n"  # weak-crypto finding (python)


@pytest.fixture
def store() -> ScanJobStore:
    return ScanJobStore()


@pytest.fixture
def client(store: ScanJobStore) -> Iterator[TestClient]:
    """A TestClient whose scan-job store is a fresh, isolated instance."""

    app = create_app()
    app.dependency_overrides[get_scan_job_store] = lambda: store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _make_zip(path: Path, files: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return path


def test_store_provider_returns_a_cached_singleton() -> None:
    get_scan_job_store.cache_clear()
    first = get_scan_job_store()

    assert isinstance(first, ScanJobStore)
    assert get_scan_job_store() is first  # cached process-wide singleton


# --- successful scan -------------------------------------------------------------------


def test_successful_scan_returns_completed_job(
    client: TestClient, store: ScanJobStore, tmp_path: Path
) -> None:
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})

    response = client.post("/api/v1/scans", json={"archive_path": str(archive)})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["error"] is None
    assert body["result"]["scan"]["scan"]["total_findings"] >= 1
    # The job was created and then updated to COMPLETED in the shared store.
    stored = store.get(body["job_id"])
    assert stored.status is ScanJobStatus.COMPLETED
    assert [j.job_id for j in store.list()] == [body["job_id"]]


def test_successful_scan_honors_manual_config(
    client: TestClient, tmp_path: Path
) -> None:
    archive = _make_zip(
        tmp_path / "mixed.zip",
        {"a.py": _MD5_PY, "b.js": 'const password = "S3cr3t-Example";\n'},
    )

    response = client.post(
        "/api/v1/scans",
        json={"archive_path": str(archive), "config": {"mode": "manual", "groups": ["python"]}},
    )

    assert response.status_code == 200
    scan = response.json()["result"]["scan"]["scan"]
    assert scan["resolved_language_groups"] == ["python"]
    assert {f["location"]["file"] for f in scan["findings"]} == {"a.py"}


# --- upload / scan failures (recorded as a FAILED job, HTTP 200) ------------------------


def test_missing_archive_fails_the_job(
    client: TestClient, store: ScanJobStore, tmp_path: Path
) -> None:
    response = client.post(
        "/api/v1/scans", json={"archive_path": str(tmp_path / "nope.zip")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["result"] is None
    assert body["error"]  # non-empty diagnostic
    assert store.get(body["job_id"]).status is ScanJobStatus.FAILED


def test_zip_slip_archive_fails_the_job(
    client: TestClient, tmp_path: Path
) -> None:
    archive = tmp_path / "slip.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(zipfile.ZipInfo("../evil.py"), "pwned\n")

    response = client.post("/api/v1/scans", json={"archive_path": str(archive)})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "PathTraversalError" in body["error"]


def test_scan_execution_failure_fails_the_job(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(path: Path, config: object, **kwargs: object) -> None:
        raise ScanExecutionError("weak-crypto-scanner", RuntimeError("kaboom"))

    monkeypatch.setattr("app.api.v1.scans.scan_archive", _boom)

    response = client.post(
        "/api/v1/scans", json={"archive_path": str(tmp_path / "repo.zip")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "weak-crypto-scanner" in body["error"]


def test_resource_limit_yields_failed_job(
    client: TestClient, store: ScanJobStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A resource-limit violation is an UploadError, so the endpoint behaves exactly like any
    # other upload failure: a FAILED job at HTTP 200 (endpoint contract unchanged by Slice 3).
    monkeypatch.setattr(
        "app.services.upload.extractor.get_settings",
        lambda: Settings(extraction_max_file_count=1),
    )
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY, "b.py": "x = 1\n"})

    response = client.post("/api/v1/scans", json={"archive_path": str(archive)})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "FileCountLimitError" in body["error"]
    assert store.get(body["job_id"]).status is ScanJobStatus.FAILED


# --- invalid requests (422, no job created) --------------------------------------------


def test_missing_archive_path_is_422(client: TestClient, store: ScanJobStore) -> None:
    response = client.post("/api/v1/scans", json={"config": {"mode": "auto"}})

    assert response.status_code == 422
    assert store.list() == ()  # nothing created for an invalid request


def test_unknown_field_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scans", json={"archive_path": "/x.zip", "bogus": 1}
    )

    assert response.status_code == 422


def test_invalid_config_auto_with_groups_is_422(
    client: TestClient, store: ScanJobStore
) -> None:
    response = client.post(
        "/api/v1/scans",
        json={"archive_path": "/x.zip", "config": {"mode": "auto", "groups": ["python"]}},
    )

    assert response.status_code == 422
    assert store.list() == ()


def test_invalid_config_manual_without_groups_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/scans",
        json={"archive_path": "/x.zip", "config": {"mode": "manual", "groups": []}},
    )

    assert response.status_code == 422


# --- response serialization ------------------------------------------------------------


def test_response_serializes_and_round_trips(
    client: TestClient, store: ScanJobStore, tmp_path: Path
) -> None:
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})

    body = client.post("/api/v1/scans", json={"archive_path": str(archive)}).json()

    assert set(body) == {"job_id", "status", "created_at", "completed_at", "result", "error"}
    # The response body reconstructs the exact ScanJob held in the store.
    restored = ScanJob.model_validate(body)
    assert restored == store.get(body["job_id"])


# --- read side: GET /api/v1/scans ------------------------------------------------------

_T0 = datetime(2026, 7, 19, 12, 0, 0, tzinfo=UTC)
_T1 = datetime(2026, 7, 19, 12, 0, 5, tzinfo=UTC)


def test_list_scans_empty(client: TestClient) -> None:
    response = client.get("/api/v1/scans")

    assert response.status_code == 200
    assert response.json() == []


def test_list_scans_is_deterministically_ordered(
    client: TestClient, store: ScanJobStore
) -> None:
    # Seed out of chronological order; the endpoint must return created_at-then-id order.
    store.create(create_scan_job(job_id="b", created_at=_T1))
    store.create(create_scan_job(job_id="a", created_at=_T0))
    store.create(create_scan_job(job_id="c", created_at=_T1))

    response = client.get("/api/v1/scans")

    assert response.status_code == 200
    assert [job["job_id"] for job in response.json()] == ["a", "b", "c"]


def test_list_scans_reflects_a_submitted_scan(
    client: TestClient, tmp_path: Path
) -> None:
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})
    posted = client.post("/api/v1/scans", json={"archive_path": str(archive)}).json()

    listing = client.get("/api/v1/scans").json()

    assert [job["job_id"] for job in listing] == [posted["job_id"]]
    assert listing[0]["status"] == "completed"


# --- read side: GET /api/v1/scans/{job_id} ---------------------------------------------


def test_get_existing_scan(client: TestClient, store: ScanJobStore) -> None:
    store.create(create_scan_job(job_id="job-1", created_at=_T0))

    response = client.get("/api/v1/scans/job-1")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == "job-1"
    assert body["status"] == "pending"
    # Round-trips back to the exact ScanJob in the store.
    assert ScanJob.model_validate(body) == store.get("job-1")


def test_get_missing_scan_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/scans/does-not-exist")

    assert response.status_code == 404
    assert "does-not-exist" in response.json()["detail"]


# --- typed-exception status mapping ----------------------------------------------------


def test_duplicate_job_maps_to_409(
    client: TestClient, store: ScanJobStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Force the POST path to create a job whose id already exists -> DuplicateScanJobError.
    store.create(create_scan_job(job_id="collision", created_at=_T0))
    monkeypatch.setattr(
        "app.api.v1.scans.create_scan_job",
        lambda: create_scan_job(job_id="collision", created_at=_T0),
    )
    archive = _make_zip(tmp_path / "repo.zip", {"a.py": _MD5_PY})

    response = client.post("/api/v1/scans", json={"archive_path": str(archive)})

    assert response.status_code == 409
    assert "collision" in response.json()["detail"]
