"""Verifies the /ws/{job_id} stream still matches the schema the frontend's
useJobSocket consumes (specs/api.md), now driven by the REAL agent. parse is
mocked (no API key/cost); execute + validate run real FFmpeg.
"""
import shutil
import subprocess

import pytest
from starlette.websockets import WebSocketDisconnect

from fastapi.testclient import TestClient

from backend.jobs import store
from backend.main import app

client = TestClient(app)
skip_no_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def _make_video(path, seconds=4):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=160x120:rate=10",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-shortest", str(path)],
        check=True, capture_output=True,
    )


@skip_no_ffmpeg
def test_ws_streams_real_agent(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.agent.executor.settings.upload_dir", str(tmp_path))
    monkeypatch.setattr(
        "backend.agent.parser.parse_command",
        lambda state: {"plan": [{"op": "trim", "params": {"start": 0, "end": 2}}],
                       "status": "executing"},
    )
    src = tmp_path / "src.mp4"
    _make_video(src, 4)

    job = store.create_job(filename="src.mp4")
    job.video_path = str(src)
    job.metadata = {"duration_s": 4}

    resp = client.post("/edit", json={"job_id": job.job_id, "command": "trim to 2s"})
    assert resp.status_code == 202

    types_seen, result = [], None
    with client.websocket_connect(f"/ws/{job.job_id}") as ws:
        try:
            while True:
                msg = ws.receive_json()
                types_seen.append(msg["type"])
                if msg["type"] == "result":
                    result = msg
        except WebSocketDisconnect:
            pass

    assert {"status", "plan", "progress", "result"}.issubset(set(types_seen))
    assert result and result["output_url"].endswith(job.job_id)
    assert job.status == "done"


def test_ws_unknown_job_reports_error():
    with client.websocket_connect("/ws/nonexistent") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
