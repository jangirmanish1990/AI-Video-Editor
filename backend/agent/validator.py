"""validate_output: the final node of the LangGraph agent.

If an upstream node already failed, leave the error as-is. Otherwise confirm the
produced file exists and is playable (ffprobe duration > 0 for video), and mark
the run done.
"""
from __future__ import annotations

import os

from backend.agent.state import AgentState
from backend.processing.probe import probe_metadata


def validate_output(state: AgentState) -> dict:
    if state.get("status") == "error":
        return {}  # error already set and messaged upstream

    output_path = state.get("output_path")
    if not output_path or not os.path.exists(output_path):
        return {"status": "error", "error": "The edit produced no output file."}

    # Audio-only outputs (extract_audio) won't have a video duration; accept them.
    if output_path.endswith(".mp3"):
        return {"status": "done", "output_duration": 0.0}

    meta = probe_metadata(output_path)
    if meta.get("duration_s", 0.0) <= 0.0:
        return {"status": "error", "error": "The output video appears to be empty or corrupt."}

    return {"status": "done", "output_duration": meta.get("duration_s", 0.0)}
