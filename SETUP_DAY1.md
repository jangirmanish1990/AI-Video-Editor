# Day 1 — Setup & Project Skeleton

Goal: working repo, Claude Code installed and authenticated, CLAUDE.md in place.
Time: ~1.5 hours. Everything below is PowerShell on Windows.

---

## Step 1 — Place the project
Extract this skeleton to your D: drive:
```powershell
# You should end up with:  D:\ai-video-editor
cd D:\ai-video-editor
dir   # confirm CLAUDE.md, README.md, .claude\, backend\, frontend\ are present
```

## Step 2 — Install Node.js (if you don't have it)
Claude Code runs on Node.js.
```powershell
winget install OpenJS.NodeJS.LTS
# close & reopen PowerShell, then verify:
node --version    # should be v18+ (v20 LTS recommended)
```

## Step 3 — Install Claude Code
```powershell
npm install -g @anthropic-ai/claude-code
claude --version
```

## Step 4 — Authenticate (the important part)
Your OpenAI key does NOT authenticate Claude Code. You need a Claude subscription
(Pro or Max) or Anthropic API credits.

```powershell
# First, make sure no Anthropic API key is lurking in your environment —
# if one is set, Claude Code uses it and bills you pay-as-you-go instead of your subscription.
echo $env:ANTHROPIC_API_KEY        # should print nothing/blank

# If it prints a key and you'd rather use your subscription, clear it for this session:
# $env:ANTHROPIC_API_KEY = $null

# Now start Claude Code — first run opens a browser to log in:
cd D:\ai-video-editor
claude
```
At the login prompt choose **Claude.ai** (subscription) — a browser tab opens, sign in,
return to the terminal. Then inside Claude Code:
```
/status
```
Confirm it shows subscription/OAuth auth and NOT an `ANTHROPIC_API_KEY` env var.

## Step 5 — Initialize git
```powershell
cd D:\ai-video-editor
git init
git add .
git commit -m "Day 1: project skeleton + CLAUDE.md"
```
(Optional) create a GitHub repo and push — you'll need it for Vercel/Railway later anyway:
```powershell
gh repo create ai-video-editor --private --source=. --remote=origin --push
```

## Step 6 — Run /init and review CLAUDE.md
Inside Claude Code:
```
/init
```
`/init` scans the repo and proposes a CLAUDE.md. We already wrote a strong one, so when it
finishes, tell Claude:
```
Merge anything useful /init found into the existing CLAUDE.md, but keep my structure,
conventions, and the credentials section intact. Don't remove the Windows/no-Docker notes.
```
Read the result. CLAUDE.md is the file Claude reads every session — it's worth getting right.

## Step 7 — Set up the Python venv (so it's ready for Day 3)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If activation is blocked by execution policy:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Step 8 — Install FFmpeg (needed from Day 6)
```powershell
winget install Gyan.FFmpeg
# reopen PowerShell, then:
ffmpeg -version
```

## Step 9 — Create your .env
```powershell
copy .env.example .env
notepad .env      # paste your real OPENAI_API_KEY, save
```

---

## Day 1 done — checklist
- [ ] `claude --version` works
- [ ] `/status` shows subscription auth (no stray ANTHROPIC_API_KEY)
- [ ] git initialized, first commit made
- [ ] CLAUDE.md reviewed and accurate
- [ ] `.venv` created, requirements installed
- [ ] `ffmpeg -version` works
- [ ] `.env` created with your OpenAI key

## Next — Day 2
Write the four specs in `.claude/specs/`: `agent.md`, `api.md`, `frontend.md`, `deploy.md`.
These are the typed contracts Claude reads before writing code for each layer. Ping me and
we'll draft them together.
