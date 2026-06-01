---
description: Scaffold a full feature — FastAPI route + React component + test — from a one-line description, wired into the app and verified.
argument-hint: <one-line feature description>
allowed-tools: Read, Write, Edit, Bash(python -m flake8:*), Bash(python -m pytest:*), Bash(npm run build:*)
---
Scaffold a complete vertical feature for this project from the description below.

Feature: $ARGUMENTS

Work in this order. Do not skip the spec reads — they are the contract.

## 1. Load the contracts
- Read `CLAUDE.md` for conventions.
- Read `.claude/specs/api.md` (route + WebSocket conventions, job store, error shape).
- Read `.claude/specs/frontend.md` (component tree, api.js surface, design tokens).
- Read `src/index.css` for the design tokens before writing any JSX.

## 2. Plan (state it briefly, then proceed)
Derive from the description:
- a short slug (snake_case for files, PascalCase for the component),
- the backend endpoint(s) it needs and their request/response shapes,
- what the React component renders and which api.js call it uses,
- what the test asserts (happy path + one failure path).
State this plan in 3-4 lines so it's on the record, then build it.

## 3. Backend route
- Create `backend/routes/<slug>.py`: an `APIRouter`, `async def` handlers,
  pydantic models for every request/response body, JSON errors via
  `HTTPException(status_code, detail=...)` — never raw stderr or stack traces.
- Register it in `backend/main.py` with `app.include_router(<slug>.router)`,
  keeping the existing import/include style.

## 4. Backend test
- Create `backend/tests/test_<slug>.py` using `TestClient`.
- Cover the happy path and at least one 4xx (bad input or missing resource).
- Follow the existing tests' style.

## 5. Frontend component
- Delegate to the **ui-builder** sub-agent to build
  `frontend/src/components/<PascalName>.jsx` from the plan, so heavy JSX stays
  out of the main context. The sub-agent already knows the design system.
- If a new backend call is needed, add a thin wrapper to `src/api.js` matching
  the existing function style (return parsed JSON, throw on non-ok).
- Mount the component in `src/App.jsx` at the appropriate place (respect the
  existing layout and the Day-N placeholder comments).

## 6. Verify (must pass before reporting done)
Run, in order, and fix anything that fails:
- `python -m flake8 backend/`
- `python -m pytest backend/tests/ -q`
- `cd frontend && npm run build`

## 7. Report
List the files created and modified, and one line on how the component wires
into App.jsx. If you had to deviate from a spec, say so and update the spec.
