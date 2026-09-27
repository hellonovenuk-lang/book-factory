"""A revised-and-reapproved page must make the assembled interior stale.

On a real book five approved pages were revised and re-approved after
assembly, but `status` still reported the interior as ready and `next` moved
straight on to the cover, although `output/interior.pdf` still held the old
pages. `Book.interior_current()` is the fix: the interior only counts as
current when the manifest assembly wrote alongside it still matches the pages
approved right now, checksum for checksum.
"""

from __future__ import annotations

from bookfactory.core import api, tasks as task_module
from bookfactory.core.book import PAGE, Book


def _revise_and_reapprove(workspace, page_id: str) -> None:
    """Open a revision, change the page's actual content, and re-approve it.

    A real edit, not just a new revision number: the render must come out
    different bytes so the checksum actually changes, the way a real
    corrected page would.
    """
    api.revise("test-book", page_id, kind=PAGE, reason="typo", root=workspace)
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec(page_id)
    spec["copy"]["attribution"] = spec["copy"].get("attribution", "") + " (corrected)"
    book.write_page_spec(page_id, spec)
    book.save()
    api.render("test-book", page_id=page_id, submit=True, root=workspace)
    api.approve("test-book", page_id, kind=PAGE, root=workspace, by="tester")


def test_untouched_book_stays_current(produced_book, workspace):
    api.qa("test-book", root=workspace)
    api.assemble("test-book", root=workspace)
    book = Book.load("test-book", workspace)
    assert book.interior_current()

    status = api.status("test-book", root=workspace)
    assert status["readiness"]["interior"] != "stale"

    task = task_module.next_task(book)
    assert task is None or task.task_id != "test-book-assemble"


def test_revised_and_reapproved_page_makes_interior_stale(produced_book, workspace):
    api.qa("test-book", root=workspace)
    api.assemble("test-book", root=workspace)

    _revise_and_reapprove(workspace, "p004")

    book = Book.load("test-book", workspace)
    assert not book.interior_current()

    status = api.status("test-book", root=workspace)
    assert status["readiness"]["interior"] == "stale"

    task = task_module.next_task(book)
    assert task is not None
    assert task.task_id == "test-book-assemble"
    assert task.type == "assembly"
    assert "out of date" in task.instructions.lower()


def test_reassembling_makes_it_current_again(produced_book, workspace):
    api.qa("test-book", root=workspace)
    api.assemble("test-book", root=workspace)
    _revise_and_reapprove(workspace, "p004")
    assert not Book.load("test-book", workspace).interior_current()

    api.qa("test-book", root=workspace)
    api.assemble("test-book", root=workspace)

    book = Book.load("test-book", workspace)
    assert book.interior_current()

    status = api.status("test-book", root=workspace)
    assert status["readiness"]["interior"] != "stale"

    task = task_module.next_task(book)
    assert task is None or task.task_id != "test-book-assemble"


def test_stale_interior_blocks_release_ready(produced_book, workspace):
    from bookfactory.core import gates

    api.assemble("test-book", root=workspace)
    _revise_and_reapprove(workspace, "p004")

    book = Book.load("test-book", workspace)
    result = gates.release_ready(book)
    assert not result.ok
    assert any("stale" in reason for reason in result.reasons)


def test_preflight_from_before_reassembly_no_longer_counts(produced_book, workspace):
    """A preflight run on the old interior must be run again after re-assembly."""
    api.qa("test-book", root=workspace)
    api.assemble("test-book", root=workspace)
    api.preflight("test-book", root=workspace)
    assert Book.load("test-book", workspace).latest_preflight() is not None

    _revise_and_reapprove(workspace, "p004")
    api.qa("test-book", root=workspace)
    api.assemble("test-book", root=workspace)

    book = Book.load("test-book", workspace)
    assert book.interior_current()
    assert book.latest_preflight() is None
    task = task_module.next_task(book)
    assert task is not None and task.type == "preflight"
