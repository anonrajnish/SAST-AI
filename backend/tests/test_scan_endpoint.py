"""Tests for the scan endpoints (REST API — multipart upload + read side)."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.config import Settings, get_settings
from app.dependencies import get_scan_job_store
from app.main import create_app
from app.services.jobs import ScanJob, ScanJobStatus, ScanJobStore, create_scan_job
from app.services.scan import ScanExecutionError
from app.services.upload import ArchiveTooLargeError, stream_zip_to_temp
from fastapi.testclient import TestClient

_MD5_PY = "import hashlib\nx = hashlib.md5(d)\n"  # weak-crypto finding (python)
_SECRET_JS = 'const password = "S3cr3t-Example";\n'  # hardcoded secret (web)


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


def _zip_bytes(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buffer.getvalue()


def _zip_slip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(zipfile.ZipInfo("../evil.py"), "pwned\n")
    return buffer.getvalue()


def _post(
    client: TestClient,
    content: bytes,
    *,
    filename: str = "repo.zip",
    data: dict[str, object] | None = None,
) -> object:
    return client.post(
        "/api/v1/scans",
        files={"file": (filename, content, "application/zip")},
        data=data or {},
    )


# --- successful multipart scan ---------------------------------------------------------


def test_successful_scan_returns_completed_job(
    client: TestClient, store: ScanJobStore
) -> None:
    response = _post(client, _zip_bytes({"a.py": _MD5_PY}))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["result"]["scan"]["scan"]["total_findings"] >= 1
    assert store.get(body["job_id"]).status is ScanJobStatus.COMPLETED


def test_successful_scan_honors_manual_config(client: TestClient) -> None:
    response = _post(
        client,
        _zip_bytes({"a.py": _MD5_PY, "b.js": _SECRET_JS}),
        data={"mode": "manual", "groups": ["python"]},
    )

    assert response.status_code == 200
    scan = response.json()["result"]["scan"]["scan"]
    assert scan["resolved_language_groups"] == ["python"]
    assert {f["location"]["file"] for f in scan["findings"]} == {"a.py"}


# --- invalid requests (422/413, no job created) ----------------------------------------


def test_missing_file_is_422(client: TestClient, store: ScanJobStore) -> None:
    response = client.post("/api/v1/scans", data={"mode": "auto"})

    assert response.status_code == 422
    assert store.list() == ()


def test_invalid_config_auto_with_groups_is_422(
    client: TestClient, store: ScanJobStore
) -> None:
    response = _post(
        client, _zip_bytes({"a.py": _MD5_PY}), data={"mode": "auto", "groups": ["python"]}
    )

    assert response.status_code == 422
    assert store.list() == ()


def test_invalid_config_manual_without_groups_is_422(
    client: TestClient, store: ScanJobStore
) -> None:
    response = _post(client, _zip_bytes({"a.py": _MD5_PY}), data={"mode": "manual"})

    assert response.status_code == 422
    assert store.list() == ()


def test_oversize_upload_via_content_length_is_413(
    client: TestClient, store: ScanJobStore
) -> None:
    client.app.dependency_overrides[get_settings] = lambda: Settings(
        extraction_max_archive_bytes=50
    )

    response = _post(client, _zip_bytes({"a.py": _MD5_PY}))

    assert response.status_code == 413
    assert store.list() == ()


def test_oversize_upload_via_streaming_cap_is_413(
    client: TestClient, store: ScanJobStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _too_large(source: object, *, max_bytes: int) -> Path:
        raise ArchiveTooLargeError(max_bytes + 1, max_bytes)

    monkeypatch.setattr("app.api.v1.scans.stream_zip_to_temp", _too_large)

    response = _post(client, _zip_bytes({"a.py": _MD5_PY}))

    assert response.status_code == 413
    assert store.list() == ()


def test_json_archive_path_body_is_no_longer_accepted(client: TestClient) -> None:
    # The server-side archive_path input was removed; a JSON body has no file field.
    response = client.post("/api/v1/scans", json={"archive_path": "/etc/passwd.zip"})

    assert response.status_code == 422


# --- upload / scan failures (recorded as a FAILED job, HTTP 200) ------------------------


def test_corrupted_upload_fails_the_job(
    client: TestClient, store: ScanJobStore
) -> None:
    response = _post(client, b"this is not a zip archive")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "CorruptedArchiveError" in body["error"]
    assert store.get(body["job_id"]).status is ScanJobStatus.FAILED


def test_zip_slip_upload_fails_the_job(client: TestClient) -> None:
    response = _post(client, _zip_slip_bytes())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "PathTraversalError" in body["error"]


def test_scan_execution_failure_fails_the_job(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(path: Path, config: object, **kwargs: object) -> None:
        raise ScanExecutionError("weak-crypto-scanner", RuntimeError("kaboom"))

    monkeypatch.setattr("app.api.v1.scans.scan_archive", _boom)

    response = _post(client, _zip_bytes({"a.py": _MD5_PY}))

    assert response.status_code == 200
    assert "weak-crypto-scanner" in response.json()["error"]


def test_resource_limit_yields_failed_job(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The file-count limit is enforced inside the extractor (which reads settings directly).
    monkeypatch.setattr(
        "app.services.upload.extractor.get_settings",
        lambda: Settings(extraction_max_file_count=1),
    )

    response = _post(client, _zip_bytes({"a.py": _MD5_PY, "b.py": "x = 1\n"}))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "FileCountLimitError" in body["error"]


# --- temp-file cleanup -----------------------------------------------------------------


def test_upload_temp_file_removed_on_success(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Path] = {}

    def _spy(source: io.BufferedReader, *, max_bytes: int) -> Path:
        path = stream_zip_to_temp(source, max_bytes=max_bytes, directory=tmp_path)
        captured["path"] = path
        return path

    monkeypatch.setattr("app.api.v1.scans.stream_zip_to_temp", _spy)

    assert _post(client, _zip_bytes({"a.py": _MD5_PY})).status_code == 200
    assert captured["path"].parent == tmp_path
    assert not captured["path"].exists()  # deleted in the endpoint's finally


def test_upload_temp_file_removed_on_failure(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Path] = {}

    def _spy(source: io.BufferedReader, *, max_bytes: int) -> Path:
        path = stream_zip_to_temp(source, max_bytes=max_bytes, directory=tmp_path)
        captured["path"] = path
        return path

    monkeypatch.setattr("app.api.v1.scans.stream_zip_to_temp", _spy)

    assert _post(client, b"not a zip").status_code == 200  # FAILED job
    assert not captured["path"].exists()


# --- response serialization ------------------------------------------------------------


def test_response_serializes_and_round_trips(
    client: TestClient, store: ScanJobStore
) -> None:
    body = _post(client, _zip_bytes({"a.py": _MD5_PY})).json()

    assert set(body) == {"job_id", "status", "created_at", "completed_at", "result", "error"}
    assert ScanJob.model_validate(body) == store.get(body["job_id"])


def test_store_provider_returns_a_cached_singleton() -> None:
    get_scan_job_store.cache_clear()
    first = get_scan_job_store()

    assert isinstance(first, ScanJobStore)
    assert get_scan_job_store() is first


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
    store.create(create_scan_job(job_id="b", created_at=_T1))
    store.create(create_scan_job(job_id="a", created_at=_T0))
    store.create(create_scan_job(job_id="c", created_at=_T1))

    response = client.get("/api/v1/scans")

    assert [job["job_id"] for job in response.json()] == ["a", "b", "c"]


def test_list_scans_reflects_a_submitted_scan(client: TestClient) -> None:
    posted = _post(client, _zip_bytes({"a.py": _MD5_PY})).json()

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
    assert ScanJob.model_validate(body) == store.get("job-1")


def test_get_missing_scan_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/scans/does-not-exist")

    assert response.status_code == 404
    assert "does-not-exist" in response.json()["detail"]


def test_duplicate_job_maps_to_409(
    client: TestClient, store: ScanJobStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    store.create(create_scan_job(job_id="collision", created_at=_T0))
    monkeypatch.setattr(
        "app.api.v1.scans.create_scan_job",
        lambda: create_scan_job(job_id="collision", created_at=_T0),
    )

    response = _post(client, _zip_bytes({"a.py": _MD5_PY}))

    assert response.status_code == 409
    assert "collision" in response.json()["detail"]
