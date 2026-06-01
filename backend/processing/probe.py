"""Probe a media file for the metadata the frontend and agent need.

Returns a dict with the shape declared in specs/api.md:
    {duration_s, width, height, fps, has_audio}
Fails soft: if ffprobe can't read the file, returns zeroed metadata rather
than raising, so an upload never 500s on a probe hiccup.
"""
import ffmpeg

_EMPTY = {"duration_s": 0.0, "width": 0, "height": 0, "fps": 0.0, "has_audio": False}


def _parse_fps(rate: str | None) -> float:
    if not rate:
        return 0.0
    try:
        num, den = rate.split("/")
        den_f = float(den)
        return round(float(num) / den_f, 2) if den_f else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe_metadata(path: str) -> dict:
    try:
        info = ffmpeg.probe(path)
    except (ffmpeg.Error, FileNotFoundError):
        return dict(_EMPTY)

    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    duration = float(info.get("format", {}).get("duration") or 0.0)
    return {
        "duration_s": round(duration, 2),
        "width": int(video["width"]) if video and video.get("width") else 0,
        "height": int(video["height"]) if video and video.get("height") else 0,
        "fps": _parse_fps(video.get("r_frame_rate")) if video else 0.0,
        "has_audio": audio is not None,
    }
