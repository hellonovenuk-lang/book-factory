"""Project creation and canonical state."""

from __future__ import annotations

import json

import pytest

from bookfactory.core import api, stages
from bookfactory.core.book import Book
from bookfactory.core.errors import BookAlreadyExists, BookNotFound, ValidationError
from bookfactory.core.models import BookState


def test_create_book_writes_canonical_state(workspace):
    result = api.create_book("Golf Addict", policy="checkpointed", root=workspace, target_page_count=90)
    assert result["book_id"] == "golf-addict"

    book = Book.load("golf-addict", workspace)
    assert book.state.title == "Golf Addict"
    assert book.state.format.trim == "6x9"
    assert book.state.format.target_page_count == 90
    assert book.paths.state_file.is_file()
    assert book.paths.manifest_file.is_file()
    assert book.paths.asset_registry.is_file()


def test_create_book_scaffolds_the_guided_templates(new_book):
    for path in (new_book.paths.brief_file, new_book.paths.concept_file,
                 new_book.paths.voice_bible, new_book.paths.visual_bible,
                 new_book.paths.outline_file, new_book.paths.design_tokens,
                 new_book.paths.reference_set, new_book.paths.readme):
        assert path.is_file(), f"{path} was not scaffolded"


def test_book_json_answers_the_questions_a_fresh_agent_asks(new_book):
    data = json.loads(new_book.paths.state_file.read_text())
    for key in ("book_id", "title", "stage", "format", "manuscript", "style",
                "page_plan", "next_action", "updated_at"):
        assert key in data, f"book.json is missing {key}"
    assert data["next_action"]["summary"]


def test_state_round_trips_without_losing_anything(new_book):
    data = new_book.state.to_dict()
    assert BookState.from_dict(data).to_dict() == data


def test_duplicate_book_id_is_refused(workspace):
    api.create_book("Test Book", policy="checkpointed", book_id="test-book", root=workspace)
    with pytest.raises(BookAlreadyExists):
        api.create_book("Test Book", policy="checkpointed", book_id="test-book", root=workspace)


def test_unknown_book_is_reported_with_what_is_available(workspace):
    api.create_book("Test Book", policy="checkpointed", book_id="test-book", root=workspace)
    with pytest.raises(BookNotFound) as excinfo:
        Book.load("no-such-book", workspace)
    assert "test-book" in excinfo.value.remedy


def test_invalid_book_id_is_rejected(workspace):
    with pytest.raises(ValidationError):
        api.create_book("Test", policy="checkpointed", book_id="Not A Valid Id", root=workspace)


def test_corrupt_state_file_is_rejected_not_guessed(new_book):
    new_book.paths.state_file.write_text('{"book_id": "test-book"}', encoding="utf-8")
    with pytest.raises(ValidationError) as excinfo:
        Book.load("test-book", new_book.paths.root.parent.parent)
    assert excinfo.value.problems


def test_state_with_unknown_stage_is_rejected(new_book, workspace):
    data = json.loads(new_book.paths.state_file.read_text())
    data["stage"] = "vibes"
    new_book.paths.state_file.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValidationError):
        Book.load("test-book", workspace)


def test_stage_cannot_move_backwards(locked_book, workspace):
    with pytest.raises(ValidationError):
        api.advance("test-book", stages.IDEA, root=workspace)


def test_stage_is_derived_from_repository_evidence(locked_book):
    """The stage describes where the book actually is, not a flag someone set."""
    assert locked_book.state.stage == stages.VISUAL_LOCK
    assert locked_book.state.manuscript.locked
    assert locked_book.state.style.visual_locked


def test_audit_log_records_meaningful_events_only(locked_book, workspace):
    events = [record["event"] for record in api.audit_history("test-book", root=workspace)]
    assert "book_created" in events
    assert "concept_locked" in events
    assert "manuscript_locked" in events
    assert "visual_locked" in events
    assert all(event in _KNOWN_EVENTS for event in events), events


_KNOWN_EVENTS = {
    "book_created", "stage_advanced", "concept_locked", "voice_locked", "manuscript_locked",
    "visual_locked", "page_planned", "draft_submitted", "approved", "rejected",
    "revision_opened", "qa_run", "assembled", "review_generated", "preflight_run",
    "blocked", "unblocked", "cover_required", "cover_draft_submitted", "cover_approved",
    "production_policy_recorded", "production_policy_changed", "picture_budget_changed",
}


def test_blocking_surfaces_in_state_and_in_next(new_book, workspace):
    api.block("test-book", "Waiting on the operator to choose a title", root=workspace)
    book = Book.load("test-book", workspace)
    assert book.state.blocked["reason"].startswith("Waiting")
    assert "Unblock" in book.state.next_action["summary"]
    api.unblock("test-book", root=workspace)
    assert Book.load("test-book", workspace).state.blocked is None
