"""Cloud storage via Cloudinary.

Uploads processed video/audio outputs so download links persist after server
restarts and work from the deployed Railway instance. The cloudinary SDK reads
CLOUDINARY_URL from os.environ (populated by load_dotenv in config.py).

Fails soft: if Cloudinary isn't configured or the upload fails for any reason,
returns None and the app falls back to serving the file from disk.
"""
from __future__ import annotations

import os

import cloudinary
import cloudinary.uploader


def _enabled() -> bool:
    return bool(os.environ.get("CLOUDINARY_URL"))


def upload_output(job) -> str | None:
    """Upload job.output_path to Cloudinary. Returns the secure_url or None."""
    if not _enabled():
        return None
    output_path = getattr(job, "output_path", None)
    if not output_path or not os.path.exists(output_path):
        return None
    try:
        result = cloudinary.uploader.upload(
            output_path,
            resource_type="video",
            folder="ai-video-editor",
            public_id=job.job_id,
            overwrite=True,
        )
        return result.get("secure_url")
    except Exception:
        return None  # non-fatal — caller falls back to local file
