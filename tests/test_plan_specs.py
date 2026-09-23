"""Page plan and specs in one file, with artwork registered from each spec.

See `PLAN.md`, "Phase 8: Page plan and specs in one file", for the contract
these tests check.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from bookfactory.cli.main import main
from bookfactory.core import api, tasks
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from tests.conftest import PAGE_PLAN


def _plan_without_required_assets() -> list[dict]:
    """The test plan with its specs, leaving the artwork to be found in the specs."""
    pages = copy.deepcopy(PAGE_PLAN)
    for page in pages:
        page.pop("required_assets", None)
    return pages


def test_one_plan_file_writes_every_spec_and_registers_the_artwork(
    locked_book: Book, workspace: Path,
) -> None:
    result = api.plan_pages("test-book", _plan_without_required_assets(), root=workspace)

    assert result["total"] == len(PAGE_PLAN)
    assert result["specs"] == len(PAGE_PLAN)
    assert result["assets_registered"] == ["fig-scope"]

    book = Book.load("test-book", workspace)
    assert all(page.spec for page in book.manifest)
    page = book.manifest.get("p002")
    assert page.required_assets == ["fig-scope"]
    asset = book.registry.get("fig-scope")
    assert asset.kind == "illustration"
    assert asset.page_id == "p002"
    assert asset.title == page.title
    assert asset.description == "A neglected garden."

    planned = api.audit_history("test-book", root=workspace, event="page_planned")
    assert planned[-1]["assets_registered"] == ["fig-scope"]


def test_next_task_skips_straight_to_the_artwork(locked_book: Book, workspace: Path) -> None:
    api.plan_pages("test-book", _plan_without_required_assets(), root=workspace)
    task = tasks.next_task(Book.load("test-book", workspace))
    assert task is not None
    assert not task.task_id.endswith("-spec")
    assert not task.task_id.endswith("-register")


def test_one_bad_spec_refuses_the_whole_file_and_changes_nothing(
    locked_book: Book, workspace: Path,
) -> None:
    pages = _plan_without_required_assets()
    pages[2]["spec"]["not_a_spec_field"] = "oops"
    specs_dir = locked_book.paths.root / "pages" / "specs"
    before = sorted(p.name for p in specs_dir.glob("*")) if specs_dir.exists() else []

    with pytest.raises(ValidationError) as caught:
        api.plan_pages("test-book", pages, root=workspace)

    assert any(problem.startswith("p003:") for problem in caught.value.problems)
    book = Book.load("test-book", workspace)
    assert len(book.manifest) == 0
    assert book.registry.find("fig-scope") is None
    after = sorted(p.name for p in specs_dir.glob("*")) if specs_dir.exists() else []
    assert after == before


def test_spec_command_registers_its_artwork(locked_book: Book, workspace: Path) -> None:
    pages = [{k: v for k, v in page.items() if k not in ("spec", "required_assets")}
             for page in PAGE_PLAN]
    api.plan_pages("test-book", pages, root=workspace)

    result = api.write_page_spec("test-book", "p002", PAGE_PLAN[1]["spec"], root=workspace)

    assert result["assets_registered"] == ["fig-scope"]
    book = Book.load("test-book", workspace)
    assert book.manifest.get("p002").required_assets == ["fig-scope"]


def test_already_registered_artwork_is_left_alone(locked_book: Book, workspace: Path) -> None:
    api.register_asset("test-book", "fig-scope", root=workspace, kind="illustration",
                       title="Chosen by hand", page_id="p002")

    result = api.plan_pages("test-book", _plan_without_required_assets(), root=workspace)

    assert result["assets_registered"] == []
    book = Book.load("test-book", workspace)
    assert book.registry.get("fig-scope").title == "Chosen by hand"
    assert book.manifest.get("p002").required_assets == ["fig-scope"]


def test_listed_and_spec_artwork_are_not_doubled(locked_book: Book, workspace: Path) -> None:
    api.plan_pages("test-book", copy.deepcopy(PAGE_PLAN), root=workspace)
    book = Book.load("test-book", workspace)
    assert book.manifest.get("p002").required_assets == ["fig-scope"]


def test_cli_plan_from_file_reports_specs_and_artwork(
    locked_book: Book, workspace: Path, tmp_path: Path, capsys,
) -> None:
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps({"pages": _plan_without_required_assets()}),
                         encoding="utf-8")

    code = main(["plan", "test-book", "--from-file", str(plan_file),
                 "--root", str(workspace), "--json"])

    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["specs"] == len(PAGE_PLAN)
    assert output["assets_registered"] == ["fig-scope"]
