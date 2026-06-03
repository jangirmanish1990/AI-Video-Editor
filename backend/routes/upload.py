"""POST /upload — accept a video, validate it, persist it, probe, transcribe.

Hardened: rate-limited per IP, filename sanitized (no path traversal), and the
saved file is validated as a real video via ffprobe (extension alone isn't
trusted). Whisper transcription runs as a fire-and-forget background task.
"""
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile

from backend.config import settings
from backend.jobs import store
from backend.processing.probe import probe_metadata
from backend.security import client_key, safe_filename, upload_limiter
from backend.transcription import transcribe

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


def _transcribe_job(job_id: str) -> None:
    job = store.get_job(job_id)
    if job is None:
        return
    job.transcript = transcribe(job.video_path)


@router.post("/upload")
async def upload(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    upload_limiter.check(client_key(request))

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: mp4, mov, mkv, webm.",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    job = store.create_job(filename=safe_filename(file.filename))
    dest = upload_dir / f"{job.job_id}_{job.filename}"

    size = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File exceeds {settings.max_upload_mb} MB limit.",
                )
            out.write(chunk)

    metadata = probe_metadata(str(dest))
    # Trust ffprobe, not the extension: a real video has video-stream dimensions.
    if metadata["width"] == 0 and metadata["height"] == 0:
        dest.unlink(missing_ok=True)
        store.delete_job(job.job_id)
        raise HTTPException(
            status_code=400,
            detail="That file doesn't look like a valid video.",
        )

    job.video_path = str(dest)
    job.metadata = metadata

    background_tasks.add_task(_transcribe_job, job.job_id)

    return {"job_id": job.job_id, "filename": job.filename, "metadata": job.metadata}
