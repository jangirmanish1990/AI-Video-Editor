"""Edit op: background_music — mix a music track under the video's audio.

The music is looped to cover the whole video and lowered in volume so it sits
under any existing dialogue. If the video has no audio track, the music becomes
the audio (trimmed to the video length).

params:
    music_path: str (injected by the executor from the job; required)
    volume:     float (default 0.25) — music level relative to original

Returns: {"output_path": output_path}
Raises: RuntimeError if no music track is attached.
"""
import ffmpeg

from backend.processing.probe import probe_metadata


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    music_path = params.get("music_path")
    if not music_path:
        raise RuntimeError("No background music attached. Upload a music track first.")
    volume = float(params.get("volume", 0.25))

    has_audio = probe_metadata(input_path).get("has_audio", False)

    video = ffmpeg.input(input_path)
    music = ffmpeg.input(music_path, stream_loop=-1)  # loop to cover the video
    music_a = music.audio.filter("volume", volume)

    if has_audio:
        audio = ffmpeg.filter([video.audio, music_a], "amix", inputs=2, duration="first")
    else:
        audio = music_a

    out = ffmpeg.output(video.video, audio, output_path, vcodec="copy", shortest=None)
    ffmpeg.run(out, overwrite_output=True, quiet=True)

    return {"output_path": output_path}
