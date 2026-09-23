"""The picture budget: how many page pictures a book may have.

See `PLAN.md`, "Phase 11: Picture budget and the Higgsfield routine", for the
contract these tests check.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from bookfactory.cli.main import main
from bookfactory.core import api
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.tasks import next_task
from tests.conftest import PAGE_PLAN


def _opener(title: str, asset_id: str | None) -> dict:
    illustration = ({"asset_id": asset_id, "concept": "A scene."} if asset_id else None)
    return {"title": title, "type": "chapter_opener", "chapter": 1,
            "spec": {"copy": {"heading": title}, "illustration": illustration}}


def _editorial(title: str, asset_id: str) -> dict:
    return {"title": title, "type": "editorial_illustration", "chapter": 1,
            "spec": {"copy": {"heading": title},
                     "illustration": {"asset_id": asset_id, "concept": "A scene."}}}


def _default_budget(workspace: Path) -> None:
    """Put the locked test book back on the new-book default."""
    api.set_pictures("test-book", "chapter_openers", by="tester", root=workspace)


def test_a_new_book_allows_pictures_only_on_chapter_openers(new_book: Book) -> None:
    assert new_book.state.pictures.budget == "chapter_openers"
    assert new_book.state.pictures.source == "new_book_default"


def test_a_book_made_before_budgets_loads_as_unlimited(new_book: Book, workspace: Path) -> None:
    data = json.loads(new_book.paths.state_file.read_text())
    del data["pictures"]
    new_book.paths.state_file.write_text(json.dumps(data))
    assert Book.load("test-book", workspace).state.pictures.budget == "unlimited"


def test_chapter_opener_pictures_are_allowed(locked_book: Book, workspace: Path) -> None:
    _default_budget(workspace)
    result = api.plan_pages("test-book", [_opener("One", "art-one"), _opener("Two", None)],
                            root=workspace)
    assert result["assets_registered"] == ["art-one"]


def test_a_picture_on_another_page_type_refuses_the_whole_plan(
    locked_book: Book, workspace: Path,
) -> None:
    _default_budget(workspace)
    with pytest.raises(ValidationError) as caught:
        api.plan_pages("test-book", [_opener("One", "art-one"), _editorial("Two", "art-two")],
                       root=workspace)
    assert len(caught.value.problems) == 1
    problem = caught.value.problems[0]
    assert problem.startswith("p002:")
    assert "chapter_openers" in problem and "pictures set" in problem
    book = Book.load("test-book", workspace)
    assert len(book.manifest) == 0
    assert book.registry.find("art-one") is None


def test_the_spec_command_is_checked_too(locked_book: Book, workspace: Path) -> None:
    _default_budget(workspace)
    api.plan_pages("test-book", [{"title": "Two", "type": "editorial_illustration"}],
                   root=workspace)
    with pytest.raises(ValidationError, match="picture budget"):
        api.write_page_spec("test-book", "p001", _editorial("Two", "art-two")["spec"],
                            root=workspace)


def test_a_limit_counts_the_whole_plan(locked_book: Book, workspace: Path) -> None:
    api.set_pictures("test-book", "limit", count=2, by="tester", root=workspace)
    pages = [_editorial("One", "a1"), _editorial("Two", "a2"), _editorial("Three", "a3")]
    with pytest.raises(ValidationError) as caught:
        api.plan_pages("test-book", pages, root=workspace)
    assert [p.split(":")[0] for p in caught.value.problems] == ["p003"]

    result = api.plan_pages("test-book", pages[:2], root=workspace)
    assert result["assets_registered"] == ["a1", "a2"]


def test_a_picture_used_twice_counts_once(locked_book: Book, workspace: Path) -> None:
    api.set_pictures("test-book", "limit", count=1, by="tester", root=workspace)
    api.plan_pages("test-book", [_editorial("One", "a1"), _editorial("Two", "a1")],
                   root=workspace)


def test_unlimited_allows_any_page(locked_book: Book, workspace: Path) -> None:
    api.plan_pages("test-book", copy.deepcopy(PAGE_PLAN), root=workspace)


def test_only_the_operator_changes_it_and_it_is_recorded(new_book: Book,
                                                         workspace: Path) -> None:
    with pytest.raises(ValidationError):
        api.set_pictures("test-book", "unlimited", by="", root=workspace)
    with pytest.raises(ValidationError):
        api.set_pictures("test-book", "limit", by="Kieran", root=workspace)
    with pytest.raises(ValidationError):
        api.set_pictures("test-book", "unlimited", count=3, by="Kieran", root=workspace)

    result = api.set_pictures("test-book", "limit", count=12, by="Kieran",
                              reason="Wants a few spot pictures", root=workspace)
    assert result["pictures"]["budget"] == "limit"
    assert result["pictures"]["set_by"] == "Kieran"
    entry = api.audit_history("test-book", root=workspace, event="picture_budget_changed")[-1]
    assert entry["old_budget"] == "chapter_openers"
    assert entry["budget"] == "limit" and entry["count"] == 12 and entry["by"] == "Kieran"


def test_the_page_plan_task_states_the_budget(locked_book: Book, workspace: Path) -> None:
    _default_budget(workspace)
    task = next_task(Book.load("test-book", workspace))
    assert task.task_id.endswith("page-plan")
    assert "Picture budget: chapter_openers" in task.instructions
    assert "Never raise the budget yourself" in task.instructions


def test_status_shows_the_budget(new_book: Book, workspace: Path) -> None:
    assert api.status("test-book", root=workspace)["pictures"] == {
        "budget": "chapter_openers", "count": None, "page_pictures": 0}


def test_cli_show_and_set(new_book: Book, workspace: Path, capsys) -> None:
    assert main(["pictures", "show", "test-book", "--root", str(workspace), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["pictures"]["budget"] == "chapter_openers"
    assert main(["pictures", "set", "test-book", "limit", "--count", "5", "--by", "Kieran",
                 "--root", str(workspace), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["pictures"]["count"] == 5
