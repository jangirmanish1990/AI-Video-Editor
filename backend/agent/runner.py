"""Runs the agent graph for a job and emits WebSocket events.

`emit(event)` delivers one JSON event to the client. Transport-agnostic and
synchronous, so it's safe to call from a worker thread. After the run it
persists the plan + results to the job and writes a debug record for the
/debug-agent command. Event types match specs/api.md.
"""
from __future__ import annotations

from typing import Callable

from backend.agent import debug_log
from backend.agent.errors import friendly_error
from backend.agent.graph import build_graph
from backend.agent.observability import run_config


def _failed_op(results: list[dict]) -> str | None:
    return next((r["op"] for r in results if r.get("status") == "error"), None)


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

    config = run_config(job, on_progress)
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
        final["status"] = "error"
        final["error"] = "The edit failed unexpectedly."

    # Persist run detail (visible via GET /jobs and /debug-agent).
    job.plan = final.get("plan")
    job.results = final.get("results", [])
    debug_log.write_run(job, final)

    if final.get("status") == "error":
        job.status = "error"
        message = friendly_error(
            final.get("error", "The edit failed."),
            _failed_op(final.get("results", [])),
        )
        job.error = message
        emit({"type": "error", "message": message})
        return

    job.status = "done"
    job.output_path = final.get("output_path")
    emit({
        "type": "result",
        "output_url": f"/download/{job.job_id}",
        "duration_s": final.get("output_duration", 0.0),
    })
    emit({"type": "status", "status": "done"})
