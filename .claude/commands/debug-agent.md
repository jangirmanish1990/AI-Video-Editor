---
description: Inspect the most recent agent run — the command, the parsed plan JSON, per-op results and any FFmpeg stderr, plus the LangSmith trace if tracing is enabled.
allowed-tools: Read, Bash(cat:*), Bash(type:*)
---
Show me what happened in the most recent edit run.

1. Read `logs/last_run.json` (the agent writes it after every run). If it doesn't
   exist, tell me no edit has run yet this server session and stop.
2. Present, clearly and concisely:
   - The user command.
   - The parsed plan as formatted JSON — the ops + params GPT-4o produced.
   - Final status (done / error); if error, the error message.
   - For each entry in `results`: op name, status, and duration. ONLY for a
     failed op, show the LAST ~15 lines of its `stderr` (where the real FFmpeg
     error is). Never dump a full stderr log.
3. If `.env` has `LANGSMITH_TRACING=true`, remind me the full trace is viewable
   in LangSmith under the `LANGSMITH_PROJECT` project at https://smith.langchain.com.
4. If the run errored, give a one-line diagnosis and the most likely fix
   (e.g. "trim end exceeded video length — clamp to duration").

This is a debugging view, not a report — keep it tight.
