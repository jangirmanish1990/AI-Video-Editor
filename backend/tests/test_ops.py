"""Tests for the processing layer: extract_audio op, ffprobe, transcription."""
import shutil
import subprocess

import pytest

from backend import transcription
from backend.config import settings
from backend.processing.ops import extract_audio
from backend.processing.probe import probe_metadata

ffmpeg_missing = shutil.which("ffmpeg") is None
skip_no_ffmpeg = pytest.mark.skipif(ffmpeg_missing, reason="ffmpeg not installed")


def _make_test_video(path):
    """1-second 128x96 clip with a 440Hz sine audio track."""
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=128x96:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-shortest", str(path),
        ],
        check=True,
        capture_output=True,
    )


@skip_no_ffmpeg
def test_extract_audio_produces_mp3(tmp_path):
    src = tmp_path / "src.mp4"
    _make_test_video(src)
    out = tmp_path / "out.mp3"

    result = extract_audio.run(str(src), str(out), {"format": "mp3"})

    assert result["output_path"] == str(out)
    assert out.exists() and out.stat().st_size > 0


@skip_no_ffmpeg
def test_probe_reads_metadata(tmp_path):
    src = tmp_path / "src.mp4"
    _make_test_video(src)

    meta = probe_metadata(str(src))

    assert meta["width"] == 128 and meta["height"] == 96
    assert meta["duration_s"] > 0
    assert meta["has_audio"] is True


def test_probe_bad_file_fails_soft(tmp_path):
    bogus = tmp_path / "not_a_video.mp4"
    bogus.write_bytes(b"\x00\x01\x02")
    meta = probe_metadata(str(bogus))
    assert meta["duration_s"] == 0.0 and meta["has_audio"] is False


def test_transcribe_without_key_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    assert transcription.transcribe("anything.mp4") is None
