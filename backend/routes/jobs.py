"""GET /jobs/{job_id} and GET /download/{job_id}."""
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from backend.jobs import store

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.to_public()


@router.get("/download/{job_id}")
async def download(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Cloud storage (Cloudinary): redirect directly — no server bandwidth needed.
    if job.output_url:
        return RedirectResponse(job.output_url)

    # Dev / local fallback: stream the file from disk.
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=404, detail="No processed output yet for this job.")
    return FileResponse(job.output_path, media_type="video/mp4")
