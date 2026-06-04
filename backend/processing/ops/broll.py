"""Edit op: insert_clip — prepend or append an attached B-roll clip.

Joining two arbitrary clips is the hard part: they may differ in resolution,
framerate, pixel format, and audio presence. So we normalize BOTH to the main
video's geometry/fps (with a silent track added where audio is missing), then
join with the concat demuxer (-c copy), which is reliable once inputs match.

params:
    clip_path: str (injected by the executor from the job; required)
    position:  "start" (default) | "end"

Returns: {"output_path": output_path}
Raises: RuntimeError if no B-roll clip is attached.
"""
import os

import ffmpeg

from backend.processing.probe import probe_metadata


def _normalize(src: str, dst: str, w: int, h: int, fps: float) -> None:
    has_audio = probe_metadata(src).get("has_audio", False)
    inp = ffmpeg.input(src)
    video = (
        inp.video
        .filter("scale", w, h, force_original_aspect_ratio="decrease")
        .filter("pad", w, h, "(ow-iw)/2", "(oh-ih)/2")
        .filter("setsar", 1)
        .filter("fps", fps)
    )
    common = dict(vcodec="libx264", acodec="aac", ar=44100, ac=2, pix_fmt="yuv420p")
    if has_audio:
        out = ffmpeg.output(video, inp.audio, dst, **common)
    else:
        silent = ffmpeg.input("anullsrc=channel_layout=stereo:sample_rate=44100", f="lavfi")
        out = ffmpeg.output(video, silent.audio, dst, shortest=None, **common)
    ffmpeg.run(out, overwrite_output=True, quiet=True)


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    clip_path = params.get("clip_path")
    if not clip_path:
        raise RuntimeError("No B-roll clip attached. Upload a clip first.")
    position = (params.get("position") or "start").lower()

    meta = probe_metadata(input_path)
    w = meta.get("width") or 1280
    h = meta.get("height") or 720
    fps = meta.get("fps") or 30
    if fps <= 0:
        fps = 30

    out_dir = os.path.dirname(output_path) or "."
    base = os.path.splitext(os.path.basename(output_path))[0]
    norm_main = os.path.join(out_dir, f"{base}_nmain.mp4")
    norm_broll = os.path.join(out_dir, f"{base}_nbroll.mp4")
    list_path = os.path.join(out_dir, f"{base}_concat.txt")

    try:
        _normalize(input_path, norm_main, w, h, fps)
        _normalize(clip_path, norm_broll, w, h, fps)

        order = [norm_broll, norm_main] if position == "start" else [norm_main, norm_broll]
        with open(list_path, "w", encoding="utf-8") as handle:
            for path in order:
                handle.write(f"file '{os.path.abspath(path).replace(os.sep, '/')}'\n")

        (
            ffmpeg.input(list_path, format="concat", safe=0)
            .output(output_path, c="copy")
            .run(overwrite_output=True, quiet=True)
        )
    finally:
        for path in (norm_main, norm_broll, list_path):
            if os.path.exists(path):
                os.remove(path)

    return {"output_path": output_path}
