---
name: add-ffmpeg-op
description: Add a new FFmpeg edit operation to the video editor. Use when the user wants to support a new kind of edit — trim, cut, remove silence, change speed, crop, rotate, color grade, add captions, overlay, concatenate, etc. Covers the op implementation, registry wiring, and tests.
---

# Adding an FFmpeg edit operation

Use this when the user asks to support a new edit operation. The operation name
they want is implied by the request (e.g. "support trimming" → `trim`).

## Contract every op follows
An op is a module at `backend/processing/ops/<op_name>.py` exposing:

```python
def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    """One-line description of the edit. params: <document each key + default>.
    Returns {"output_path": output_path}. Raises ffmpeg.Error on failure."""
```

- Use `ffmpeg-python` (`import ffmpeg`). Build the stream, then
  `ffmpeg.run(stream, overwrite_output=True, quiet=True)`.
- Do NOT catch ffmpeg.Error inside the op — let it propagate. The executor
  (execute_plan node / ffmpeg-runner sub-agent) catches and reports it.
- Pure function of (input, output, params). No global state, no I/O beyond the
  files passed in.

## Steps
1. Read `.claude/specs/agent.md` for the EditOp schema and this op's intended
   params (the six v1 ops and their params are listed there).
2. Create `backend/processing/ops/<op_name>.py` implementing `run(...)` per the
   contract above. Look at `extract_audio.py` as the reference implementation.
3. Register it in `backend/processing/registry.py`: import the module and set
   the matching entry's `"fn": <module>.run` (the metadata entry already exists
   for the six v1 ops; for a brand-new op, add a full entry with op,
   description, params_schema, fn).
4. Add a test to `backend/tests/test_ops.py`:
   - Generate a tiny fixture clip with the `_make_test_video` helper already in
     that file (guard with `@skip_no_ffmpeg`).
   - Assert the output file exists, is non-empty, and (where it matters) has the
     expected duration/dimensions via `probe_metadata`.
5. If the op needs a param the parser must produce, confirm `specs/agent.md`
   documents it; update the spec if you changed the param shape.
6. Update `CLAUDE.md`'s "Supported edit ops" / status line if this completes a
   new op.

## Verify before reporting done
- `python -m flake8 backend/`
- `python -m pytest backend/tests/ -q`

Report which op was added, its params, and the files touched.
