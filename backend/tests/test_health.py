"""Smoke tests for the backend skeleton."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ops_lists_all_six():
    resp = client.get("/ops")
    assert resp.status_code == 200
    names = {entry["op"] for entry in resp.json()}
    assert names == {"trim", "cut", "remove_silence", "speed", "caption", "extract_audio"}


def test_unknown_job_returns_404():
    resp = client.get("/jobs/does-not-exist")
    assert resp.status_code == 404


def test_edit_unknown_job_returns_404():
    resp = client.post("/edit", json={"job_id": "nope", "command": "trim to 30s"})
    assert resp.status_code == 404


def test_upload_rejects_bad_extension():
    resp = client.post(
        "/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
