"""Edit op: remove_silence — drop silent gaps, keeping the audible segments.

Two passes:
  1. Run ffmpeg's silencedetect filter to find silent intervals.
  2. Invert those into "keep" segments, then trim+concat the keeps.

If no silence is found (or the file has no audio), the input is copied through
unchanged so the op is always safe to run.

params:
    threshold_db:   int   (default -40)  loudness below this counts as silence
    min_silence_ms: int   (default 500)  shorter gaps are ignored

Returns: {"output_path": output_path}
"""
import re

import ffmpeg

from backend.processing.probe import probe_metadata

_SILENCE_START = re.compile(r"silence_start:\s*([0-9.]+)")
_SILENCE_END = re.compile(r"silence_end:\s*([0-9.]+)")


def _detect_silences(input_path: str, threshold_db: int, min_silence_s: float) -> list[tuple]:
    """Return list of (start, end) silent intervals via silencedetect."""
    try:
        _, err = (
            ffmpeg.input(input_path)
            .filter("silencedetect", noise=f"{threshold_db}dB", d=min_silence_s)
            .output("-", format="null")
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as exc:
        err = exc.stderr or b""

    log = err.decode("utf-8", errors="ignore")
    starts = [float(m) for m in _SILENCE_START.findall(log)]
    ends = [float(m) for m in _SILENCE_END.findall(log)]
    # Pair them up; a trailing unmatched start runs to end-of-file (handled later).
    return list(zip(starts, ends))


def detect_silences(
    input_path: str, threshold_db: int = -40, min_silence_s: float = 0.5
) -> list[tuple]:
    """Public wrapper: return (start, end) silent intervals for a media file."""
    return _detect_silences(input_path, threshold_db, min_silence_s)


def _keep_segments(silences: list[tuple], duration: float) -> list[tuple]:
    """Invert silent intervals into the segments to keep."""
    keeps = []
    cursor = 0.0
    for s_start, s_end in silences:
        if s_start > cursor:
            keeps.append((cursor, s_start))
        cursor = max(cursor, s_end)
    if cursor < duration:
        keeps.append((cursor, duration))
    return [(a, b) for a, b in keeps if b - a > 0.05]  # drop slivers


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    threshold_db = int(params.get("threshold_db", -40))
    min_silence_s = int(params.get("min_silence_ms", 500)) / 1000.0

    meta = probe_metadata(input_path)
    duration = meta.get("duration_s", 0.0)

    silences = []
    if meta.get("has_audio"):
        silences = _detect_silences(input_path, threshold_db, min_silence_s)
    keeps = _keep_segments(silences, duration) if silences else []

    # Nothing to remove (or no usable info) -> pass the input through unchanged.
    if not silences or not keeps:
        ffmpeg.input(input_path).output(output_path, c="copy").run(
            overwrite_output=True, quiet=True
        )
        return {"output_path": output_path}

    base = ffmpeg.input(input_path)
    streams = []
    for start, end in keeps:
        v = base.video.filter("trim", start=start, end=end).filter("setpts", "PTS-STARTPTS")
        a = base.audio.filter("atrim", start=start, end=end).filter("asetpts", "PTS-STARTPTS")
        streams.extend([v, a])

    joined = ffmpeg.concat(*streams, v=1, a=1, n=len(keeps)).node
    stream = ffmpeg.output(joined[0], joined[1], output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    return {"output_path": output_path}
