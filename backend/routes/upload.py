"""POST /upload — accept a video, persist it, probe metadata, start transcription.

Saves the file, reads real metadata with ffprobe, and kicks off Whisper
transcription as a background task (fire-and-forget; the result is cached on
the job and surfaced via GET /jobs/{job_id}). The caption op (Day 9) consumes
the transcript.
"""
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from backend.config import settings
from backend.jobs import store
from backend.processing.probe import probe_metadata
from backend.transcription import transcribe

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


def _transcribe_job(job_id: str) -> None:
    job = store.get_job(job_id)
    if job is None:
        return
    job.transcript = transcribe(job.video_path)


@router.post("/upload")
async def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: mp4, mov, mkv, webm.",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    job = store.create_job(filename=file.filename or "video")
    dest = upload_dir / f"{job.job_id}_{file.filename}"

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

    job.video_path = str(dest)
    job.metadata = probe_metadata(str(dest))

    # Fire-and-forget transcription (runs in a threadpool after the response).
    background_tasks.add_task(_transcribe_job, job.job_id)

    return {"job_id": job.job_id, "filename": job.filename, "metadata": job.metadata}
