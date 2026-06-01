# Spec: Frontend (React + Vite + Tailwind)

Read before touching anything in `frontend/src/`.

## App layout
```
frontend/
├── index.html
├── vite.config.js             # React + @tailwindcss/vite plugin (Tailwind v4)
├── package.json
└── src/
    ├── main.jsx
    ├── index.css               # @import "tailwindcss" + @theme design tokens
    ├── App.jsx                 # layout shell + top-level state
    ├── api.js                  # fetch wrappers + WS helper (reads VITE_API_URL)
    ├── components/
    │   ├── Uploader.jsx        # drag/drop + file picker → POST /upload
    │   ├── VideoPlayer.jsx     # HTML5 <video>, controlled play/seek
    │   ├── WaveformTimeline.jsx# Wavesurfer.js, region select, silence markers
    │   ├── CommandBar.jsx      # NL input, submit → POST /edit, opens WS
    │   ├── JobStatus.jsx       # live progress from WS (planning→executing→done)
    │   ├── HistoryPanel.jsx    # past edits (localStorage), download links
    │   └── OpsReference.jsx    # collapsible supported-commands list (GET /ops)
    └── hooks/
        ├── useJobSocket.js     # subscribes to WS /ws/{job_id}, returns events
        └── useUpload.js
```

## State (lifted to App.jsx, passed down via props; no Redux for v1)
```
currentJob: { jobId, filename, metadata, status, plan, resultUrl, error } | null
history:    JobRecord[]   // persisted to localStorage under "ave_history"
selection:  { start, end } | null   // from WaveformTimeline region drag
```

## Data flow
1. Uploader → POST /upload → store currentJob with metadata, render player + waveform.
2. User types in CommandBar (optionally after drag-selecting a region on the waveform).
3. CommandBar → POST /edit {job_id, command, region?} → 202 → open WS via useJobSocket.
4. JobStatus renders the live event stream:
   - `plan` event → show the parsed ops as chips
   - `progress` events → "Executing op 2/3: remove_silence…" with a bar
   - `result` event → enable download, push to history, show before/after preview
   - `error` event → red banner with the friendly message
5. On `result`, append to history and persist to localStorage.

## useJobSocket(jobId)
- Opens `${VITE_API_URL.replace('http','ws')}/ws/${jobId}`.
- Returns `{events, status, plan, result, error}` updated as messages arrive.
- Cleans up the socket on unmount or when status is done/error.

## Styling
- Tailwind utility classes only. No inline styles, no CSS modules.
- Color theme: neutral dark UI (slate-900 surfaces) with one accent (orange-500) for
  primary actions and progress. Keep it clean and flat.
- Components are functional + hooks. One component per file. Named default export.

## api.js surface
```
uploadVideo(file) -> { jobId, filename, metadata }
startEdit(jobId, command, region?) -> { jobId, status }
getOps() -> [{op, description, params_schema}]
downloadUrl(jobId) -> string
openJobSocket(jobId) -> WebSocket
```

## Env
`VITE_API_URL` — backend base URL. Dev: http://localhost:8000. Prod: the Railway URL.

## Out of scope for v1
- Auth / user accounts (history is local only)
- Multi-file batch UI (Day 22 adds this)
