"""OpenAI Whisper transcription.

Extracts the audio track to a temporary mp3 first (smaller than the video,
keeps us under Whisper's 25 MB limit, and avoids container formats Whisper
doesn't accept like mkv), then sends it to the API.

Fails soft: returns None if no API key is configured or anything goes wrong,
so the app stays usable for local testing without burning API calls.
"""
import os
import tempfile

from openai import OpenAI

from backend.config import settings
from backend.processing.ops import extract_audio


def transcribe(video_path: str) -> list[dict] | None:
    if not settings.openai_api_key:
        return None

    tmp_audio = tempfile.mktemp(suffix=".mp3")
    try:
        extract_audio.run(video_path, tmp_audio, {"format": "mp3"})

        client = OpenAI(api_key=settings.openai_api_key)
        with open(tmp_audio, "rb") as audio_file:
            resp = client.audio.transcriptions.create(
                model=settings.openai_whisper_model,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = getattr(resp, "segments", None) or []
        return [
            {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
            for seg in segments
        ]
    except Exception:
        # Network error, bad audio, quota, etc. — leave transcript unset.
        return None
    finally:
        if os.path.exists(tmp_audio):
            os.unlink(tmp_audio)
