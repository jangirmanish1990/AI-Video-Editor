"""Route coverage for upload / jobs / download (generated via the test-writer
sub-agent). Transcription is stubbed so uploads never hit the Whisper API.
"""
import shutil
import subprocess

import pytest

from fastapi.testclient import TestClient

from backend.jobs import store
from backend.main import app

client = TestClient(app)
skip_no_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def _make_video(path, seconds=2):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=160x120:rate=10",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-shortest", str(path)],
        check=True, capture_output=True,
    )


@skip_no_ffmpeg
def test_upload_returns_real_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.routes.upload.settings.upload_dir", str(tmp_path))
    monkeypatch.setattr("backend.routes.upload.transcribe", lambda path: [])  # no Whisper call
    src = tmp_path / "clip.mp4"
    _make_video(src, 2)

    with open(src, "rb") as handle:
        resp = client.post("/upload", files={"file": ("clip.mp4", handle.read(), "video/mp4")})

    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["metadata"]["width"] == 160 and data["metadata"]["height"] == 120
    assert data["metadata"]["duration_s"] > 0
    assert data["metadata"]["has_audio"] is True


def test_jobs_lookup_returns_public_record():
    job = store.create_job(filename="x.mp4")
    job.metadata = {"duration_s": 3.0}
    resp = client.get(f"/jobs/{job.job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job.job_id
    # server-only fields are stripped by to_public()
    assert "video_path" not in body and "transcript" not in body


def test_download_without_output_is_404():
    job = store.create_job(filename="x.mp4")
    resp = client.get(f"/download/{job.job_id}")
    assert resp.status_code == 404


def test_download_unknown_job_is_404():
    assert client.get("/download/missing").status_code == 404


def test_upload_oversize_rejected(monkeypatch):
    monkeypatch.setattr("backend.routes.upload.settings.max_upload_mb", 0)
    payload = b"\x00" * (1024 * 1024)  # 1 MB, exceeds the 0 MB cap
    resp = client.post("/upload", files={"file": ("big.mp4", payload, "video/mp4")})
    assert resp.status_code == 400


@skip_no_ffmpeg
def test_silences_endpoint_detects_gap(tmp_path):
    # 1s tone, 2s silence, 1s tone -> at least one silent interval.
    src = tmp_path / "gap.mp4"
    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i", "testsrc=duration=4:size=160x120:rate=10",
         "-f", "lavfi", "-i",
         "aevalsrc='sin(2*PI*440*t)*lt(t,1)+sin(2*PI*440*t)*gt(t,3)':d=4",
         "-shortest", str(src)],
        check=True, capture_output=True,
    )
    job = store.create_job(filename="gap.mp4")
    job.video_path = str(src)
    job.metadata = {"duration_s": 4, "has_audio": True}

    resp = client.get(f"/silences/{job.job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert "silences" in body
    assert len(body["silences"]) >= 1
    first = body["silences"][0]
    assert "start" in first and "end" in first


def test_silences_unknown_job_is_404():
    assert client.get("/silences/missing").status_code == 404


def test_silences_no_audio_returns_empty():
    job = store.create_job(filename="x.mp4")
    job.video_path = "x.mp4"
    job.metadata = {"duration_s": 5.0, "has_audio": False}
    resp = client.get(f"/silences/{job.job_id}")
    assert resp.status_code == 200
    assert resp.json()["silences"] == []


@skip_no_ffmpeg
def test_audio_upload_attaches_music(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.routes.upload.settings.upload_dir", str(tmp_path))
    music = tmp_path / "song.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=1", str(music)],
        check=True, capture_output=True,
    )
    job = store.create_job(filename="v.mp4")
    with open(music, "rb") as handle:
        resp = client.post(
            f"/audio/{job.job_id}",
            files={"file": ("song.mp3", handle.read(), "audio/mpeg")},
        )
    assert resp.status_code == 200
    assert store.get_job(job.job_id).music_path is not None


def test_audio_upload_rejects_non_audio(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.routes.upload.settings.upload_dir", str(tmp_path))
    job = store.create_job(filename="v.mp4")
    resp = client.post(
        f"/audio/{job.job_id}",
        files={"file": ("fake.mp3", b"not audio at all", "audio/mpeg")},
    )
    assert resp.status_code == 400


def test_audio_upload_unknown_job_404():
    resp = client.post("/audio/missing", files={"file": ("s.mp3", b"x", "audio/mpeg")})
    assert resp.status_code == 404


@skip_no_ffmpeg
def test_broll_upload_attaches_clip(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.routes.upload.settings.upload_dir", str(tmp_path))
    clip = tmp_path / "b.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=10", str(clip)],
        check=True, capture_output=True,
    )
    job = store.create_job(filename="v.mp4")
    with open(clip, "rb") as handle:
        resp = client.post(
            f"/broll/{job.job_id}",
            files={"file": ("b.mp4", handle.read(), "video/mp4")},
        )
    assert resp.status_code == 200
    assert store.get_job(job.job_id).broll_path is not None


def test_broll_upload_unknown_job_404():
    resp = client.post("/broll/missing", files={"file": ("b.mp4", b"x", "video/mp4")})
    assert resp.status_code == 404
