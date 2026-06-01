"""Edit op: extract_audio — rip the audio track to a separate file.

Op signature (the contract every op follows; see specs/agent.md):
    run(input_path: str, output_path: str, params: dict) -> dict

params:
    format: "mp3" (default) | "wav" | "m4a"

Returns: {"output_path": <str>}
Raises: ffmpeg.Error if the underlying FFmpeg call fails (the executor /
ffmpeg-runner sub-agent is responsible for catching and reporting these).
"""
import ffmpeg

_ACODEC = {
    "mp3": "libmp3lame",
    "wav": "pcm_s16le",
    "m4a": "aac",
}


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    fmt = params.get("format", "mp3")
    acodec = _ACODEC.get(fmt, "libmp3lame")

    stream = ffmpeg.input(input_path)
    stream = ffmpeg.output(stream.audio, output_path, acodec=acodec)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    return {"output_path": output_path}
