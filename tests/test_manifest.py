"""The page manifest: the authoritative list of what is in the book."""

from __future__ import annotations

import pytest

from bookfactory.core import api
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.manifest import PageManifest
from bookfactory.core.models import PageRecord


def _page(page_id: str, sequence: int, **kwargs) -> PageRecord:
    return PageRecord(page_id=page_id, sequence=sequence,
                      title=kwargs.pop("title", "A page"),
                      type=kwargs.pop("type", "editorial_illustration"), **kwargs)


def test_duplicate_page_id_is_refused():
    manifest = PageManifest.empty("test-book")
    manifest.add(_page("p001", 1))
    with pytest.raises(ValidationError):
        manifest.add(_page("p001", 2))


def test_duplicate_sequence_is_refused():
    manifest = PageManifest.empty("test-book")
    manifest.add(_page("p001", 1))
    with pytest.raises(ValidationError) as excinfo:
        manifest.add(_page("p002", 1))
    assert "already taken" in str(excinfo.value)


def test_gap_in_the_sequence_is_reported():
    manifest = PageManifest.empty("test-book")
    manifest.add(_page("p001", 1))
    manifest.add(_page("p003", 3))
    problems = manifest.problems()
    assert any("gaps in page sequence: 2" in problem for problem in problems)


def test_sequence_must_start_at_one():
    manifest = PageManifest.empty("test-book")
    manifest.add(_page("p004", 4))
    assert any("starts at 4" in problem for problem in manifest.problems())


def test_filename_collision_between_pages_is_reported():
    """The old workflow reused 'early_signs_of_progress.png' across chapters."""
    from bookfactory.core.models import ApprovalRecord

    manifest = PageManifest.empty("test-book")
    approval = ApprovalRecord(revision="v1", path="pages/approved/shared.pdf",
                              sha256="abc", approved_at="2026-01-01T00:00:00Z")
    first = _page("p001", 1)
    second = _page("p002", 2)
    first.approved = approval
    second.approved = ApprovalRecord(**approval.to_dict())
    manifest.add(first)
    manifest.add(second)
    assert any("filename collision" in problem for problem in manifest.problems())


def test_canonical_filenames_lead_with_the_id(produced_book):
    """Identity is the id; the title is only there to help a human read the folder."""
    names = [book_page.approved.path.rsplit("/", 1)[-1] for book_page in produced_book.manifest]
    assert names == ["p001-the-assessment.pdf", "p002-scope-of-the-manual.pdf",
                     "p003-severity-assessment.pdf", "p004-closing-note.pdf"]


def test_printed_numbers_skip_front_matter_and_run_consecutively(workspace, locked_book):
    pages = [{"title": f"Page {index}", "type": "quote"} for index in range(1, 7)]
    api.plan_pages("test-book", pages, root=workspace, front_matter_pages=2)
    book = Book.load("test-book", workspace)
    numbers = [(page.sequence, page.printed_number) for page in book.manifest]
    assert numbers == [(1, None), (2, None), (3, 1), (4, 2), (5, 3), (6, 4)]
    assert book.manifest.problems() == []


def test_duplicate_printed_numbers_are_caught_by_technical_qa(produced_book, workspace):
    from bookfactory.qa import technical

    produced_book.manifest.get("p002").printed_number = 1
    produced_book.save()
    codes = [finding.code for finding in technical.check(produced_book).findings]
    assert "technical.duplicate_printed_number" in codes


def test_approved_page_cannot_be_dropped_from_the_manifest(produced_book):
    with pytest.raises(ValidationError):
        produced_book.manifest.remove("p001")


def test_missing_page_spec_is_reported_by_validate(planned_book, workspace):
    planned_book.paths.spec_file("p003").unlink()
    result = api.validate("test-book", root=workspace)
    assert result["ok"] is False
    assert any("p003" in problem for problem in result["problems"])
