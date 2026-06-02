"""Edit op: speed — change playback speed by a factor, audio kept in sync.

Video uses setpts (PTS / factor). Audio uses atempo, which only accepts 0.5-2.0
per filter, so factors outside that range are chained (e.g. 4.0 -> 2.0 * 2.0).

params:
    factor: float (0.5-4.0). >1 speeds up, <1 slows down.

Returns: {"output_path": output_path}
"""
import ffmpeg


def _atempo_chain(stream, factor: float):
    # Decompose factor into steps within atempo's [0.5, 2.0] range.
    remaining = factor
    while remaining > 2.0:
        stream = stream.filter("atempo", 2.0)
        remaining /= 2.0
    while remaining < 0.5:
        stream = stream.filter("atempo", 0.5)
        remaining /= 0.5
    return stream.filter("atempo", round(remaining, 4))


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    factor = float(params.get("factor", 1.0))
    if factor <= 0:
        factor = 1.0

    base = ffmpeg.input(input_path)
    video = base.video.filter("setpts", f"PTS/{factor}")
    audio = _atempo_chain(base.audio, factor)

    stream = ffmpeg.output(video, audio, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    return {"output_path": output_path}
