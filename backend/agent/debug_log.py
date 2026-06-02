"""Persist each agent run to logs/ so the /debug-agent command can inspect it.

Writes logs/last_run.json (most recent) and logs/<job_id>.json. Best-effort:
any failure here is swallowed so debug logging can never break an edit.
"""
from __future__ import annotations

import json
from pathlib import Path

LOG_DIR = Path("logs")


def write_run(job, final_state: dict) -> None:
    try:
        LOG_DIR.mkdir(exist_ok=True)
        record = {
            "job_id": job.job_id,
            "command": job.command,
            "status": final_state.get("status"),
            "plan": final_state.get("plan"),
            "results": final_state.get("results", []),
            "error": final_state.get("error"),
            "output_path": final_state.get("output_path"),
        }
        payload = json.dumps(record, indent=2)
        (LOG_DIR / "last_run.json").write_text(payload, encoding="utf-8")
        (LOG_DIR / f"{job.job_id}.json").write_text(payload, encoding="utf-8")
    except Exception:
        pass
