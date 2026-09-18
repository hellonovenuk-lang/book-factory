"""Production gates. A blocked gate must always say exactly why."""

from __future__ import annotations

import pytest

from bookfactory.core import api, gates, stages
from bookfactory.core.book import Book
from bookfactory.core.errors import GateBlocked
from tests.conftest import BRIEF, MANUSCRIPT, SAMPLE, VOICE


def test_concept_lock_refuses_a_brief_full_of_placeholders(new_book, workspace):
    with pytest.raises(GateBlocked) as excinfo:
        api.lock("test-book", "concept", root=workspace)
    assert any("TODO" in reason or "empty" in reason for reason in excinfo.value.reasons)


def test_voice_lock_requires_a_real_writing_sample(new_book, workspace):
    new_book.paths.brief_file.write_text(BRIEF, encoding="utf-8")
    new_book.save()
    api.lock("test-book", "concept", root=workspace)

    book = Book.load("test-book", workspace)
    book.paths.voice_bible.write_text(VOICE, encoding="utf-8")
    book.save()
    with pytest.raises(GateBlocked) as excinfo:
        api.lock("test-book", "voice", root=workspace)
    assert any("writing-sample" in reason for reason in excinfo.value.reasons)


def test_manuscript_lock_requires_the_voice_to_be_locked_first(new_book, workspace):
    new_book.paths.brief_file.write_text(BRIEF, encoding="utf-8")
    new_book.paths.manuscript_file.write_text(MANUSCRIPT, encoding="utf-8")
    new_book.save()
    api.lock("test-book", "concept", root=workspace)
    with pytest.raises(GateBlocked) as excinfo:
        api.lock("test-book", "manuscript", root=workspace)
    assert any("voice is not locked" in reason for reason in excinfo.value.reasons)


def test_manuscript_lock_snapshots_and_checksums_the_manuscript(locked_book):
    assert locked_book.state.manuscript.locked
    snapshot = locked_book.paths.manuscript_version_file(locked_book.state.manuscript.version)
    assert snapshot.is_file()
    from bookfactory.core import checksums

    assert checksums.sha256_file(snapshot) == locked_book.state.manuscript.sha256
    assert checksums.is_immutable(snapshot)


def test_visual_lock_refuses_until_every_required_reference_is_approved(
        new_book, workspace):
    new_book.paths.brief_file.write_text(BRIEF, encoding="utf-8")
    new_book.paths.voice_bible.write_text(VOICE, encoding="utf-8")
    new_book.paths.writing_sample_file.write_text(SAMPLE, encoding="utf-8")
    new_book.paths.manuscript_file.write_text(MANUAL_STUB, encoding="utf-8")
    new_book.save()
    api.lock("test-book", "concept", root=workspace)
    api.lock("test-book", "voice", root=workspace)
    api.lock("test-book", "manuscript", root=workspace)

    with pytest.raises(GateBlocked) as excinfo:
        api.lock("test-book", "visual", root=workspace)
    reasons = " ".join(excinfo.value.reasons)
    assert "ref-character-main" in reasons
    assert "has not been registered" in reasons


MANUAL_STUB = MANUSCRIPT


def test_page_production_is_blocked_until_both_locks_are_in_place(new_book, workspace):
    """The single most expensive mistake: producing pages before the style settles."""
    result = gates.page_production(new_book)
    assert result.ok is False
    assert any("manuscript is not locked" in reason for reason in result.reasons)
    assert any("visual style is not locked" in reason for reason in result.reasons)


def test_visual_lock_marks_the_reference_set_as_locked(locked_book):
    references = locked_book.registry.locked_references()
    assert {asset.asset_id for asset in references} == set(locked_book.required_reference_ids())


def test_advance_reports_the_blocking_gate_rather_than_refusing_vaguely(
        planned_book, workspace):
    with pytest.raises(GateBlocked) as excinfo:
        api.advance("test-book", stages.ASSEMBLY, root=workspace)
    assert excinfo.value.reasons
    assert any("not approved" in reason for reason in excinfo.value.reasons)


def test_release_ready_needs_an_assembled_interior_and_a_preflight(produced_book, workspace):
    with pytest.raises(GateBlocked) as excinfo:
        api.advance("test-book", stages.RELEASE_READY, root=workspace)
    joined = " ".join(excinfo.value.reasons)
    assert "interior.pdf" in joined or "preflight" in joined
