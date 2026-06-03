"""In-memory job store (v1).

Survives only for the life of the process. A production deployment would back
this with Redis or DynamoDB — noted in the README. The public-facing shape is
produced by JobRecord.to_public(), which strips server-only fields.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field


@dataclass
class JobRecord:
    job_id: str
    filename: str = ""
    video_path: str = ""          # server-only
    command: str = ""
    status: str = "created"       # created|planning|executing|done|error
    metadata: dict = field(default_factory=dict)
    plan: list | None = None
    results: list = field(default_factory=list)
    transcript: list | None = None  # server-only
    output_path: str | None = None  # server-only
    output_url: str | None = None
    error: str | None = None

    def to_public(self) -> dict:
        data = asdict(self)
        for server_only in ("video_path", "transcript", "output_path"):
            data.pop(server_only, None)
        return data


_jobs: dict[str, JobRecord] = {}


def new_job_id() -> str:
    return uuid.uuid4().hex[:12]


def create_job(filename: str = "", video_path: str = "") -> JobRecord:
    job_id = new_job_id()
    record = JobRecord(job_id=job_id, filename=filename, video_path=video_path)
    _jobs[job_id] = record
    return record


def get_job(job_id: str) -> JobRecord | None:
    return _jobs.get(job_id)


def delete_job(job_id: str) -> None:
    _jobs.pop(job_id, None)
