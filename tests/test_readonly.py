"""Read-only commands must not change the repository.

`status`, `next`, `task` and `validate` are what every session runs first. If
they write, every look at a book becomes a commit - and a merge conflict with
whoever else is working on it. `qa` writes its report and nothing else.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from bookfactory.cli.main import main as cli
from bookfactory.core import api
from bookfactory.core.book import Book
from tests.conftest import REPO_ROOT, force_remove

READ_ONLY = ("status", "next", "task", "validate")


def _snapshot(root: Path) -> dict[str, tuple[str, int]]:
    """Content hash and mode of every file, plus every directory, under `root`."""
    state = {}
    for path in sorted(root.rglob("*")):
        key = str(path.relative_to(root))
        if path.is_file():
            state[key] = (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode)
        elif path.is_dir():
            state[key + "/"] = ("dir", path.stat().st_mode)
    return state


def _diff(before: dict, after: dict) -> list[str]:
    return sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))


def _run_everything(book_id: str, root: Path) -> None:
    api.status(book_id, root=root)
    api.next_task(book_id, root=root)
    api.get_task(book_id, root=root)
    api.validate(book_id, root=root)
    for command in READ_ONLY:
        for extra in ([], ["--json"]):
            assert cli([command, book_id, "--root", str(root), *extra]) in (0, 1)


@pytest.fixture
def demo_copy(tmp_path: Path) -> Path:
    """The committed demo book - real, finished, with an open revision - in a scratch root."""
    source = REPO_ROOT / "books" / "demo-book"
    if not (source / "book.json").is_file():
        pytest.skip("books/demo-book is not present")
    shutil.copytree(source, tmp_path / "books" / "demo-book")
    yield tmp_path
    force_remove(tmp_path / "books" / "demo-book")


def test_read_only_commands_change_nothing_in_the_demo_book(demo_copy):
    book_dir = demo_copy / "books" / "demo-book"
    before = _snapshot(book_dir)
    _run_everything("demo-book", demo_copy)
    assert _diff(before, _snapshot(book_dir)) == []


def test_read_only_commands_change_nothing_mid_production(produced_book, workspace):
    book_dir = produced_book.paths.root
    before = _snapshot(book_dir)
    _run_everything("test-book", workspace)
    assert _diff(before, _snapshot(book_dir)) == []


def test_qa_writes_only_its_report(produced_book, workspace):
    book_dir = produced_book.paths.root
    before = _snapshot(book_dir)
    api.qa("test-book", root=workspace)
    changed = _diff(before, _snapshot(book_dir))
    assert "qa/latest.json" in changed
    reports = [c for c in changed if c.startswith("qa/reports/")]
    assert len(reports) == 1
    assert set(changed) == {"qa/latest.json", *reports}


def test_read_only_views_reflect_a_new_qa_report_without_saving(produced_book, workspace):
    """After `qa`, `next` and `status` move on at once, although QA saved no state."""
    assert api.next_task("test-book", root=workspace)["type"] == "qa"
    api.qa("test-book", root=workspace)
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "assembly"
    status = api.status("test-book", root=workspace)
    assert status["next_action"]["task_id"] == task["task_id"]
    assert status["stage"] == Book.load("test-book", workspace).derived_stage()


def test_next_persist_is_the_explicit_opt_in_to_writing_the_open_task(produced_book, workspace):
    book = Book.load("test-book", workspace)
    for stale in book.paths.open_tasks_dir.glob("*.json"):
        stale.unlink()
    api.next_task("test-book", root=workspace)
    assert list(book.paths.open_tasks_dir.glob("*.json")) == []

    assert cli(["next", "test-book", "--persist", "--root", str(workspace)]) == 0
    written = list(book.paths.open_tasks_dir.glob("*.json"))
    assert len(written) == 1
    assert Book.load("test-book", workspace).state.next_action["task_id"] == written[0].stem
