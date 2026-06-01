"""POST /upload — accept a video, persist it, return a job with metadata.

Day 3 skeleton: validates type/size and saves the file. ffprobe metadata and
async Whisper transcription are stubbed with TODOs for Day 6.
"""
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.config import settings
from backend.jobs import store

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
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

    # TODO(Day 6): probe real metadata with ffprobe.
    job.metadata = {
        "duration_s": 0.0,
        "width": 0,
        "height": 0,
        "fps": 0.0,
        "has_audio": True,
    }
    # TODO(Day 6): fire async Whisper transcription, cache result by job_id.

    return {"job_id": job.job_id, "filename": job.filename, "metadata": job.metadata}
