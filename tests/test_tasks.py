"""`bookfactory next` - the command that makes fresh-session operation possible."""

from __future__ import annotations

from bookfactory.core import api
from bookfactory.core.book import PAGE, Book
from bookfactory.core.tasks import next_task


def test_a_brand_new_book_asks_for_the_brief(new_book, workspace):
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "authoring"
    assert "brief" in task["summary"].lower()
    assert task["approval_required"] is True


def test_next_is_cached_into_book_json_so_a_bare_read_is_enough(new_book, workspace):
    from bookfactory.core.jsonio import read_json

    api.next_task("test-book", root=workspace)
    data = read_json(new_book.paths.state_file)
    assert data["next_action"]["task_id"].startswith("test-book-")
    assert data["next_action"]["summary"]


def test_a_locked_book_with_no_pages_asks_for_the_page_plan(locked_book, workspace):
    task = api.next_task("test-book", root=workspace)
    assert "page plan" in task["summary"].lower()
    assert task["output"]["destination"] == "pages/manifest.json"


def test_illustration_tasks_carry_the_locked_references(planned_book, workspace):
    """A visual task must point at approved reference files, not describe them again."""
    api.render("test-book", page_id="p001", submit=True, root=workspace)
    api.approve("test-book", "p001", kind=PAGE, root=workspace)

    book = Book.load("test-book", workspace)
    asset = book.registry.get("fig-scope")
    asset.approved = None
    asset.status = "planned"
    asset.drafts = []
    book.save()

    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "illustration"
    assert task["asset_id"] == "fig-scope"
    assert task["constraints"]["embedded_text"] is False
    assert task["constraints"]["maintain_character_identity"] is True
    assert task["output"]["destination"] == "assets/drafts/fig-scope/"
    assert any("style/references" in reference or "assets/approved" in reference
               for reference in task["references"])


def test_a_submitted_draft_produces_an_explicit_approval_task(planned_book, workspace):
    api.render("test-book", page_id="p001", submit=True, root=workspace)
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "approval"
    assert task["page_id"] == "p001"
    assert "approve" in task["instructions"]
    assert "reject" in task["instructions"]
    assert task["approval_required"] is True


def test_nothing_is_approved_by_silence(planned_book, workspace):
    """The task text must make explicit approval the only route forward."""
    api.render("test-book", page_id="p001", submit=True, root=workspace)
    task = api.next_task("test-book", root=workspace)
    assert "Nothing is approved by silence" in task["instructions"]


def test_after_every_page_is_approved_the_next_step_is_qa(produced_book, workspace):
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "qa"


def test_after_qa_the_next_step_is_assembly(produced_book, workspace):
    api.qa("test-book", root=workspace)
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "assembly"


def test_after_assembly_the_next_step_is_preflight(produced_book, workspace):
    api.qa("test-book", root=workspace)
    api.assemble("test-book", root=workspace)
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "preflight"


def test_the_open_task_directory_holds_exactly_one_current_task(produced_book, workspace):
    api.next_task("test-book", root=workspace)
    book = Book.load("test-book", workspace)
    open_tasks = list(book.paths.open_tasks_dir.glob("*.json"))
    assert len(open_tasks) == 1

    api.qa("test-book", root=workspace)
    api.next_task("test-book", root=workspace)
    book = Book.load("test-book", workspace)
    assert len(list(book.paths.open_tasks_dir.glob("*.json"))) == 1, "stale tasks must be closed"
    assert list(book.paths.done_tasks_dir.glob("*.json")), "closed tasks are kept"


def test_derivation_is_pure(produced_book):
    first = next_task(produced_book).to_dict()
    second = next_task(produced_book).to_dict()
    first.pop("created_at")
    second.pop("created_at")
    assert first == second


def test_a_finished_book_has_no_next_task(workspace):
    from bookfactory.core.paths import books_dir
    import pytest

    if not (books_dir() / "demo-book" / "book.json").is_file():
        pytest.skip("demo book fixture not present")
    assert next_task(Book.load("demo-book")) is None
