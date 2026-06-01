# AI Video Editor — Project Memory

> Read this file at the start of every session. Keep it lean (< 500 tokens of "live" rules).
> Detailed contracts live in `.claude/specs/` — read the relevant spec before writing code for that layer.

## What we're building
A full-stack AI video editor. A user uploads a video, types a natural-language command
("remove all silences", "add captions", "trim to 60 seconds"), and a LangGraph agent
plans + executes the edits via FFmpeg, streaming progress to a React UI over WebSocket.

## Stack
- Frontend: React 18 + Vite + Tailwind (dev port 5173)
- Backend: FastAPI + WebSocket (dev port 8000), served by uvicorn
- Agent: LangGraph StateGraph — 3 nodes (parse_command → execute_plan → validate_output)
- LLM: OpenAI GPT-4o via the `openai` SDK / `langchain-openai`. **No Anthropic key in app code.**
- Transcription: OpenAI Whisper API (same OPENAI_API_KEY)
- Video: `ffmpeg-python`; FFmpeg binary must be on PATH
- Storage: local `uploads/` in dev → Cloudinary in prod
- Deploy: Vercel (frontend) + Railway (backend)

## Credentials — important distinction
- **Claude Code (this tool)** authenticates with a **Claude Pro subscription** (browser `/login`,
  choose "Claude.ai"). No per-token charges. This is separate from the app.
- **The app** uses `OPENAI_API_KEY` for GPT-4o + Whisper. Keep it in `.env` ONLY.
- Never set `ANTHROPIC_API_KEY` as a global env var — it would override the subscription and
  trigger pay-as-you-go API billing. Run `/status` to confirm subscription auth is active.

## Working within Pro limits
- Pro uses a shared 5-hour rolling token window across Claude Code AND Claude.ai chat.
- Do heavy coding in the Claude Code CLI; keep it lean to preserve the window.
- Delegate large-output work (FFmpeg runs, full test suites, repo search) to sub-agents
  so their output stays out of the main context.
- Check budget anytime with `/usage`. If a window is exhausted, wait for it to roll off.

## Conventions
- Before writing code for a layer, read its spec: `.claude/specs/{agent,api,frontend,deploy}.md`
- New LangGraph node → use the `/add-new-node` skill
- New FFmpeg edit operation → use the `/add-ffmpeg-op` skill
- New full feature (route + component + test) → use the `/scaffold` command
- Heavy/long-output work → delegate to a sub-agent (ffmpeg-runner, test-writer, ui-builder)
- Python: type hints everywhere, max line length 100, pytest for tests
- Frontend: functional components + hooks, Tailwind utility classes, no inline styles
- Secrets never committed. `.env` is gitignored; `.env.example` documents the keys.

## Environment (Windows, no admin, no Docker)
- OS: Windows + PowerShell. No Docker locally — Railway handles containerization in prod.
- Python venv: `python -m venv .venv` then `.venv\Scripts\Activate.ps1`
- FFmpeg: install once via `winget install Gyan.FFmpeg`, then verify `ffmpeg -version`
- Run servers in two terminals: backend `uvicorn backend.main:app --reload`,
  frontend `cd frontend && npm run dev`. Or run both at once: `.\scripts\dev.ps1`

## Env vars (see .env.example)
OPENAI_API_KEY        # required — GPT-4o + Whisper
CLOUDINARY_URL        # prod only — video storage
LANGSMITH_API_KEY     # optional — agent tracing
LANGSMITH_TRACING     # optional — "true" to enable

## Current status
- [x] Day 1 — repo skeleton + CLAUDE.md + Claude Code auth verified (Pro subscription)
- [x] Day 2 — wrote the 4 specs (agent, api, frontend, deploy)
- [x] Day 3 — backend skeleton + PreToolUse lint hook + .mcp.json
- [x] Day 4 — frontend skeleton (Vite+React+Tailwind v4) + ui-builder sub-agent + Uploader/VideoPlayer/CommandBar/JobStatus
- [x] Day 5 — stub WebSocket wired + verified (test_ws_contract) + /scaffold command. PHASE 1 COMPLETE.
- [x] Day 6 — Whisper transcription + real ffprobe metadata on upload; add-ffmpeg-op skill; extract_audio op (working, tested)
- [ ] Day 7 — LangGraph parse_command node (GPT-4o function calling → EditOp plan)

## Supported edit ops (target — built in Phase 2)
trim · cut · remove_silence · speed · caption · extract_audio
