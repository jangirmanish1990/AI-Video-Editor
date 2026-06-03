"""Lightweight security helpers: filename sanitization + per-IP rate limiting.

The rate limiter is in-memory (per process) — fine for a single-instance demo.
A multi-instance deployment would back this with Redis. Limits are generous
enough not to impede normal use, restrictive enough to blunt abuse.
"""
import os
import re
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_SAFE = re.compile(r"[^A-Za-z0-9._-]")


def safe_filename(filename: str | None) -> str:
    """Strip any directory components and unsafe characters, preventing path
    traversal (e.g. '../../etc/passwd' -> 'etc_passwd')."""
    base = os.path.basename(filename or "")
    base = base.replace("\\", "/").split("/")[-1]  # belt-and-suspenders on Windows paths
    base = _SAFE.sub("_", base).lstrip(".")
    return base[:80] or "video"


class RateLimiter:
    def __init__(self, max_requests: int, window_s: int):
        self.max = max_requests
        self.window = window_s
        self._hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.time()
        dq = self._hits[key]
        while dq and dq[0] < now - self.window:
            dq.popleft()
        if len(dq) >= self.max:
            raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
        dq.append(now)

    def reset(self) -> None:
        self._hits.clear()


def client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# Module-level limiters shared across requests.
upload_limiter = RateLimiter(max_requests=30, window_s=60)
edit_limiter = RateLimiter(max_requests=60, window_s=60)

MAX_COMMAND_CHARS = 1000
