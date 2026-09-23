"""The `bookfactory produce` command line: a thin wrapper over `api.produce`."""

from __future__ import annotations

import json

import pytest

from bookfactory.cli.main import main

BOOK = "test-book"


def run(capsys, *argv) -> tuple[int, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def run_json(capsys, *argv) -> tuple[int, object]:
    code, out = run(capsys, "--json", *argv)
    return code, json.loads(out)


def test_help_lists_produce(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    assert "produce" in out


def test_json_output_has_stopped_because(capsys, planned_book, workspace):
    code, data = run_json(capsys, "--root", str(workspace), "produce", BOOK, "--max-steps", "1")
    assert code == 0
    assert "stopped_because" in data
    assert data["book_id"] == BOOK


def test_dry_run_changes_nothing(capsys, planned_book, workspace):
    from bookfactory.core.book import Book

    before = Book.load(BOOK, workspace).manifest.get("p001").latest_draft()
    code, data = run_json(capsys, "--root", str(workspace), "produce", BOOK, "--dry-run")
    assert code == 0
    assert data["dry_run"] is True
    assert data["stopped_because"] == "dry_run"
    after = Book.load(BOOK, workspace).manifest.get("p001").latest_draft()
    assert before == after


def test_human_output_contains_the_message(capsys, planned_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "produce", BOOK, "--max-steps", "1")
    assert code == 0
    assert "PRODUCE" in out
    assert "p001" in out


def test_max_steps_zero_is_refused(capsys, planned_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "produce", BOOK, "--max-steps", "0")
    assert code != 0
    assert "max_steps" in out or "at least" in out
