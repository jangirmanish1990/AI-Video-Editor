#!/usr/bin/env python3
"""PreToolUse hook: lint Python content before Claude Code writes it.

Reads the Claude Code hook payload from stdin (JSON). For `Write` operations
targeting a .py file, it lints the content about to be written using flake8.
If flake8 reports problems it prints them to stderr and exits 2, which BLOCKS
the write and feeds the errors back to Claude so it can fix them in one pass.

Design notes:
- Pure Python (no jq, no bash) so it runs on Windows out of the box.
- Only the `Write` tool carries full file content; `Edit` payloads are partial,
  so we skip them here (the Day 11 PostToolUse pytest hook is the net for edits).
- Fails open: if flake8 isn't installed or input is malformed, exit 0 (allow).
"""
import json
import os
import subprocess
import sys
import tempfile


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # malformed input → don't block

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""

    if not file_path.endswith(".py"):
        sys.exit(0)

    content = tool_input.get("content")
    if tool_name != "Write" or content is None:
        sys.exit(0)  # can't reliably lint partial edits pre-application

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--max-line-length=100", tmp_path],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        sys.exit(0)  # flake8 unavailable → don't block
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if result.returncode != 0:
        report = (result.stdout or "").replace(tmp_path or "", file_path)
        print(
            f"flake8 found issues in {file_path} — fix them before writing:\n{report}",
            file=sys.stderr,
        )
        sys.exit(2)  # block the write

    sys.exit(0)


if __name__ == "__main__":
    main()
