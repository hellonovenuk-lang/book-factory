"""The command line. Human output first, JSON for agents."""

from __future__ import annotations

import json

import pytest

from bookfactory.cli.main import main
from bookfactory.core import api


def run(capsys, *argv) -> tuple[int, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def run_json(capsys, *argv) -> tuple[int, object]:
    code, out = run(capsys, "--json", *argv)
    return code, json.loads(out)


def test_help_lists_the_operations(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    for command in ("create", "status", "next", "approve", "assemble", "preflight"):
        assert command in out


def test_status_reads_like_a_production_report(capsys, produced_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "status", "test-book")
    assert code == 0
    assert "BOOK: Test Book" in out
    assert "STAGE" in out
    assert "MANUSCRIPT" in out
    assert "LOCKED" in out
    assert "PAGES" in out
    assert "APPROVED" in out
    assert "NEXT" in out


def test_status_json_gives_an_agent_everything(capsys, produced_book, workspace):
    code, data = run_json(capsys, "--root", str(workspace), "status", "test-book")
    assert code == 0
    for key in ("book_id", "stage", "format", "manuscript", "style", "pages",
                "assets", "next_action", "gates"):
        assert key in data
    assert data["pages"]["approved"] == 4


def test_next_prints_the_single_next_action(capsys, produced_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "next", "test-book")
    assert code == 0
    assert "NEXT ACTION" in out
    assert "TASK" in out


def test_next_json_matches_the_task_schema(capsys, produced_book, workspace):
    from bookfactory.core import schema

    code, data = run_json(capsys, "--root", str(workspace), "next", "test-book")
    assert code == 0
    schema.validate("task", data, context="cli next")


def test_validate_reports_ok_on_a_sound_book(capsys, produced_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "validate", "test-book")
    assert code == 0
    assert "structurally sound" in out


def test_validate_exits_non_zero_when_state_is_broken(capsys, produced_book, workspace):
    import os

    page = produced_book.manifest.get("p001")
    path = produced_book.paths.resolve(page.approved.path)
    os.chmod(path, 0o644)
    path.write_bytes(b"tampered")

    code, out = run(capsys, "--root", str(workspace), "validate", "test-book")
    assert code == 1
    assert "checksum mismatch" in out


def test_errors_are_reported_with_a_remedy(capsys, workspace):
    code, out = run(capsys, "--root", str(workspace), "status", "no-such-book")
    assert code == 4
    assert "ERROR" in out


def test_errors_are_machine_readable_in_json_mode(capsys, workspace):
    code, data = run_json(capsys, "--root", str(workspace), "status", "no-such-book")
    assert code == 4
    assert data["error"] == "BookNotFound"
    assert "message" in data and "remedy" in data


def test_approve_tells_the_operator_the_artefact_is_now_immutable(
        capsys, planned_book, workspace):
    api.render("test-book", page_id="p001", submit=True, root=workspace)
    code, out = run(capsys, "--root", str(workspace), "approve", "test-book", "p001",
                    "--kind", "page")
    assert code == 0
    assert "APPROVED" in out
    assert "immutable" in out
    assert "revise" in out


def test_qa_exits_non_zero_on_failure(capsys, planned_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "qa", "test-book")
    assert code == 1
    assert "QUALITY ASSURANCE" in out


def test_assemble_failure_explains_itself(capsys, planned_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "assemble", "test-book")
    assert code == 9
    assert "not approved" in out


def test_stages_command_documents_the_process(capsys):
    code, out = run(capsys, "stages")
    assert code == 0
    assert "Visual Lock" in out
    assert "approval gate" in out


def test_doctor_reports_the_render_backend(capsys):
    code, out = run(capsys, "doctor")
    assert code == 0
    assert "render backends" in out


def test_list_shows_every_book(capsys, produced_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "list")
    assert code == 0
    assert "test-book" in out


def test_history_shows_the_audit_trail(capsys, produced_book, workspace):
    code, out = run(capsys, "--root", str(workspace), "history", "test-book", "--limit", "100")
    assert code == 0
    assert "book_created" in out
    assert "approved" in out


def test_task_command_returns_the_full_task(capsys, planned_book, workspace):
    code, data = run_json(capsys, "--root", str(workspace), "task", "test-book")
    assert code == 0
    assert data["task_id"].startswith("test-book-")


def test_json_flag_works_after_the_subcommand(capsys, produced_book, workspace):
    """`bookfactory next <book> --json` is the form every document shows and the
    form an agent reaches for. It has to work."""
    code = main(["next", "test-book", "--root", str(workspace), "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["book_id"] == "test-book"


def test_json_flag_works_before_the_subcommand(capsys, produced_book, workspace):
    code = main(["--json", "--root", str(workspace), "next", "test-book"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["book_id"] == "test-book"


def test_a_flag_given_before_the_subcommand_is_not_lost(capsys, produced_book, workspace):
    """argparse subparsers overwrite parent defaults unless suppressed."""
    code = main(["--json", "status", "test-book", "--root", str(workspace)])
    assert code == 0
    assert json.loads(capsys.readouterr().out)["book_id"] == "test-book"
