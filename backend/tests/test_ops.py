"""Tests for the processing layer: extract_audio op, ffprobe, transcription."""
import shutil
import subprocess

import pytest

from backend import transcription
from backend.config import settings
from backend.processing.ops import caption, cut, extract_audio, remove_silence, speed, trim
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


@skip_no_ffmpeg
def test_trim_shortens_to_range(tmp_path):
    src = tmp_path / "src.mp4"
    _make_test_video(src)  # ~1s; remake longer for a meaningful trim
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=4:size=128x96:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-shortest", str(src)],
        check=True, capture_output=True,
    )
    out = tmp_path / "trim.mp4"
    trim.run(str(src), str(out), {"start": 1, "end": 3})
    assert 1.5 < probe_metadata(str(out))["duration_s"] < 2.5


@skip_no_ffmpeg
def test_cut_removes_middle(tmp_path):
    src = tmp_path / "src.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=4:size=128x96:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-shortest", str(src)],
        check=True, capture_output=True,
    )
    out = tmp_path / "cut.mp4"
    cut.run(str(src), str(out), {"start": 1, "end": 3})  # remove 2s of 4s -> ~2s
    assert 1.4 < probe_metadata(str(out))["duration_s"] < 2.6


@skip_no_ffmpeg
def test_speed_halves_duration(tmp_path):
    src = tmp_path / "src.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=4:size=128x96:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-shortest", str(src)],
        check=True, capture_output=True,
    )
    out = tmp_path / "fast.mp4"
    speed.run(str(src), str(out), {"factor": 2.0})  # 4s -> ~2s
    assert 1.5 < probe_metadata(str(out))["duration_s"] < 2.6


@skip_no_ffmpeg
def test_remove_silence_passthrough_when_no_silence(tmp_path):
    # Continuous tone => no silence detected => output ~ same length.
    src = tmp_path / "tone.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=3:size=128x96:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-shortest", str(src)],
        check=True, capture_output=True,
    )
    out = tmp_path / "desilenced.mp4"
    remove_silence.run(str(src), str(out), {"threshold_db": -40, "min_silence_ms": 500})
    assert probe_metadata(str(out))["duration_s"] > 2.0


@skip_no_ffmpeg
def test_remove_silence_drops_silent_gap(tmp_path):
    # 1s tone + 2s silence + 1s tone => removing silence should yield ~2s.
    src = tmp_path / "gapped.mp4"
    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i", "testsrc=duration=4:size=128x96:rate=10",
         "-f", "lavfi", "-i",
         "aevalsrc='sin(2*PI*440*t)*lt(t,1)+sin(2*PI*440*t)*gt(t,3)':d=4",
         "-shortest", str(src)],
        check=True, capture_output=True,
    )
    out = tmp_path / "tight.mp4"
    remove_silence.run(str(src), str(out), {"threshold_db": -30, "min_silence_ms": 500})
    # Should be shorter than the 4s original (the 2s silent gap is removed).
    assert probe_metadata(str(out))["duration_s"] < 3.5


def test_srt_timestamp_format():
    assert caption._format_timestamp(3661.5) == "01:01:01,500"
    assert caption._format_timestamp(0) == "00:00:00,000"


def test_srt_build_numbers_blocks():
    segs = [
        {"start": 0, "end": 1.5, "text": " Hello "},
        {"start": 1.5, "end": 3, "text": "World"},
    ]
    srt = caption._build_srt(segs)
    assert "1\n00:00:00,000 --> 00:00:01,500\nHello" in srt
    assert "2\n00:00:01,500 --> 00:00:03,000\nWorld" in srt


def test_caption_without_transcript_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.processing.ops.caption.transcribe", lambda p: None)
    src = tmp_path / "x.mp4"
    src.write_bytes(b"\x00")
    with pytest.raises(RuntimeError):
        caption.run(str(src), str(tmp_path / "o.mp4"), {})


@skip_no_ffmpeg
def test_caption_burns_and_writes_srt(tmp_path):
    src = tmp_path / "src.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=3:size=320x240:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-shortest", str(src)],
        check=True, capture_output=True,
    )
    out = tmp_path / "captioned.mp4"
    transcript = [
        {"start": 0, "end": 1.5, "text": "Hello world"},
        {"start": 1.5, "end": 3, "text": "second line"},
    ]
    caption.run(str(src), str(out), {"transcript": transcript})

    assert out.exists() and out.stat().st_size > 0
    assert (tmp_path / "captioned.srt").exists()
    assert probe_metadata(str(out))["duration_s"] > 2.0


@skip_no_ffmpeg
def test_background_music_mixes_under_audio(tmp_path):
    from backend.processing.ops import bgmusic
    vid = tmp_path / "v.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=3:size=160x120:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-shortest", str(vid)],
        check=True, capture_output=True,
    )
    music = tmp_path / "m.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=1", str(music)],
        check=True, capture_output=True,
    )
    out = tmp_path / "mixed.mp4"
    bgmusic.run(str(vid), str(out), {"music_path": str(music), "volume": 0.25})
    meta = probe_metadata(str(out))
    assert out.exists() and meta["has_audio"] is True
    assert meta["duration_s"] > 2.0


def test_background_music_without_track_raises(tmp_path):
    from backend.processing.ops import bgmusic
    with pytest.raises(RuntimeError):
        bgmusic.run("x.mp4", str(tmp_path / "o.mp4"), {})


@skip_no_ffmpeg
def test_insert_clip_prepends_broll(tmp_path):
    from backend.processing.ops import broll
    main = tmp_path / "main.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=3:size=320x240:rate=15",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-shortest", str(main)],
        check=True, capture_output=True,
    )
    clip = tmp_path / "broll.mp4"  # different res/fps, no audio
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=duration=2:size=640x360:rate=30",
         "-an", str(clip)],
        check=True, capture_output=True,
    )
    out = tmp_path / "joined.mp4"
    broll.run(str(main), str(out), {"clip_path": str(clip), "position": "start"})
    meta = probe_metadata(str(out))
    # ~3s main + ~2s broll, normalized to main's 320x240
    assert meta["width"] == 320 and meta["height"] == 240
    assert meta["duration_s"] > 4.0


def test_insert_clip_without_clip_raises(tmp_path):
    from backend.processing.ops import broll
    with pytest.raises(RuntimeError):
        broll.run("x.mp4", str(tmp_path / "o.mp4"), {})
