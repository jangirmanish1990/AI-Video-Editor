"""Tests for the parse_command planner node.

The LLM is fully mocked, so these are fast, free, and need no API key. They
lock the node's contract: valid plan shape, order preservation, invalid-op
filtering, and graceful errors.
"""
from backend.agent import parser


class _FakeResponse:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls


class _FakeLLM:
    """Stands in for a bind_tools-wrapped ChatOpenAI."""

    def __init__(self, tool_calls=None, raise_exc=False):
        self._tool_calls = tool_calls or []
        self._raise = raise_exc

    def bind_tools(self, tools, tool_choice=None):
        return self

    def invoke(self, messages):
        if self._raise:
            raise RuntimeError("network down")
        return _FakeResponse(self._tool_calls)


def _patch(monkeypatch, fake):
    monkeypatch.setattr(parser, "_make_llm", lambda: fake)


def _toolcall(ops):
    return [{"name": "create_edit_plan", "args": {"ops": ops}, "id": "1", "type": "tool_call"}]


def test_empty_command_errors():
    out = parser.parse_command({"command": "   "})
    assert out["status"] == "error"


def test_simple_trim_plan(monkeypatch):
    _patch(monkeypatch, _FakeLLM(_toolcall([{"op": "trim", "params": {"start": 0, "end": 30}}])))
    out = parser.parse_command(
        {"command": "keep the first 30 seconds", "metadata": {"duration_s": 60}}
    )
    assert out["status"] == "executing"
    assert out["plan"] == [{"op": "trim", "params": {"start": 0, "end": 30}}]


def test_multi_op_order_preserved(monkeypatch):
    ops = [
        {"op": "trim", "params": {"start": 0, "end": 30}},
        {"op": "remove_silence", "params": {"threshold_db": -40}},
    ]
    _patch(monkeypatch, _FakeLLM(_toolcall(ops)))
    out = parser.parse_command({"command": "trim then remove silences"})
    assert [p["op"] for p in out["plan"]] == ["trim", "remove_silence"]


def test_invalid_ops_filtered(monkeypatch):
    ops = [{"op": "trim", "params": {}}, {"op": "teleport", "params": {}}]
    _patch(monkeypatch, _FakeLLM(_toolcall(ops)))
    out = parser.parse_command({"command": "trim and teleport"})
    assert [p["op"] for p in out["plan"]] == ["trim"]


def test_all_invalid_errors(monkeypatch):
    _patch(monkeypatch, _FakeLLM(_toolcall([{"op": "teleport", "params": {}}])))
    out = parser.parse_command({"command": "teleport the video"})
    assert out["status"] == "error"


def test_no_tool_call_errors(monkeypatch):
    _patch(monkeypatch, _FakeLLM([]))
    out = parser.parse_command({"command": "do something odd"})
    assert out["status"] == "error"


def test_llm_exception_reports_key_hint(monkeypatch):
    _patch(monkeypatch, _FakeLLM(raise_exc=True))
    out = parser.parse_command({"command": "trim it"})
    assert out["status"] == "error"
    assert "OPENAI_API_KEY" in out["error"]


def test_user_message_includes_region():
    from backend.agent import prompts

    msg = prompts.user_message(
        "trim to selection",
        {"duration_s": 20, "has_audio": True, "region": {"start": 3.0, "end": 8.5}},
        None,
    )
    assert "3.00s to 8.50s" in msg
    assert "selection" in msg.lower()


def test_user_message_no_region_when_absent():
    from backend.agent import prompts

    msg = prompts.user_message("trim it", {"duration_s": 20, "has_audio": True}, None)
    assert "selection" not in msg.lower()
