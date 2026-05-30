# AI Video Editor

A full-stack AI-powered video editor. Upload a video, type a natural-language command
("remove all silences", "add captions", "trim to 60 seconds"), and a LangGraph agent
plans and executes the edits via FFmpeg — streamed live to a React timeline UI.

Built end-to-end with **Claude Code** (CLAUDE.md, specs, skills, commands, hooks, plugins,
sub-agents). LLM runtime is **OpenAI GPT-4o + Whisper**. Deploys to **Vercel + Railway** — no Docker.

## Status
Day 1 of 30 — repo skeleton and project memory in place. See `CLAUDE.md` for the live roadmap.

## Stack
| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite + Tailwind |
| Backend | FastAPI + WebSocket |
| Agent | LangGraph (parse → execute → validate) |
| LLM | OpenAI GPT-4o |
| Transcription | OpenAI Whisper API |
| Video | ffmpeg-python |
| Storage | local → Cloudinary (prod) |
| Deploy | Vercel (FE) + Railway (BE) |

## Local setup (Windows / PowerShell)
```powershell
# 1. Clone / open the project
cd D:\ai-video-editor

# 2. Python backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. FFmpeg (once)
winget install Gyan.FFmpeg
ffmpeg -version   # verify

# 4. Secrets
copy .env.example .env
# then edit .env and paste your OPENAI_API_KEY

# 5. (from Day 4) Frontend
cd frontend
npm install
npm run dev
```

## Running with Claude Code
```powershell
cd D:\ai-video-editor
claude          # logs in via your Claude subscription on first run
/status         # confirm auth method (should NOT show an ANTHROPIC_API_KEY env var)
```

## Project structure
```
ai-video-editor/
├── CLAUDE.md              # project memory — read first
├── .claude/
│   ├── specs/             # typed contracts (Day 2)
│   ├── skills/            # reusable playbooks
│   ├── commands/          # slash commands
│   ├── agents/            # sub-agents
│   ├── settings.json      # permissions + hooks
│   └── .mcp.json          # MCP servers
├── backend/               # FastAPI app
├── frontend/              # React + Vite app
├── requirements.txt
├── .env.example
└── .gitignore
```
# AI-Video-Editor
