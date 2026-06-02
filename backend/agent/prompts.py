"""Prompts for the parse_command node.

The op list is generated from the registry so the prompt always reflects exactly
which operations are implemented — add an op, and the planner learns about it
automatically.
"""
from backend.processing.registry import list_ops

SYSTEM_PROMPT = """You are the planning component of an AI video editor.

Translate the user's natural-language request into an ordered list of edit \
operations, then return them by calling the create_edit_plan tool.

You may ONLY use these operations:
{ops}

Rules:
- Always call create_edit_plan. Never reply with prose.
- Express all time values in seconds as numbers (e.g. 30, 12.5). The video's \
duration is provided; never produce a time beyond it.
- Operations run in order; each runs on the output of the previous one.
- If the request needs an operation not listed above, return an empty ops array.
- Prefer the simplest plan that satisfies the request."""


def ops_documentation() -> str:
    lines = []
    for entry in list_ops():
        schema = entry["params_schema"]
        params = ", ".join(f"{k} ({v})" for k, v in schema.items()) if schema else "no params"
        lines.append(f"- {entry['op']}: {entry['description']} | params: {params}")
    return "\n".join(lines)


def system_prompt() -> str:
    return SYSTEM_PROMPT.format(ops=ops_documentation())


def user_message(command: str, metadata: dict | None, transcript: list[dict] | None) -> str:
    lines = [f'User request: "{command.strip()}"']
    meta = metadata or {}
    if meta.get("duration_s"):
        lines.append(f"Video duration: {meta['duration_s']} seconds.")
    lines.append(f"Audio present: {bool(meta.get('has_audio'))}.")
    region = meta.get("region")
    if region and region.get("start") is not None and region.get("end") is not None:
        lines.append(
            f'Selected region: {float(region["start"]):.2f}s to {float(region["end"]):.2f}s. '
            f'"the selection" or "selected part" refers to this range.'
        )
    if transcript:
        text = " ".join(seg.get("text", "") for seg in transcript).strip()
        if text:
            lines.append(f"Transcript (may be truncated): {text[:1500]}")
    return "\n".join(lines)
