# Spec: Agent (LangGraph)

The agent turns a natural-language command into executed video edits.
Read this before touching anything in `backend/agent/`.

## Graph shape
3-node `StateGraph`, linear with one conditional:

```
parse_command → execute_plan → validate_output → END
                     │
                     └─(on op error)→ validate_output  (reports failure, no retry in v1)
```

## State
```python
class AgentState(TypedDict):
    job_id: str
    command: str                 # raw user input
    video_path: str              # input file on disk (or Cloudinary URL in prod)
    transcript: list[dict] | None  # [{start, end, text}], None if not yet transcribed
    metadata: dict               # {duration_s, width, height, fps, has_audio}
    plan: list[EditOp] | None    # produced by parse_command
    results: list[OpResult]      # appended by execute_plan, one per op
    output_path: str | None      # final processed file
    status: str                  # "planning" | "executing" | "done" | "error"
    error: str | None
```

## EditOp schema (the contract between parse and execute)
```python
class EditOp(TypedDict):
    op: str                      # one of the registered op names
    params: dict                 # op-specific, validated against the op's pydantic model
```

Registered ops (v1) and their params:
- `trim`            → {start: float, end: float}            seconds
- `cut`             → {start: float, end: float}            removes the range, joins remainder
- `remove_silence`  → {threshold_db: int = -40, min_silence_ms: int = 500}
- `speed`           → {factor: float}                       0.5–4.0
- `caption`         → {} (uses transcript; transcribes first if transcript is None)
- `extract_audio`   → {format: str = "mp3"}

## Node contracts

### parse_command
- Input: command, transcript (may be None), metadata
- Calls GPT-4o with **function calling** (tool schema = the EditOp list above) so the model
  MUST return structured ops, never prose.
- Model from env `OPENAI_MODEL` (default gpt-4o). Temperature 0.
- Output: `plan` (list[EditOp]), `status="executing"`.
- If the command needs the transcript (e.g. caption) and it's None, set a flag so
  execute_plan transcribes first.
- On unparseable command: `status="error"`, `error` = friendly explanation.

### execute_plan
- Does NOT run FFmpeg itself. Delegates to the **ffmpeg-runner sub-agent** with the plan.
- Applies ops sequentially; each op's output is the next op's input.
- Appends an `OpResult` per op: {op, status, output_path?, stderr?, duration_s}.
- Streams a progress event per op over the job's WebSocket (see api.md).
- On first op failure: stop, set `status="error"`, record which op failed.

### validate_output
- Confirms `output_path` exists and is a playable file (ffprobe duration > 0).
- On success: `status="done"`.
- On error: optionally call GPT-4o to turn raw FFmpeg stderr into a human-readable
  one-line explanation for the UI.

## OpResult schema
```python
class OpResult(TypedDict):
    op: str
    status: str          # "ok" | "error"
    output_path: str | None
    stderr: str | None
    duration_s: float
```

## LLM rules
- Use `langchain-openai.ChatOpenAI` bound with `.bind_tools([...])` for parse_command.
- Never let the model emit free-form edit instructions — always structured EditOps.
- Keep the system prompt in `backend/agent/prompts.py`, not inline.

## Observability
- If `LANGSMITH_TRACING=true`, the graph is auto-traced. No code change needed beyond env vars.

## Out of scope for v1
- Multi-step retries / self-correction loop (Phase 4 may add a critic node)
- Parallel op execution (ops are sequential; batch-across-videos parallelism is Day 22)
