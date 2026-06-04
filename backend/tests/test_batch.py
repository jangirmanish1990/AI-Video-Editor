"""Tests for the /batch endpoint — validation, background execution, polling."""
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from backend.jobs import store as job_store
from backend.main import app

client = TestClient(app)
skip_no_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def _make_video(path, seconds=2):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"testsrc=duration={seconds}:size=160x120:rate=10",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
         "-shortest", str(path)],
        check=True, capture_output=True,
    )


def test_batch_rejects_unknown_jobs():
    resp = client.post("/batch", json={"job_ids": ["no-such-id"], "command": "trim to 5s"})
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


def test_batch_rejects_empty_command():
    job = job_store.create_job(filename="x.mp4")
    resp = client.post("/batch", json={"job_ids": [job.job_id], "command": ""})
    assert resp.status_code == 422


def test_batch_rejects_too_many_jobs():
    ids = [job_store.create_job(filename=f"{i}.mp4").job_id for i in range(11)]
    resp = client.post("/batch", json={"job_ids": ids, "command": "trim to 5s"})
    assert resp.status_code == 422


def test_batch_unknown_id_returns_404():
    assert client.get("/batch/nonexistent").status_code == 404


@skip_no_ffmpeg
def test_batch_processes_two_jobs(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.agent.executor.settings.upload_dir", str(tmp_path))
    monkeypatch.setattr(
        "backend.agent.parser.parse_command",
        lambda s: {"plan": [{"op": "trim", "params": {"start": 0, "end": 1}}],
                   "status": "executing"},
    )
    # Create two jobs with real videos.
    src1 = tmp_path / "a.mp4"
    _make_video(src1)
    src2 = tmp_path / "b.mp4"
    _make_video(src2)
    j1 = job_store.create_job(filename="a.mp4")
    j1.video_path = str(src1)
    j1.metadata = {"duration_s": 2}
    j2 = job_store.create_job(filename="b.mp4")
    j2.video_path = str(src2)
    j2.metadata = {"duration_s": 2}

    resp = client.post("/batch", json={
        "job_ids": [j1.job_id, j2.job_id],
        "command": "trim to 1 second",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["total"] == 2
    batch_id = data["batch_id"]

    # BackgroundTasks run inline in TestClient — batch is already done.
    poll = client.get(f"/batch/{batch_id}").json()
    assert poll["status"] == "done"
    assert poll["completed"] == 2
    assert all(r["status"] == "done" for r in poll["results"])
    assert all(r["output_url"] for r in poll["results"])
