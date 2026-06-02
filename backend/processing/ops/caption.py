"""Edit op: caption — burn the Whisper transcript into the video as subtitles.

The transcript is normally passed in via params (the executor injects the job's
transcript). If absent, the op transcribes the input itself. It writes a .srt
beside the output, then hardcodes it with FFmpeg's subtitles filter.

params:
    transcript: list[{start, end, text}] (optional; fetched if missing)

Returns: {"output_path": output_path}
Raises: RuntimeError if no transcript can be obtained.
"""
import os

import ffmpeg

from backend.transcription import transcribe


def _format_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:  # rounding spillover
        ms = 0
        seconds += 1
    total = int(seconds)
    return f"{total // 3600:02d}:{(total // 60) % 60:02d}:{total % 60:02d},{ms:03d}"


def _build_srt(segments: list[dict]) -> str:
    blocks = []
    for i, seg in enumerate(segments, start=1):
        start = _format_timestamp(seg.get("start", 0))
        end = _format_timestamp(seg.get("end", 0))
        text = (seg.get("text") or "").strip()
        blocks.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(blocks)


def _subtitles_arg(srt_path: str) -> str:
    # Escape for the subtitles filter: forward slashes, escaped drive colon.
    escaped = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")
    return f"subtitles='{escaped}'"


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    transcript = params.get("transcript") or transcribe(input_path)
    if not transcript:
        raise RuntimeError(
            "No transcript available to caption. Ensure OPENAI_API_KEY is set "
            "and the video contains speech."
        )

    srt_path = os.path.splitext(output_path)[0] + ".srt"
    with open(srt_path, "w", encoding="utf-8") as handle:
        handle.write(_build_srt(transcript))

    stream = ffmpeg.input(input_path)
    stream = ffmpeg.output(stream, output_path, vf=_subtitles_arg(srt_path))
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    return {"output_path": output_path}
