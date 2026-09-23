"""Append-only audit log, one JSONL file per book.

Only meaningful production events are recorded - the log is meant to be read by
a human asking 'what happened to this book?', not to be an event-sourcing
substrate. State is never reconstructed from it.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import clock
from bookfactory.core.jsonio import append_jsonl, read_jsonl

MEANINGFUL_EVENTS = {
    "book_created",
    "stage_advanced",
    "concept_locked",
    "voice_locked",
    "manuscript_locked",
    "visual_locked",
    "page_planned",
    "draft_submitted",
    "approved",
    "rejected",
    "revision_opened",
    "qa_run",
    "assembled",
    "review_generated",
    "preflight_run",
    "blocked",
    "unblocked",
    "production_policy_recorded",
    "intake_drafted",
    "picture_budget_changed",
    "production_policy_changed",
}


def record(log_path: str | Path, event: str, /, **fields) -> dict:
    # Positional-only: callers pass arbitrary field names, including 'path'.
    entry = {"at": clock.timestamp(), "event": event}
    entry.update({k: v for k, v in fields.items() if v is not None})
    append_jsonl(log_path, entry)
    return entry


def history(log_path: str | Path, /, *, limit: int | None = None,
            event: str | None = None) -> list[dict]:
    records = read_jsonl(log_path)
    if event:
        records = [r for r in records if r.get("event") == event]
    if limit:
        records = records[-limit:]
    return records
