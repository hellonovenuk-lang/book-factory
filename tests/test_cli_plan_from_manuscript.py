"""`bookfactory plan <book> --from-manuscript --out <plan.json>`.

The command writes a plan file and nothing else; loading it into the book
stays `plan --from-file`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bookfactory.cli.main import main
from bookfactory.core.book import Book

MANUSCRIPT = """# Test Book

## Front matter

### Title page

Test Book

A small book used to prove the production system works.

## Stage One: Arrival

### Chapter opener

Stage One: Arrival

Induction for returning testers.

Welcome back. Please leave your laptop at the door.

[Picture: chapter opener. A tester on the doorstep holding a laptop.]

### Why you are here

You have been running tests for a long time. Your family would like you back.

Nobody is taking your laptop away. It is going in a drawer for the evening.

### No. 01 · Checklist: Arrival kit

- [ ] One front door key.
- [ ] One pair of indoor shoes.
"""


def _snapshot(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _write_manuscript(book: Book) -> None:
    book.paths.manuscript_file.write_text(MANUSCRIPT, encoding="utf-8")


def test_writes_a_plan_file_and_changes_nothing_in_the_book(locked_book, workspace, tmp_path,
                                                            capsys):
    _write_manuscript(locked_book)
    before = _snapshot(locked_book.paths.root)
    out = tmp_path / "plan.json"

    code = main(["--root", str(workspace), "--json", "plan", "test-book",
                 "--from-manuscript", "--out", str(out), "--backend", "weasyprint"])

    assert code == 0
    result = json.loads(capsys.readouterr().out)
    plan = json.loads(out.read_text())
    assert [p["type"] for p in plan["pages"]] == [
        "front_matter", "chapter_opener", "text_illustration", "activity"]
    assert plan["warnings"] == []
    assert {e["status"] for e in plan["fit"]} == {"fits"}
    assert result["pages"] == 4
    assert _snapshot(locked_book.paths.root) == before


def test_the_plan_file_loads_with_from_file(locked_book, workspace, tmp_path, capsys):
    _write_manuscript(locked_book)
    out = tmp_path / "plan.json"
    assert main(["--root", str(workspace), "plan", "test-book", "--from-manuscript",
                 "--out", str(out), "--backend", "weasyprint"]) == 0
    capsys.readouterr()

    code = main(["--root", str(workspace), "--json", "plan", "test-book",
                 "--from-file", str(out)])

    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["specs"] == 4
    assert result["assets_registered"] == ["art-stage-01-opener"]


def test_refuses_an_unlocked_manuscript(new_book, workspace, tmp_path, capsys):
    out = tmp_path / "plan.json"

    code = main(["--root", str(workspace), "plan", "test-book", "--from-manuscript",
                 "--out", str(out)])

    assert code != 0
    captured = capsys.readouterr()
    assert "not locked" in captured.err + captured.out
    assert not out.exists()


def test_needs_out(locked_book, workspace, capsys):
    code = main(["--root", str(workspace), "plan", "test-book", "--from-manuscript"])

    assert code == 2
    assert not list(locked_book.paths.root.glob("**/plan.json"))


def test_human_output_says_nothing_changed(locked_book, workspace, tmp_path, capsys):
    _write_manuscript(locked_book)
    out = tmp_path / "plan.json"

    code = main(["--root", str(workspace), "plan", "test-book", "--from-manuscript",
                 "--out", str(out), "--backend", "weasyprint"])

    assert code == 0
    text = capsys.readouterr().out
    assert "Nothing in the book has changed" in text
    assert f"--from-file {out}" in text
