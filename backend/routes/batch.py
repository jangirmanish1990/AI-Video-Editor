"""POST /batch and GET /batch/{batch_id}.

/batch applies a single command to multiple already-uploaded jobs and runs them
sequentially in the background. Results accumulate on the BatchRecord and are
readable via GET /batch/{batch_id} (poll until status != "processing").

This is intentionally kept sequential (one job at a time) so each FFmpeg
process has full CPU/memory — a production version would tune parallelism.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from backend.agent.runner import run_agent
from backend.batch import store as batch_store
from backend.jobs import store as job_store
from backend.security import MAX_COMMAND_CHARS, client_key, edit_limiter

router = APIRouter()


class BatchRequest(BaseModel):
    job_ids: list[str] = Field(..., min_length=1, max_length=10)
    command: str = Field(..., min_length=1, max_length=MAX_COMMAND_CHARS)


def _process_batch(batch_id: str) -> None:
    batch = batch_store.get_batch(batch_id)
    if batch is None:
        return
    errors = 0
    for job_id in batch.job_ids:
        job = job_store.get_job(job_id)
        if job is None:
            batch.results.append({
                "job_id": job_id, "status": "error",
                "output_url": None, "error": "Job not found.",
            })
            errors += 1
            batch.completed += 1
            continue
        job.command = batch.command
        run_agent(job, emit=lambda _e: None)   # no WS in batch mode
        batch.results.append({
            "job_id": job_id,
            "status": job.status,
            "output_url": f"/download/{job_id}" if job.status == "done" else None,
            "error": job.error,
        })
        if job.status != "done":
            errors += 1
        batch.completed += 1

    batch.status = "error" if errors == len(batch.job_ids) else "done"


@router.post("/batch", status_code=202)
async def run_batch(
    request: Request,
    req: BatchRequest,
    background_tasks: BackgroundTasks,
):
    edit_limiter.check(client_key(request))
    missing = [jid for jid in req.job_ids if not job_store.get_job(jid)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Jobs not found: {', '.join(missing)}")
    batch = batch_store.create_batch(req.command, req.job_ids)
    background_tasks.add_task(_process_batch, batch.batch_id)
    return {"batch_id": batch.batch_id, "total": len(req.job_ids), "status": batch.status}


@router.get("/batch/{batch_id}")
async def get_batch(batch_id: str):
    batch = batch_store.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found.")
    return {
        "batch_id": batch.batch_id,
        "command": batch.command,
        "status": batch.status,
        "total": len(batch.job_ids),
        "completed": batch.completed,
        "results": batch.results,
    }
