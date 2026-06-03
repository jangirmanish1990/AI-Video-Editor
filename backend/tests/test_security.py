"""Security hardening tests: filename sanitization, rate limiting, content
validation, and the command-length cap.
"""
import shutil
import subprocess

import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.jobs import store
from backend.main import app
from backend.security import RateLimiter, safe_filename

client = TestClient(app)
skip_no_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def test_safe_filename_strips_traversal():
    assert safe_filename("../../etc/passwd") == "passwd"
    assert safe_filename("..\\..\\windows\\system32\\evil.mp4") == "evil.mp4"
    assert safe_filename("my video (final).mp4") == "my_video__final_.mp4"
    assert safe_filename("") == "video"
    assert safe_filename(None) == "video"


def test_rate_limiter_blocks_after_max():
    rl = RateLimiter(max_requests=2, window_s=60)
    rl.check("ip-a")
    rl.check("ip-a")
    with pytest.raises(HTTPException) as exc:
        rl.check("ip-a")
    assert exc.value.status_code == 429
    # A different client is unaffected.
    rl.check("ip-b")


def test_rate_limiter_window_expiry():
    rl = RateLimiter(max_requests=1, window_s=0)  # window of 0 -> always expired
    rl.check("ip")
    rl.check("ip")  # would raise if the window hadn't expired


def test_edit_rejects_overlong_command():
    job = store.create_job(filename="x.mp4")
    resp = client.post("/edit", json={"job_id": job.job_id, "command": "x" * 2000})
    assert resp.status_code == 422  # pydantic max_length


def test_edit_rejects_empty_command():
    job = store.create_job(filename="x.mp4")
    resp = client.post("/edit", json={"job_id": job.job_id, "command": ""})
    assert resp.status_code == 422


def test_upload_rejects_non_video_content(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.routes.upload.settings.upload_dir", str(tmp_path))
    monkeypatch.setattr("backend.routes.upload.transcribe", lambda p: [])
    # Valid extension, garbage bytes -> ffprobe finds no video stream -> rejected.
    resp = client.post(
        "/upload",
        files={"file": ("fake.mp4", b"this is not a video", "video/mp4")},
    )
    assert resp.status_code == 400


@skip_no_ffmpeg
def test_upload_accepts_real_video(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.routes.upload.settings.upload_dir", str(tmp_path))
    monkeypatch.setattr("backend.routes.upload.transcribe", lambda p: [])
    src = tmp_path / "real.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-shortest", str(src)],
        check=True, capture_output=True,
    )
    with open(src, "rb") as handle:
        resp = client.post("/upload", files={"file": ("real.mp4", handle.read(), "video/mp4")})
    assert resp.status_code == 200
