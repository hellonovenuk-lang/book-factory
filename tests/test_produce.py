"""`produce`: the loop that runs a book's mechanical tasks and stops at everything else.

The rules it sits on are AGENTS.md 2, 3, 3a and 8: one task at a time, never
approve or lock on the operator's behalf, obey the task's `mode`, never skip
a gate. These tests prove each of those holds while the loop runs.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bookfactory.core import api, cover, gates, produce, production
from bookfactory.core.book import ASSET, PAGE, Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import read_json, write_json
from tests.conftest import make_image

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
    """Make every authority command explode if `produce` ever reaches for it.

    The one exception is `api.approve`, and only for a page, only with
    `autonomous=True`, only for an explicit revision, never with `force`.
    Returns the list of approve calls it let through.
    """
    def refuse(name):
        def _refused(*args, **kwargs):
            raise AssertionError(f"produce called api.{name}")
        return _refused

    real_approve = api.approve
    calls: list[dict] = []

    def checked_approve(book_id, identifier, **kwargs):
        assert kwargs.get("kind") == PAGE, f"produce approved a {kwargs.get('kind')!r}"
        assert kwargs.get("autonomous") is True, "produce approved without autonomous=True"
        assert kwargs.get("revision"), "produce approved without naming the draft"
        assert "force" not in kwargs, "produce passed force to approve"
        calls.append({"id": identifier, **kwargs})
        return real_approve(book_id, identifier, **kwargs)

    monkeypatch.setattr(api, "approve", checked_approve)
    for name in ("approve_passing", "reject", "revise", "lock", "advance",
                 "set_policy", "set_pictures", "unblock", "block", "confirm_intake"):
        monkeypatch.setattr(api, name, refuse(name))
    #: The cover's own decisions live in core/cover.py.
    for name in ("approve", "finalize", "preflight"):
        monkeypatch.setattr(cover, name, refuse(f"cover.{name}"))
    return calls


def _record_policy(workspace, mode: str) -> None:
    """Record the operator's policy choice, as tests/test_autonomous.py does.

    Written directly because `forbid_authority` disables `api.set_policy`
    (produce must never call it), and so the audit log holds only what
    produce itself did.
    """
    book = Book.load(BOOK, workspace)
    book.state.production_policy = production.policy_from_choice(mode)
    book.save()


def _approvals(events: list[dict]) -> list[dict]:
    return [e for e in events if e["event"] == "approved"]


def _assert_only_autonomous_page_approvals(events: list[dict], policy: str) -> None:
    """Every decision `produce` wrote is a page approval under the recorded policy."""
    decisions = [e for e in events if e["event"] in DECISION_EVENTS]
    assert decisions == _approvals(events), f"produce wrote other decisions: {decisions}"
    for event in decisions:
        assert event["authorization"] == f"autonomous_production_policy:{policy}", event
    assert not [e for e in events
                if e["event"] == "stage_advanced" and e.get("to") == "release_ready"]


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


@pytest.mark.parametrize("policy", ["visual_checkpoint", "autonomous"])
def test_a_policy_that_authorizes_it_runs_render_then_approve_through_every_page(
        planned_book, workspace, forbid_authority, policy):
    _record_policy(workspace, policy)
    before = len(_audit(workspace))

    result = produce.run(BOOK, root=workspace)

    pages = [f"p{n:03d}" for n in range(1, 5)]
    expected_ids = []
    for page_id in pages:
        expected_ids += [f"{BOOK}-{page_id}-render", f"{BOOK}-{page_id}-approve"]
    expected_ids += [f"{BOOK}-qa", f"{BOOK}-assemble", f"{BOOK}-preflight"]
    assert [s["task_id"] for s in result["steps"]] == expected_ids
    assert [s["type"] for s in result["steps"]] == (
        ["page_render", "approval"] * 4 + ["qa", "assembly", "preflight"])

    approve_steps = [s for s in result["steps"] if s["type"] == "approval"]
    for page_id, step in zip(pages, approve_steps):
        assert step["action"] == (f"bookfactory approve {BOOK} {page_id} --kind page "
                                  "--draft v1 --by produce --autonomous")
        assert step["result"] == f"approved {page_id} draft v1 under the recorded {policy} policy"

    #: A four-page fixture is too short for KDP, so preflight fails and stays next.
    assert result["stopped_because"] == "no_progress"

    book = Book.load(BOOK, workspace)
    for page_id in pages:
        page = book.manifest.get(page_id)
        assert page.is_approved
        assert page.approved.revision == "v1"
        assert page.approved.authorization == f"autonomous_production_policy:{policy}"
    assert book.paths.interior_pdf.is_file()

    #: Only api.approve, only for these pages, and each named its draft.
    assert [(c["id"], c["revision"], c["by"]) for c in forbid_authority] == [
        (p, "v1", "produce") for p in pages]

    events = _new_events(workspace, before)
    approvals = _approvals(events)
    assert [(e["kind"], e["id"], e["revision"], e["by"]) for e in approvals] == [
        ("page", p, "v1", "produce") for p in pages]
    _assert_only_autonomous_page_approvals(events, policy)


def test_a_checkpointed_book_stops_at_the_first_page_approval(
        planned_book, workspace, forbid_authority):
    assert Book.load(BOOK, workspace).state.production_policy.mode == "checkpointed"
    before = len(_audit(workspace))
    result = produce.run(BOOK, root=workspace)

    assert [s["type"] for s in result["steps"]] == ["page_render"]
    assert result["stopped_because"] == "wait_for_operator"
    assert result["next_task"]["task_id"] == f"{BOOK}-p001-approve"
    assert forbid_authority == []
    assert not Book.load(BOOK, workspace).manifest.get("p001").is_approved
    _assert_no_decisions(_new_events(workspace, before))


def test_a_picture_approval_is_never_made_even_under_autonomous(
        produced_book, workspace, monkeypatch):
    _record_policy(workspace, "autonomous")
    api.revise(BOOK, "fig-scope", kind=ASSET, reason="Composition too tight", root=workspace)
    art = make_image(workspace / "staging" / "fig-scope-v2.png", (1800, 1350), seed=21)
    api.submit_asset(BOOK, "fig-scope", art, kind=ASSET, root=workspace)

    def refused(*args, **kwargs):
        raise AssertionError("produce must never approve a picture")
    monkeypatch.setattr(api, "approve", refused)
    monkeypatch.setattr(api, "approve_passing", refused)

    before = len(_audit(workspace))
    result = produce.run(BOOK, root=workspace)

    assert result["steps"] == []
    assert result["next_task"]["type"] == "approval"
    assert result["next_task"]["asset_id"] == "fig-scope"
    assert result["next_task"]["mode"] == "continue_automatically"
    assert result["stopped_because"] == "not_mechanical"
    assert "an approval" in result["message"]
    assert "picture" in result["message"]
    fig = Book.load(BOOK, workspace).registry.find("fig-scope")
    assert fig.revision_open and fig.approved.revision == "v1"
    _assert_no_decisions(_new_events(workspace, before))


def test_the_cover_approval_is_never_made_even_under_autonomous(
        produced_book, workspace, monkeypatch, forbid_authority):
    _record_policy(workspace, "autonomous")
    assert gates.autonomous_approval_authorized(Book.load(BOOK, workspace)).ok

    cover_task = {"task_id": f"{BOOK}-cover-approval", "book_id": BOOK, "type": "approval",
                  "summary": "Review the full-wrap cover draft", "page_id": None,
                  "asset_id": None, "gate": "cover_visual_checkpoint",
                  "mode": "continue_automatically"}
    monkeypatch.setattr(api, "next_task", lambda *a, **k: dict(cover_task))

    result = produce.run(BOOK, root=workspace)
    assert result["steps"] == []
    assert result["stopped_because"] == "not_mechanical"
    assert "cover" in result["message"]
    assert forbid_authority == []


@pytest.mark.parametrize("task", [
    #: A page id on something that is not the page's own approval task.
    {"task_id": f"{BOOK}-p001-something", "type": "approval", "page_id": "p001",
     "asset_id": None, "gate": None},
    #: A page's picture, named by page and asset.
    {"task_id": f"{BOOK}-fig-scope-approve", "type": "approval", "page_id": "p002",
     "asset_id": "fig-scope", "gate": None},
    #: A gate's approval.
    {"task_id": f"{BOOK}-p001-approve", "type": "approval", "page_id": "p001",
     "asset_id": None, "gate": "visual_lock"},
])
def test_only_a_pages_own_approval_task_qualifies(planned_book, workspace, task):
    _record_policy(workspace, "autonomous")
    task = {**task, "summary": "an approval", "mode": "continue_automatically"}
    code, message = produce._stop_for(BOOK, task, workspace)
    assert code == "not_mechanical"
    assert "an approval" in message


def test_a_page_approval_stops_when_the_authorization_gate_fails(
        planned_book, workspace, monkeypatch, forbid_authority):
    _record_policy(workspace, "visual_checkpoint")
    api.render(BOOK, page_id="p001", submit=True, root=workspace)
    assert api.next_task(BOOK, root=workspace)["mode"] == "continue_automatically"

    monkeypatch.setattr(gates, "autonomous_approval_authorized",
                        lambda book: gates.GateResult("autonomous_approval_authorized", False,
                                                      ["withdrawn for this test"]))
    before = len(_audit(workspace))
    result = produce.run(BOOK, root=workspace)

    assert result["steps"] == []
    assert result["stopped_because"] == "not_mechanical"
    assert result["next_task"]["task_id"] == f"{BOOK}-p001-approve"
    assert "withdrawn for this test" in result["message"]
    assert forbid_authority == []
    assert not Book.load(BOOK, workspace).manifest.get("p001").is_approved
    _assert_no_decisions(_new_events(workspace, before))


def test_a_page_approval_with_no_reviewable_draft_stops(
        planned_book, workspace, monkeypatch, forbid_authority):
    _record_policy(workspace, "autonomous")
    #: The task names p001's approval, but p001 has no draft at all.
    task = {"task_id": f"{BOOK}-p001-approve", "book_id": BOOK, "type": "approval",
            "summary": "Approve page p001", "page_id": "p001", "asset_id": None,
            "gate": None, "mode": "continue_automatically"}
    monkeypatch.setattr(api, "next_task", lambda *a, **k: dict(task))

    result = produce.run(BOOK, root=workspace)
    assert result["steps"] == []
    assert result["stopped_because"] == "not_mechanical"
    assert "no reviewable draft" in result["message"]
    assert forbid_authority == []


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
    folder = workspace / "books" / BOOK
    before = _snapshot(folder)

    result = produce.run(BOOK, root=workspace)

    assert result["steps"] == []
    assert result["stopped_because"] == "writing"
    assert result["next_task"]["type"] == "authoring"
    assert "copy written" in result["message"]
    assert "/write-book" in result["message"]
    assert _snapshot(folder) == before


def test_a_dry_run_at_writing_also_reports_writing(new_book, workspace):
    folder = workspace / "books" / BOOK
    before = _snapshot(folder)

    result = produce.run(BOOK, root=workspace, dry_run=True)

    assert _snapshot(folder) == before
    assert result["steps"] == []
    assert result["stopped_because"] == "writing"
    assert result["next_task"]["type"] == "authoring"


def test_a_cover_authoring_task_is_not_writing():
    task = {"task_id": f"{BOOK}-cover-direction", "type": "authoring",
            "mode": "continue_automatically", "summary": "Record cover direction"}
    code, message = produce._stop_for(BOOK, task)
    assert code == "not_mechanical"
    assert code != "writing"


def test_an_asset_register_task_is_not_writing():
    task = {"task_id": "fig-scope-register", "type": "authoring", "asset_id": "fig-scope",
            "mode": "continue_automatically", "summary": "Register required visual reference"}
    code, message = produce._stop_for(BOOK, task)
    assert code == "not_mechanical"
    assert code != "writing"


def test_a_lock_operator_decision_task_is_never_writing():
    task = {"task_id": f"{BOOK}-lock-concept", "type": "operator_decision",
            "mode": "wait_for_operator", "summary": "Approve and lock the concept"}
    code, message = produce._stop_for(BOOK, task)
    assert code == "wait_for_operator"
    assert code != "writing"


def test_a_checkpointed_books_authoring_task_still_waits_for_the_operator():
    """Mode is decided before the authoring check, whatever the task type."""
    task = {"task_id": f"{BOOK}-brief", "type": "authoring",
            "mode": "wait_for_operator", "summary": "Complete the book brief"}
    code, message = produce._stop_for(BOOK, task)
    assert code == "wait_for_operator"
    assert code != "writing"


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


def test_a_dry_run_reports_a_page_approval_and_changes_nothing(
        planned_book, workspace, forbid_authority):
    _record_policy(workspace, "visual_checkpoint")
    api.render(BOOK, page_id="p001", submit=True, root=workspace)

    folder = workspace / "books" / BOOK
    manifest = Book.load(BOOK, workspace).paths.manifest_file
    manifest_bytes = manifest.read_bytes()
    before = _snapshot(folder)

    result = produce.run(BOOK, root=workspace, dry_run=True)

    assert manifest.read_bytes() == manifest_bytes
    assert _snapshot(folder) == before
    assert result["stopped_because"] == "dry_run"
    assert result["steps"] == []
    assert result["next_task"]["task_id"] == f"{BOOK}-p001-approve"
    assert (f"bookfactory approve {BOOK} p001 --kind page --draft v1 --by produce "
            "--autonomous") in result["message"]
    assert forbid_authority == []
    assert not Book.load(BOOK, workspace).manifest.get("p001").is_approved


def test_a_dry_run_says_why_it_would_stop(new_book, workspace):
    folder = workspace / "books" / BOOK
    before = _snapshot(folder)
    result = produce.run(BOOK, root=workspace, dry_run=True)
    assert _snapshot(folder) == before
    assert result["stopped_because"] == "writing"


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
