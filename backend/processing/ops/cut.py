"""Edit op: cut — remove the range [start, end] (seconds), joining the remainder.

Splits the input into the segment before `start` and the segment after `end`,
then concatenates them. Re-encodes (the concat filter requires it) so the join
is clean regardless of keyframe positions.

params:
    start: float (required)
    end:   float (required)

Returns: {"output_path": output_path}
"""
import ffmpeg


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    start = float(params["start"])
    end = float(params["end"])

    base = ffmpeg.input(input_path)

    before_v = base.video.filter("trim", start=0, end=start).filter("setpts", "PTS-STARTPTS")
    before_a = base.audio.filter("atrim", start=0, end=start).filter("asetpts", "PTS-STARTPTS")
    after_v = base.video.filter("trim", start=end).filter("setpts", "PTS-STARTPTS")
    after_a = base.audio.filter("atrim", start=end).filter("asetpts", "PTS-STARTPTS")

    joined = ffmpeg.concat(before_v, before_a, after_v, after_a, v=1, a=1).node
    stream = ffmpeg.output(joined[0], joined[1], output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    return {"output_path": output_path}
