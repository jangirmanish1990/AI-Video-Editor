# Spec: Deployment (Vercel + Railway)

Read before touching deploy config or the `/deploy` command.
No Docker. Frontend → Vercel. Backend → Railway.

## Backend → Railway
- Railway detects `requirements.txt` (Python) automatically — no Dockerfile.
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
  (Railway injects `$PORT`; never hardcode 8000 in prod.)
- FFmpeg: add `nixpacks.toml` at repo root so the binary is present at build time:
  ```toml
  [phases.setup]
  nixPkgs = ["...", "ffmpeg"]
  ```
- Env vars to set in the Railway dashboard:
  - `OPENAI_API_KEY`
  - `CLOUDINARY_URL`
  - `FRONTEND_ORIGIN` = the Vercel URL (for CORS)
  - `MAX_UPLOAD_MB` = 500
  - `LANGSMITH_*` (optional)
- Healthcheck path: `/health`.
- After deploy, Railway gives a public URL like `https://ai-video-editor.up.railway.app`.
  WebSockets work over this automatically (wss:// upgrade supported).

## Frontend → Vercel
- Root Directory: `frontend/`. Framework preset: Vite. Build: `npm run build`. Output: `dist`.
- Env var: `VITE_API_URL` = the Railway URL (https://…). The app derives the ws:// URL from it.
- SPA routing: add `frontend/vercel.json`:
  ```json
  { "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
  ```
- Every git push to main → production deploy; PRs get preview URLs.

## Storage → Cloudinary (prod)
- Dev uses local `uploads/`. Prod swaps to Cloudinary because Railway's filesystem is ephemeral.
- `config.py` picks storage backend based on whether `CLOUDINARY_URL` is set.
- Upload route stores to Cloudinary, returns the secure URL; download route 302s to it.

## Deploy order (matters)
1. Deploy backend to Railway first → get its public URL.
2. Set `VITE_API_URL` on Vercel to that URL → deploy frontend.
3. Set `FRONTEND_ORIGIN` on Railway to the Vercel URL → redeploy backend (CORS).
4. Smoke test: upload → edit → download on the live URLs.

## CORS gotcha
If the browser console shows a CORS error after deploy, it's almost always step 3 —
`FRONTEND_ORIGIN` on Railway doesn't match the actual Vercel domain. Match it exactly,
including https:// and no trailing slash.

## The /deploy command automates
test → build → commit → push → `railway up` → `vercel --prod` → print both URLs.
It STOPS if tests or build fail (see commands/deploy.md).

## Free-tier notes
- Railway: ~$5/month credit; the app sleeps when idle — first request after idle is slow.
- Vercel: generous free tier for hobby projects, global CDN included.
- Cloudinary: ~25GB free, enough for a demo.
