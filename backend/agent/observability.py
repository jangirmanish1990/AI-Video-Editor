"""LangSmith observability helpers.

When LANGSMITH_TRACING=true (loaded from .env into os.environ by config.py),
LangChain automatically uploads a trace for each graph run. We enrich those
traces with a readable run name, tags, and metadata so a given edit is easy to
find in the LangSmith dashboard — pairing with the /debug-agent command.
"""
from __future__ import annotations

import os
from typing import Callable


def tracing_enabled() -> bool:
    return os.environ.get("LANGSMITH_TRACING", "").strip().lower() in {"1", "true", "yes"}


def project_name() -> str:
    return os.environ.get("LANGSMITH_PROJECT", "ai-video-editor")


def run_config(job, on_progress: Callable) -> dict:
    """RunnableConfig for graph.stream: carries the progress callback plus
    LangSmith trace metadata (no-op when tracing is disabled)."""
    command = job.command or ""
    return {
        "configurable": {"on_progress": on_progress},
        "run_name": f"edit: {command[:48]}" if command else "edit",
        "tags": ["ai-video-editor", f"job:{job.job_id}"],
        "metadata": {"job_id": job.job_id, "command": command},
    }
