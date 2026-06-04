"""execute_plan: the executor node of the LangGraph agent.

Runs the planned ops in order, chaining each op's output into the next op's
input. Per specs/agent.md the heavy FFmpeg work is delegated to the
ffmpeg-runner sub-agent in the Claude Code workflow; at runtime that maps to
calling each op's registered `fn`. Appends an OpResult per op and stops on the
first failure (no retry in v1).

A progress callback (optional) is invoked once per op so the route can stream
WebSocket progress events; in tests it's omitted.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import ffmpeg

from backend.agent.state import AgentState
from backend.config import settings
from backend.processing.registry import get_op


def _output_path(job_id: str, index: int, suffix: str = ".mp4") -> str:
    out_dir = Path(settings.upload_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir / f"{job_id}_step{index}{suffix}")


def execute_plan(state: AgentState, on_progress: Callable | None = None) -> dict:
    plan = state.get("plan") or []
    job_id = state.get("job_id", "job")
    current = state.get("video_path")
    results: list[dict] = []

    if not current:
        return {"status": "error", "error": "No input video to edit.", "results": results}

    total = len(plan)
    for index, step in enumerate(plan, start=1):
        op_name = step["op"]
        params = step.get("params", {})
        entry = get_op(op_name)

        if on_progress:
            on_progress(op=op_name, index=index, total=total)

        if entry is None or entry["fn"] is None:
            results.append({
                "op": op_name, "status": "error", "output_path": None,
                "stderr": f"Operation '{op_name}' is not implemented yet.", "duration_s": 0.0,
            })
            return {"results": results, "status": "error",
                    "error": f"Operation '{op_name}' is not available yet."}

        suffix = ".mp3" if op_name == "extract_audio" else ".mp4"
        out_path = _output_path(job_id, index, suffix)

        # caption needs the transcript, which lives on the state, not in params.
        if op_name == "caption" and "transcript" not in params:
            params = {**params, "transcript": state.get("transcript")}
        # background_music needs the attached music track.
        if op_name == "background_music" and "music_path" not in params:
            params = {**params, "music_path": state.get("music_path")}
        # insert_clip needs the attached b-roll clip.
        if op_name == "insert_clip" and "clip_path" not in params:
            params = {**params, "clip_path": state.get("broll_path")}

        started = time.monotonic()
        try:
            entry["fn"](current, out_path, params)
        except Exception as exc:
            if isinstance(exc, ffmpeg.Error):
                detail = (exc.stderr or b"").decode("utf-8", errors="ignore")[-800:]
            else:
                detail = str(exc)[-800:]
            results.append({
                "op": op_name, "status": "error", "output_path": None,
                "stderr": detail, "duration_s": round(time.monotonic() - started, 2),
            })
            return {"results": results, "status": "error",
                    "error": f"The '{op_name}' step failed."}

        results.append({
            "op": op_name, "status": "ok", "output_path": out_path,
            "stderr": None, "duration_s": round(time.monotonic() - started, 2),
        })
        current = out_path

    return {"results": results, "output_path": current, "status": "validating"}
