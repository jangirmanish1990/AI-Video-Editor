"""The state carried through the LangGraph agent (see specs/agent.md).

Nodes receive the full AgentState and return a partial dict of updates, which
LangGraph merges. `total=False` makes those partial returns valid typing.
"""
from __future__ import annotations

from typing import TypedDict


class EditOp(TypedDict):
    op: str
    params: dict


class OpResult(TypedDict):
    op: str
    status: str  # "ok" | "error"
    output_path: str | None
    stderr: str | None
    duration_s: float


class AgentState(TypedDict, total=False):
    job_id: str
    command: str
    video_path: str
    transcript: list[dict] | None
    music_path: str | None
    broll_path: str | None
    metadata: dict
    plan: list[EditOp] | None
    results: list[OpResult]
    output_path: str | None
    status: str  # planning | executing | done | error
    error: str | None
