"""Edit op: trim — keep only the time range [start, end] (seconds).

params:
    start: float (default 0.0)
    end:   float (required; clamped to the input duration by ffmpeg)

Returns: {"output_path": output_path}
"""
import ffmpeg


def run(input_path: str, output_path: str, params: dict | None = None) -> dict:
    params = params or {}
    start = float(params.get("start", 0.0))
    end = params.get("end")

    stream = ffmpeg.input(input_path, ss=start, **({"to": float(end)} if end is not None else {}))
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    return {"output_path": output_path}
