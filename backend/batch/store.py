"""In-memory store for batch runs (mirrors backend/jobs/store.py)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

_batches: dict[str, "BatchRecord"] = {}


@dataclass
class BatchRecord:
    batch_id: str
    command: str
    job_ids: list[str]
    status: str = "processing"   # processing | done | error
    completed: int = 0
    results: list[dict] = field(default_factory=list)


def create_batch(command: str, job_ids: list[str]) -> BatchRecord:
    record = BatchRecord(
        batch_id=uuid.uuid4().hex[:12],
        command=command,
        job_ids=list(job_ids),
    )
    _batches[record.batch_id] = record
    return record


def get_batch(batch_id: str) -> BatchRecord | None:
    return _batches.get(batch_id)
