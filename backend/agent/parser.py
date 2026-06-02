"""parse_command: the planner node of the LangGraph agent.

Takes the user's command + video metadata + transcript and uses GPT-4o tool
calling to emit a structured, validated EditOp plan. The forced tool call means
the model returns ops, never prose. Invalid op names are dropped; if nothing
valid remains (or the model can't be reached), the node sets status="error"
with a user-friendly message.
"""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from backend.agent.prompts import system_prompt, user_message
from backend.agent.state import AgentState
from backend.config import settings
from backend.processing.registry import op_names

_TOOL_NAME = "create_edit_plan"


def _edit_plan_tool() -> dict:
    """OpenAI-format tool schema. The op enum is built from the live registry."""
    return {
        "name": _TOOL_NAME,
        "description": "Return the ordered list of edit operations that fulfil the request.",
        "parameters": {
            "type": "object",
            "properties": {
                "ops": {
                    "type": "array",
                    "description": "Ordered edit operations. Empty if nothing is supported.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "op": {"type": "string", "enum": sorted(op_names())},
                            "params": {
                                "type": "object",
                                "description": "Parameters for this op (see system instructions).",
                            },
                        },
                        "required": ["op", "params"],
                    },
                }
            },
            "required": ["ops"],
        },
    }


def _make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )


def parse_command(state: AgentState) -> dict:
    command = (state.get("command") or "").strip()
    if not command:
        return {"status": "error", "error": "No command was provided."}

    llm = _make_llm().bind_tools([_edit_plan_tool()], tool_choice=_TOOL_NAME)
    messages = [
        ("system", system_prompt()),
        ("human", user_message(command, state.get("metadata"), state.get("transcript"))),
    ]

    try:
        response = llm.invoke(messages)
    except Exception:
        return {
            "status": "error",
            "error": "Could not reach the language model. Check OPENAI_API_KEY.",
        }

    tool_calls = getattr(response, "tool_calls", None) or []
    if not tool_calls:
        return {"status": "error", "error": "Could not interpret that command. Try rephrasing it."}

    raw_ops = tool_calls[0].get("args", {}).get("ops", [])
    valid = op_names()
    plan = [
        {"op": item["op"], "params": item.get("params", {})}
        for item in raw_ops
        if isinstance(item, dict) and item.get("op") in valid
    ]

    if not plan:
        return {
            "status": "error",
            "error": "That command doesn't map to any supported edit yet.",
        }

    return {"plan": plan, "status": "executing"}
