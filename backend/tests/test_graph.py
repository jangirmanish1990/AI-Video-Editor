"""Tests for the assembled graph + runner. parse is mocked; execute/validate
run real FFmpeg so the wiring is genuinely exercised.
"""
import shutil
import subprocess

import pytest

from backend.agent import runner, validator
from backend.processing.probe import probe_metadata

skip_no_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def _make_video(path, seconds=4):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=160x120:rate=10",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-shortest", str(path)],
        check=True, capture_output=True,
    )


class _Job:
    def __init__(self, **kw):
        self.job_id = "j1"
        self.command = ""
        self.video_path = ""
        self.transcript = None
        self.metadata = {}
        self.status = "created"
        self.output_path = None
        self.results = []
        self.error = None
        self.__dict__.update(kw)


def test_validate_missing_output_errors():
    out = validator.validate_output({"status": "validating", "output_path": "/no/such.mp4"})
    assert out["status"] == "error"


def test_validate_passthrough_on_upstream_error():
    out = validator.validate_output({"status": "error", "error": "boom"})
    assert out == {}


@skip_no_ffmpeg
def test_run_agent_full_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.agent.executor.settings.upload_dir", str(tmp_path))
    monkeypatch.setattr(
        "backend.agent.parser.parse_command",
        lambda state: {"plan": [{"op": "trim", "params": {"start": 0, "end": 2}}],
                       "status": "executing"},
    )
    src = tmp_path / "src.mp4"
    _make_video(src, 4)
    job = _Job(video_path=str(src), command="trim to 2s", metadata={"duration_s": 4})

    events = []
    runner.run_agent(job, events.append)

    types = [e["type"] for e in events]
    assert types[0] == "status" and events[0]["status"] == "planning"
    assert "plan" in types and "progress" in types
    assert events[-1]["type"] == "status" and events[-1]["status"] == "done"
    assert job.status == "done" and job.output_path
    assert probe_metadata(job.output_path)["duration_s"] < 2.6


def test_run_agent_parse_error_short_circuits(monkeypatch):
    monkeypatch.setattr(
        "backend.agent.parser.parse_command",
        lambda state: {"status": "error", "error": "could not understand"},
    )
    job = _Job(video_path="x.mp4", command="gibberish")
    events = []
    runner.run_agent(job, events.append)

    assert events[-1]["type"] == "error"
    assert job.status == "error"
    # never reached execution
    assert "progress" not in [e["type"] for e in events]
