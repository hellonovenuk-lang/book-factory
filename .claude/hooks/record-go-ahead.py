#!/usr/bin/env python3
"""Go-ahead slip: a Claude Code UserPromptSubmit hook.

The approval guard (`guard-authority.py`) cannot see the chat, so in auto mode
it used to block every command only Kieran may decide (lock, approve, revise,
assemble, preflight ...), even straight after Kieran typed "lock the look".

This hook sees the text Kieran actually typed. On every prompt it overwrites
`.claude/state/go-ahead.json` (under `$CLAUDE_PROJECT_DIR`, else the payload's
`cwd`) with:

    {"session_id": ..., "recorded_at": "<UTC ISO time>", "prompt": "<the text>"}

Every new prompt replaces the old slip, so a slip lasts one turn. The guard
reads it and lets an operator-authority command through only when the slip
clearly authorises exactly that command (see `go_ahead_allows` in the guard).

Claude never writes the slip: `.claude/state/**` is denied to Edit and Write in
`.claude/settings.json`, and the guard denies Bash commands that write, move,
copy over or delete anything under `.claude/state/`.

Contract (Claude Code UserPromptSubmit): JSON on stdin with at least `prompt`,
`session_id`, `cwd`. Exit 0 with no output lets the prompt through unchanged.
This hook never blocks a prompt, never prints anything and never crashes.
Standard library only.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SLIP = Path(".claude") / "state" / "go-ahead.json"


def slip_path(payload: dict) -> Path | None:
    base = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd")
    if not isinstance(base, str) or not base:
        return None
    return Path(base) / SLIP


def record(payload) -> None:
    if not isinstance(payload, dict):
        payload = {}
    path = slip_path(payload)
    if path is None:
        return
    session_id = payload.get("session_id")
    prompt = payload.get("prompt")
    if not isinstance(session_id, str) or not isinstance(prompt, str):
        # Unreadable prompt: remove the old slip, so it can't outlive its turn.
        try:
            path.unlink()
        except OSError:
            pass
        return
    slip = {
        "session_id": session_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompt": prompt,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".go-ahead-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(slip, fh, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main() -> int:
    try:
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            payload = {}
        record(payload)
    except Exception:  # never block or disturb the prompt
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
