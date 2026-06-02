"""Registry of supported edit operations.

Each entry has metadata (for GET /ops and the UI reference panel) and, once
implemented, an `fn` callable following the op contract:
    fn(input_path: str, output_path: str, params: dict) -> dict

Ops are filled in across Days 6-9 via the add-ffmpeg-op skill. Entries whose
`fn` is still None are planned but not yet executable.
"""
from backend.processing.ops import cut, extract_audio, remove_silence, speed, trim

OPS = [
    {
        "op": "trim",
        "description": "Keep only the time range between start and end (seconds).",
        "params_schema": {"start": "float", "end": "float"},
        "fn": trim.run,
    },
    {
        "op": "cut",
        "description": "Remove the range between start and end, joining the remainder.",
        "params_schema": {"start": "float", "end": "float"},
        "fn": cut.run,
    },
    {
        "op": "remove_silence",
        "description": "Auto-remove silent gaps below a loudness threshold.",
        "params_schema": {"threshold_db": "int=-40", "min_silence_ms": "int=500"},
        "fn": remove_silence.run,
    },
    {
        "op": "speed",
        "description": "Change playback speed by a factor (0.5-4.0).",
        "params_schema": {"factor": "float"},
        "fn": speed.run,
    },
    {
        "op": "caption",
        "description": "Burn the Whisper transcript into the video as subtitles.",
        "params_schema": {},
        "fn": None,
    },
    {
        "op": "extract_audio",
        "description": "Rip the audio track to a separate file.",
        "params_schema": {"format": "str=mp3"},
        "fn": extract_audio.run,
    },
]

_BY_NAME = {entry["op"]: entry for entry in OPS}


def list_ops() -> list[dict]:
    """Public metadata for every op (the `fn` is stripped)."""
    return [{k: v for k, v in entry.items() if k != "fn"} for entry in OPS]


def get_op(name: str) -> dict | None:
    return _BY_NAME.get(name)


def op_names() -> set[str]:
    return set(_BY_NAME)
