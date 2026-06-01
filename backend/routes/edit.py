"""POST /edit and WS /ws/{job_id}.

Day 3 skeleton: /edit validates the job and flips status to 'planning'. The WS
endpoint streams a stubbed event sequence so the frontend can be built against
the real message schema (see specs/api.md) before the agent exists. The real
LangGraph run + live events are wired Days 7-10.
"""
import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.jobs import store

router = APIRouter()


class Region(BaseModel):
    start: float
    end: float


class EditRequest(BaseModel):
    job_id: str
    command: str
    region: Region | None = None


@router.post("/edit", status_code=202)
async def edit(req: EditRequest):
    job = store.get_job(req.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    job.command = req.command
    job.status = "planning"
    # TODO(Day 7-10): launch the LangGraph agent in a background task and have it
    # emit events to the job's WebSocket. For now the WS streams a stub sequence.
    return {"job_id": job.job_id, "status": job.status}


@router.websocket("/ws/{job_id}")
async def job_socket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    job = store.get_job(job_id)
    if job is None:
        await websocket.send_json({"type": "error", "message": "Job not found."})
        await websocket.close()
        return

    try:
        # --- STUB sequence (replaced Day 10 by real agent events) ---
        await websocket.send_json({"type": "status", "status": "planning"})
        await asyncio.sleep(0.3)
        await websocket.send_json(
            {"type": "plan", "plan": [{"op": "trim", "params": {"start": 0, "end": 30}}]}
        )
        await websocket.send_json({"type": "status", "status": "executing"})
        await websocket.send_json({"type": "progress", "op": "trim", "index": 1, "total": 1})
        await asyncio.sleep(0.3)
        await websocket.send_json(
            {"type": "result", "output_url": f"/download/{job_id}", "duration_s": 30.0}
        )
        await websocket.send_json({"type": "status", "status": "done"})
    except WebSocketDisconnect:
        return
    finally:
        await websocket.close()
