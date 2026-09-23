"""`produce`: the loop that runs a book's mechanical tasks and stops at everything else.

The rules it sits on are AGENTS.md 2, 3, 3a and 8: one task at a time, never
approve or lock on the operator's behalf, obey the task's `mode`, never skip
a gate. These tests prove each of those holds while the loop runs.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bookfactory.core import api, produce
from bookfactory.core.book import ASSET, Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import read_json, write_json

BOOK = "test-book"

#: Events only an operator decision (or an audited --autonomous one) may write.
DECISION_EVENTS = {
    "approved", "rejected", "revision_opened", "concept_locked", "voice_locked",
    "manuscript_locked", "visual_locked", "cover_approved", "cover_visual_approved",
    "production_policy_changed", "picture_budget_changed", "unblocked",
}


def _audit(workspace) -> list[dict]:
    return api.audit_history(BOOK, root=workspace)


def _new_events(workspace, before: int) -> list[dict]:
    return _audit(workspace)[before:]


def _assert_no_decisions(events: list[dict]) -> None:
    decisions = [e for e in events if e["event"] in DECISION_EVENTS]
    assert decisions == [], f"produce wrote decision events: {decisions}"
    assert not [e for e in events
                if e["event"] == "stage_advanced" and e.get("to") == "release_ready"]


def _snapshot(folder: Path) -> dict[str, str]:
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


@pytest.fixture
def forbid_authority(monkeypatch):
    """Make every authority command explode if `produce` ever reaches for it."""
    def refuse(name):
        def _refused(*args, **kwargs):
            raise AssertionError(f"produce called api.{name}")
        return _refused

    for name in ("approve", "approve_passing", "reject", "revise", "lock", "advance",
                 "set_policy", "set_pictures", "unblock", "block", "confirm_intake"):
        monkeypatch.setattr(api, name, refuse(name))


# ----------------------------------------------------------------------
# Runs the mechanical steps
# ----------------------------------------------------------------------


def test_renders_the_next_page_then_stops_at_its_approval_without_approving(
        planned_book, workspace, forbid_authority):
    before = len(_audit(workspace))
    result = produce.run(BOOK, root=workspace)

    assert [s["task_id"] for s in result["steps"]] == [f"{BOOK}-p001-render"]
    step = result["steps"][0]
    assert step["type"] == "page_render"
    assert step["action"] == f"bookfactory render {BOOK} --page p001 --submit"
    assert "draft v1" in step["result"]

    assert result["stopped_because"] == "wait_for_operator"
    assert result["next_task"]["type"] == "approval"
    assert result["next_task"]["page_id"] == "p001"
    assert "p001" in result["message"]

    page = Book.load(BOOK, workspace).manifest.get("p001")
    assert page.latest_draft().revision == "v1"
    assert not page.is_approved
    _assert_no_decisions(_new_events(workspace, before))


def test_even_an_autonomous_book_is_never_approved_by_produce(
        planned_book, workspace, monkeypatch):
    api.set_policy(BOOK, "autonomous", by="Operator", root=workspace)

    def refused(*args, **kwargs):
        raise AssertionError("produce must never approve")
    monkeypatch.setattr(api, "approve", refused)
    monkeypatch.setattr(api, "approve_passing", refused)

    before = len(_audit(workspace))
    result = produce.run(BOOK, root=workspace)

    #: The approval reads continue_automatically under this policy, but an
    #: approval is a decision, not a mechanical step.
    assert result["next_task"]["type"] == "approval"
    assert result["next_task"]["mode"] == "continue_automatically"
    assert result["stopped_because"] == "not_mechanical"
    assert "an approval" in result["message"]
    assert not Book.load(BOOK, workspace).manifest.get("p001").is_approved
    _assert_no_decisions(_new_events(workspace, before))


def test_runs_qa_then_assembly_then_preflight(produced_book, workspace, forbid_authority):
    before = len(_audit(workspace))
    result = produce.run(BOOK, root=workspace)

    assert [s["type"] for s in result["steps"]] == ["qa", "assembly", "preflight"]
    assert [s["action"] for s in result["steps"]] == [
        f"bookfactory qa {BOOK}", f"bookfactory assemble {BOOK}", f"bookfactory preflight {BOOK}"]
    assert Book.load(BOOK, workspace).paths.interior_pdf.is_file()

    #: A four-page fixture is too short for KDP, so preflight fails and stays next.
    assert result["stopped_because"] == "no_progress"
    assert result["next_task"]["task_id"] == f"{BOOK}-preflight"
    assert "same task is still next" in result["message"]

    events = _new_events(workspace, before)
    assert {"assembled", "preflight_run"} <= {e["event"] for e in events}
    _assert_no_decisions(events)


def test_the_step_limit_is_honoured(produced_book, workspace):
    result = produce.run(BOOK, root=workspace, max_steps=1)
    assert [s["type"] for s in result["steps"]] == ["qa"]
    assert result["stopped_because"] == "max_steps"
    assert result["next_task"]["type"] == "assembly"
    assert not Book.load(BOOK, workspace).paths.interior_pdf.is_file()


@pytest.mark.parametrize("bad", [0, -1, "3", True])
def test_a_nonsense_step_limit_is_refused(produced_book, workspace, bad):
    with pytest.raises(ValidationError):
        produce.run(BOOK, root=workspace, max_steps=bad)


# ----------------------------------------------------------------------
# Stops at everything else
# ----------------------------------------------------------------------


def test_stops_at_writing(new_book, workspace):
    result = produce.run(BOOK, root=workspace)
    assert result["steps"] == []
    assert result["stopped_because"] == "not_mechanical"
    assert result["next_task"]["type"] == "authoring"
    assert "writing" in result["message"]


def test_stops_at_a_picture(produced_book, workspace):
    api.revise(BOOK, "fig-scope", kind=ASSET, reason="Composition too tight", root=workspace)
    result = produce.run(BOOK, root=workspace)
    assert result["steps"] == []
    assert result["stopped_because"] == "not_mechanical"
    assert result["next_task"]["type"] == "illustration"
    assert "a picture" in result["message"]


def test_stops_at_a_blocked_book(produced_book, workspace):
    api.block(BOOK, "IP concern", root=workspace)
    result = produce.run(BOOK, root=workspace)
    assert result["steps"] == []
    assert result["stopped_because"] == "blocked"
    assert "blocked" in result["message"]


def test_stops_at_a_mechanical_task_that_waits_for_the_operator(produced_book, workspace):
    """A checkpointed book stops before assembly when QA only warned."""
    api.qa(BOOK, root=workspace)
    latest = Book.load(BOOK, workspace).paths.qa_latest
    report = read_json(latest)
    report["summary"]["status"] = "warn"
    write_json(latest, report)

    result = produce.run(BOOK, root=workspace)
    assert result["steps"] == []
    assert result["next_task"]["type"] == "assembly"
    assert result["stopped_because"] == "wait_for_operator"
    assert not Book.load(BOOK, workspace).paths.interior_pdf.is_file()


@pytest.mark.parametrize("task_id,kind", [(f"{BOOK}-cover-finalize", "assembly"),
                                          (f"{BOOK}-cover-preflight", "preflight")])
def test_cover_steps_typed_like_mechanical_ones_are_not_run(task_id, kind):
    """`cover finalize` carries an approval forward; it is not produce's to run."""
    task = {"task_id": task_id, "type": kind, "mode": "continue_automatically",
            "summary": "cover step"}
    code, message = produce._stop_for(BOOK, task)
    assert code == "not_mechanical"
    assert "cover" in message


def test_reports_complete_when_there_is_no_next_task(produced_book, workspace, monkeypatch):
    monkeypatch.setattr(api, "next_task", lambda *a, **k: None)
    result = produce.run(BOOK, root=workspace)
    assert result["stopped_because"] == "complete"
    assert result["next_task"] is None
    assert result["steps"] == []


# ----------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------


def test_a_book_factory_error_stops_the_loop_with_its_remedy(produced_book, workspace, monkeypatch):
    def failing(*args, **kwargs):
        raise ValidationError("QA could not start", remedy="Fix the thing.")
    monkeypatch.setattr(api, "qa", failing)

    result = produce.run(BOOK, root=workspace)
    assert result["stopped_because"] == "error"
    assert "QA could not start" in result["message"]
    assert "Fix the thing." in result["message"]
    assert result["error"]["remedy"] == "Fix the thing."
    assert result["next_task"]["type"] == "qa"


def test_other_exceptions_are_not_swallowed(produced_book, workspace, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("a real bug")
    monkeypatch.setattr(api, "qa", broken)
    with pytest.raises(RuntimeError):
        produce.run(BOOK, root=workspace)


# ----------------------------------------------------------------------
# Dry run
# ----------------------------------------------------------------------


def test_a_dry_run_changes_nothing(planned_book, workspace):
    folder = workspace / "books" / BOOK
    before = _snapshot(folder)

    result = produce.run(BOOK, root=workspace, dry_run=True)

    assert _snapshot(folder) == before
    assert result["dry_run"] is True
    assert result["steps"] == []
    assert result["stopped_because"] == "dry_run"
    assert result["next_task"]["type"] == "page_render"
    assert f"bookfactory render {BOOK} --page p001 --submit" in result["message"]


def test_a_dry_run_says_why_it_would_stop(new_book, workspace):
    folder = workspace / "books" / BOOK
    before = _snapshot(folder)
    result = produce.run(BOOK, root=workspace, dry_run=True)
    assert _snapshot(folder) == before
    assert result["stopped_because"] == "not_mechanical"


# ----------------------------------------------------------------------
# The API wrapper
# ----------------------------------------------------------------------


def test_api_produce_is_the_loop(planned_book, workspace):
    result = api.produce(BOOK, root=workspace, max_steps=5)
    assert set(result) >= {"book_id", "dry_run", "steps", "stopped_because", "message",
                           "next_task"}
    assert result["book_id"] == BOOK
    assert result["steps"][0]["type"] == "page_render"
    page = Book.load(BOOK, workspace).manifest.get("p001")
    assert page.latest_draft() is not None and not page.is_approved
