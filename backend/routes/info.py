"""GET /ops and GET /silences/{job_id}.

/ops lists the supported edit operations (drives the UI reference panel).
/silences returns detected silent intervals so the waveform can highlight what
"remove silences" would cut — reuses the remove_silence detection logic.
"""
from fastapi import APIRouter, HTTPException

from backend.jobs import store
from backend.processing.ops.remove_silence import detect_silences
from backend.processing.registry import list_ops

router = APIRouter()


@router.get("/ops")
async def ops():
    return list_ops()


@router.get("/silences/{job_id}")
async def silences(job_id: str):
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    meta = job.metadata or {}
    if not job.video_path or not meta.get("has_audio", True):
        return {"silences": [], "duration": meta.get("duration_s", 0.0)}

    intervals = detect_silences(job.video_path)
    return {
        "silences": [{"start": start, "end": end} for start, end in intervals],
        "duration": meta.get("duration_s", 0.0),
    }
