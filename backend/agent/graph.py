"""The agent graph: parse_command -> execute_plan -> validate_output.

parse_command branches: on a successful plan it proceeds to execute; on a parse
error it skips straight to the end. execute always flows into validate, which
finalizes success or surfaces the upstream error.

The execute node pulls an optional on_progress callback from the run config so
the route can stream per-op WebSocket progress.
"""
from langgraph.graph import END, START, StateGraph

from backend.agent import parser, validator
from backend.agent.executor import execute_plan
from backend.agent.state import AgentState


def _parse_node(state: AgentState) -> dict:
    return parser.parse_command(state)


def _execute_node(state: AgentState, config) -> dict:
    on_progress = (config or {}).get("configurable", {}).get("on_progress")
    return execute_plan(state, on_progress=on_progress)


def _validate_node(state: AgentState) -> dict:
    return validator.validate_output(state)


def _after_parse(state: AgentState) -> str:
    return "execute" if state.get("status") == "executing" else "finish"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse", _parse_node)
    graph.add_node("execute", _execute_node)
    graph.add_node("validate", _validate_node)

    graph.add_edge(START, "parse")
    graph.add_conditional_edges("parse", _after_parse, {"execute": "execute", "finish": END})
    graph.add_edge("execute", "validate")
    graph.add_edge("validate", END)

    return graph.compile()
