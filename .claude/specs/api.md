# Spec: API (FastAPI + WebSocket)

The HTTP + WebSocket contract between frontend and backend.
Read this before touching `backend/main.py` or anything in `backend/routes/`.

## App layout
```
backend/
├── main.py            # FastAPI app, CORS, router includes, /health
├── config.py          # pydantic-settings, reads .env
├── routes/
│   ├── upload.py      # POST /upload
│   ├── edit.py        # POST /edit, WS /ws/{job_id}
│   ├── jobs.py        # GET /jobs/{job_id}, GET /download/{job_id}
│   └── info.py        # GET /ops  (supported operations, drives the UI reference panel)
├── agent/             # LangGraph (see agent.md)
├── processing/        # FFmpeg ops registry (see add-ffmpeg-op skill)
└── tests/
```

## CORS
Allow `FRONTEND_ORIGIN` (env, default http://localhost:5173). Allow credentials, all methods.

## Endpoints

### GET /health
→ `200 {"status": "ok"}`. Used by Railway healthcheck.

### POST /upload
- multipart form, field `file`.
- Validate: extension in {mp4, mov, mkv, webm}, size ≤ `MAX_UPLOAD_MB`.
- Save to `UPLOAD_DIR/{job_id}_{filename}`. Probe metadata with ffprobe.
- Kick off async Whisper transcription (fire-and-forget; result cached by job_id).
- → `200 {job_id, filename, metadata: {duration_s, width, height, fps, has_audio}}`
- → `400` on bad type/size with a clear message.

### POST /edit
- body: `{job_id: str, command: str, region?: {start: float, end: float}}`
- Starts the LangGraph run in a background task.
- → `202 {job_id, status: "planning"}` immediately; progress flows over the WebSocket.
- `region` (optional) is injected into state so commands like "trim to selection" work.

### WS /ws/{job_id}
Server → client event stream. Every message is JSON:
```
{type: "status",   status: "planning"|"executing"|"done"|"error"}
{type: "plan",     plan: [{op, params}]}                 # once, after parse
{type: "progress", op: str, index: int, total: int}      # per op
{type: "result",   output_url: str, duration_s: float}   # on success
{type: "error",    message: str, op?: str}               # on failure
```
- Client opens the socket right after POST /edit returns.
- Server closes the socket after `done` or `error`.

### GET /jobs/{job_id}
→ current job record: `{job_id, status, command, plan?, results?, output_url?, error?}`.
Used for reconnect / history hydration.

### GET /download/{job_id}
→ streams the processed file (dev) or 302-redirects to the Cloudinary URL (prod).

### GET /ops
→ `[{op, description, params_schema}]` — the registered ops. The frontend renders the
"supported commands" reference panel from this, so it's always in sync with the backend.

## Job store
v1: in-memory dict `{job_id: JobRecord}` in `backend/jobs/store.py`. Survives the process only.
(Good enough for a portfolio demo; note in README that prod would use Redis/DynamoDB.)

## Errors
Always JSON: `{"detail": "<human readable>"}`. Never leak raw stack traces or FFmpeg stderr
to the client untranslated — validate_output produces the friendly message.

## Conventions
- All route handlers are `async def`.
- File/IO and FFmpeg work runs in a threadpool or the ffmpeg-runner sub-agent, never blocking
  the event loop.
- Pydantic models for every request/response body, defined next to their route.
