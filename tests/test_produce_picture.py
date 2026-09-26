"""`produce` stops with the distinct code `picture` at a page's own illustration.

Pictures are drawn by Claude Code through the Higgsfield connector - a chat
tool, unreachable from here - so `produce` cannot draw one itself. It says so
plainly, the same way it already says `writing` for copy, so a caller such as
`/write-book` knows to draw the picture and run `produce` again. The cover's
own artwork, a picture's approval, and anything not in `continue_automatically`
mode are unaffected (AGENTS.md 2a, 3, 5).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from bookfactory.core import api, produce
from bookfactory.core.book import ASSET, Book

BOOK = "test-book"


def _snapshot(folder: Path) -> dict[str, str]:
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def test_stops_with_picture_at_a_page_illustration_and_changes_nothing(
        produced_book, workspace):
    api.revise(BOOK, "fig-scope", kind=ASSET, reason="Composition too tight", root=workspace)
    folder = workspace / "books" / BOOK
    before = _snapshot(folder)

    result = produce.run(BOOK, root=workspace)

    assert result["steps"] == []
    assert result["stopped_because"] == "picture"
    assert result["next_task"]["type"] == "illustration"
    assert result["next_task"]["asset_id"] == "fig-scope"
    assert result["next_task"]["mode"] == "continue_automatically"
    assert "picture" in result["message"]
    assert "fig-scope" in result["message"]
    assert "/write-book" in result["message"]
    assert _snapshot(folder) == before

    fig = Book.load(BOOK, workspace).registry.find("fig-scope")
    assert fig.revision_open and fig.approved.revision == "v1"


def test_cover_artwork_does_not_give_picture(monkeypatch):
    task = {"task_id": f"{BOOK}-cover-artwork", "book_id": BOOK, "type": "illustration",
            "summary": "Produce native text-free cover artwork", "page_id": None,
            "asset_id": "cover-front-artwork", "gate": None, "mode": "continue_automatically"}
    code, message = produce._stop_for(BOOK, task)
    assert code == "not_mechanical"
    assert code != "picture"


def test_a_waiting_illustration_does_not_give_picture():
    task = {"task_id": f"{BOOK}-fig-scope-illustration", "book_id": BOOK, "type": "illustration",
            "summary": "Create illustration 'fig-scope' for page p002", "page_id": "p002",
            "asset_id": "fig-scope", "gate": None, "mode": "wait_for_operator"}
    code, message = produce._stop_for(BOOK, task)
    assert code == "wait_for_operator"
    assert code != "picture"


def test_a_dry_run_reports_the_picture_stop_and_changes_nothing(produced_book, workspace):
    api.revise(BOOK, "fig-scope", kind=ASSET, reason="Composition too tight", root=workspace)
    folder = workspace / "books" / BOOK
    before = _snapshot(folder)

    result = produce.run(BOOK, root=workspace, dry_run=True)

    assert _snapshot(folder) == before
    assert result["steps"] == []
    assert result["stopped_because"] == "picture"
    assert result["next_task"]["asset_id"] == "fig-scope"
