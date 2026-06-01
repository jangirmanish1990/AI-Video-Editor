"""Registry of supported edit operations.

For the Day 3 skeleton this is static metadata so GET /ops works and the frontend
reference panel can render. The actual FFmpeg implementations are added Days 6-9
via the /add-ffmpeg-op skill, which will register callables here keyed by op name.
"""

OPS: list[dict] = [
    {
        "op": "trim",
        "description": "Keep only the time range between start and end (seconds).",
        "params_schema": {"start": "float", "end": "float"},
    },
    {
        "op": "cut",
        "description": "Remove the range between start and end, joining the remainder.",
        "params_schema": {"start": "float", "end": "float"},
    },
    {
        "op": "remove_silence",
        "description": "Auto-remove silent gaps below a loudness threshold.",
        "params_schema": {"threshold_db": "int=-40", "min_silence_ms": "int=500"},
    },
    {
        "op": "speed",
        "description": "Change playback speed by a factor (0.5-4.0).",
        "params_schema": {"factor": "float"},
    },
    {
        "op": "caption",
        "description": "Burn the Whisper transcript into the video as subtitles.",
        "params_schema": {},
    },
    {
        "op": "extract_audio",
        "description": "Rip the audio track to a separate file.",
        "params_schema": {"format": "str=mp3"},
    },
]


def list_ops() -> list[dict]:
    return OPS


def op_names() -> set[str]:
    return {entry["op"] for entry in OPS}
