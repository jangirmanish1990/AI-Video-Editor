"""Runs the agent graph for a job and emits WebSocket events.

`emit(event)` is a callback that delivers one JSON event to the client (the
route wires it to the socket). This function is transport-agnostic and runs
synchronously, so it's safe to call from a worker thread.

Event types match specs/api.md: status, plan, progress, result, error.
"""
from __future__ import annotations

from typing import Callable

from backend.agent.graph import build_graph


def run_agent(job, emit: Callable[[dict], None]) -> None:
    emit({"type": "status", "status": "planning"})

    state = {
        "job_id": job.job_id,
        "command": job.command or "",
        "video_path": job.video_path,
        "transcript": job.transcript,
        "metadata": job.metadata or {},
    }

    def on_progress(op: str, index: int, total: int) -> None:
        emit({"type": "progress", "op": op, "index": index, "total": total})

    config = {"configurable": {"on_progress": on_progress}}
    graph = build_graph()
    final = dict(state)

    try:
        for update in graph.stream(state, config=config, stream_mode="updates"):
            for node, delta in update.items():
                final.update(delta)
                if node == "parse" and delta.get("status") == "executing" and delta.get("plan"):
                    emit({"type": "plan", "plan": delta["plan"]})
                    emit({"type": "status", "status": "executing"})
    except Exception:
        job.status = "error"
        job.error = "The edit failed unexpectedly."
        emit({"type": "error", "message": job.error})
        return

    if final.get("status") == "error":
        job.status = "error"
        job.error = final.get("error", "The edit failed.")
        job.results = final.get("results", [])
        emit({"type": "error", "message": job.error})
        return

    job.status = "done"
    job.output_path = final.get("output_path")
    job.results = final.get("results", [])
    emit({
        "type": "result",
        "output_url": f"/download/{job.job_id}",
        "duration_s": final.get("output_duration", 0.0),
    })
    emit({"type": "status", "status": "done"})
