"""Tests for the execute_plan node: real op chaining, output, failure paths."""
import shutil
import subprocess

import pytest

from backend.agent import executor
from backend.processing.probe import probe_metadata

ffmpeg_missing = shutil.which("ffmpeg") is None
skip_no_ffmpeg = pytest.mark.skipif(ffmpeg_missing, reason="ffmpeg not installed")


def _make_test_video(path, seconds=4):
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=160x120:rate=10",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
            "-shortest", str(path),
        ],
        check=True,
        capture_output=True,
    )


@skip_no_ffmpeg
def test_executor_runs_trim_then_speed(tmp_path, monkeypatch):
    monkeypatch.setattr(executor.settings, "upload_dir", str(tmp_path))
    src = tmp_path / "src.mp4"
    _make_test_video(src, seconds=4)

    state = {
        "job_id": "t1",
        "video_path": str(src),
        "plan": [
            {"op": "trim", "params": {"start": 0, "end": 2}},
            {"op": "speed", "params": {"factor": 2.0}},
        ],
    }
    out = executor.execute_plan(state)

    assert out["status"] == "validating"
    assert len(out["results"]) == 2
    assert all(r["status"] == "ok" for r in out["results"])

    final = probe_metadata(out["output_path"])
    # 4s -> trim to 2s -> 2x speed -> ~1s
    assert 0.5 < final["duration_s"] < 1.6


@skip_no_ffmpeg
def test_executor_progress_callback(tmp_path, monkeypatch):
    monkeypatch.setattr(executor.settings, "upload_dir", str(tmp_path))
    src = tmp_path / "src.mp4"
    _make_test_video(src, seconds=2)

    seen = []
    state = {"job_id": "t2", "video_path": str(src),
             "plan": [{"op": "trim", "params": {"start": 0, "end": 1}}]}
    executor.execute_plan(state, on_progress=lambda **kw: seen.append(kw))

    assert seen == [{"op": "trim", "index": 1, "total": 1}]


def test_executor_no_input_errors():
    out = executor.execute_plan({"job_id": "x", "plan": [{"op": "trim", "params": {}}]})
    assert out["status"] == "error"


def test_executor_unimplemented_op_errors(tmp_path):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"\x00")
    out = executor.execute_plan(
        {"job_id": "x", "video_path": str(src), "plan": [{"op": "caption", "params": {}}]}
    )
    assert out["status"] == "error"
    assert out["results"][0]["op"] == "caption"
