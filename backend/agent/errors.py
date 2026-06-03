"""Turn an op failure into a user-friendly message (raw FFmpeg stderr never
reaches the frontend — see specs/api.md).
"""

OP_HINTS = {
    "trim": "Check that the start and end times fall within the video's length.",
    "cut": "Check that the start and end times fall within the video's length.",
    "speed": "Use a speed factor between 0.5 and 4.",
    "remove_silence": "The audio couldn't be processed for silence removal.",
    "caption": (
        "Captioning needs a transcript — make sure the video has clear speech "
        "and OPENAI_API_KEY is set."
    ),
    "extract_audio": "The video may not contain an audio track.",
    "background_music": "Attach a music track first using the + Music button.",
}


def friendly_error(base: str, failed_op: str | None) -> str:
    hint = OP_HINTS.get(failed_op or "")
    return f"{base} {hint}" if hint else base
