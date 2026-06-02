#!/usr/bin/env python3
"""PostToolUse hook: run the backend test suite after a backend Python file
is written or edited.

Reads the Claude Code hook payload from stdin. If the touched file is a .py
under backend/, runs pytest fail-fast. On failure it prints the tail to stderr
and exits 2, so Claude Code surfaces the failure and Claude fixes it before
moving on. Fails open (exit 0) if pytest is unavailable or input is malformed.

Pure Python — no jq/bash — so it runs on Windows as-is.
"""
import json
import subprocess
import sys


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = payload.get("tool_input", {}) or {}
    file_path = (tool_input.get("file_path") or "").replace("\\", "/")

    is_py = file_path.endswith(".py")
    in_backend = "/backend/" in file_path or file_path.startswith("backend/")
    if not (is_py and in_backend):
        sys.exit(0)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "backend/tests/", "-x", "-q", "--no-header"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        sys.exit(0)  # pytest not installed -> don't block

    if result.returncode != 0:
        tail = (result.stdout or "")[-1500:] + (result.stderr or "")[-400:]
        print(
            f"Backend tests failed after changing {file_path} — fix before continuing:\n{tail}",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
