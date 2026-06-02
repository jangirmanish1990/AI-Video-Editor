"""POST /edit and WS /ws/{job_id} — the live agent run.

/edit records the command and returns 202; the client then opens the WebSocket,
which runs the LangGraph agent and streams events (status, plan, progress,
result, error) per specs/api.md.

The agent is synchronous (FFmpeg + LangGraph), so it runs in a worker thread;
events cross back to the event loop via a thread-safe queue.
"""
import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.agent.runner import run_agent
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
    if req.region is not None:
        job.metadata = {**(job.metadata or {}), "region": req.region.model_dump()}
    job.status = "planning"
    return {"job_id": job.job_id, "status": job.status}


@router.websocket("/ws/{job_id}")
async def job_socket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    job = store.get_job(job_id)
    if job is None:
        await websocket.send_json({"type": "error", "message": "Job not found."})
        await websocket.close()
        return
    if not job.command:
        await websocket.send_json({"type": "error", "message": "No command set. Call /edit first."})
        await websocket.close()
        return

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def emit(event: dict) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, event)

    def worker() -> None:
        try:
            run_agent(job, emit)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

    future = loop.run_in_executor(None, worker)
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await future
        await websocket.close()
