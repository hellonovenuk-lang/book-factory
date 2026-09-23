"""One-prompt start: the agent drafts the intake answers, the operator confirms.

See `PLAN.md`, "Phase 9: One-prompt start", for the contract these tests check.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bookfactory.cli.main import main
from bookfactory.core import api
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.tasks import next_task

IDEA = "A fake rehabilitation manual for men addicted to golf."

#: What an agent can reasonably guess from IDEA alone. The colour direction
#: is left unclear, and the production policy is never drafted.
DRAFT = {
    "idea": IDEA,
    "buyer": "His partner.",
    "recipient": "The golf addict himself.",
    "recognition_trigger": "He irons his golf trousers before his work shirts.",
    "humour_level": "medium",
    "visual_feel": "classic_editorial_caricature",
    "main_character": "book_factory_invents",
    "length": "80",
    "must_include": "none",
    "must_avoid": "none",
}


def _start(workspace: Path) -> str:
    return api.create_from_idea(IDEA, root=workspace, book_id="golf")["book_id"]


def _draft(workspace: Path, book_id: str, **overrides) -> dict:
    answers = dict(DRAFT, **overrides)
    return api.draft_intake(book_id, answers, by="chatgpt", unclear=["colour_direction"],
                            root=workspace)


def test_one_sentence_to_confirmed_intake(workspace: Path) -> None:
    book_id = _start(workspace)
    result = _draft(workspace, book_id)
    assert result["still_to_ask"] == ["colour_direction", "production_policy"]

    api.confirm_intake(book_id, by="Kieran", policy="visual_checkpoint",
                       changes={"colour_direction": "colourful", "length": "60"},
                       root=workspace)

    book = Book.load(book_id, workspace)
    assert book.state.intake.completed is True
    assert book.state.intake.draft is None
    assert book.state.intake.answers["colour_direction"] == "colourful"
    assert book.state.intake.answers["length"] == "60"
    assert book.state.intake.answers["buyer"] == "His partner."
    assert book.state.intake.drafted_by == "chatgpt"
    assert book.state.intake.confirmed_by == "Kieran"
    assert book.state.intake.changed_on_confirm == ["colour_direction", "length"]
    assert book.state.production_policy.mode == "visual_checkpoint"
    assert book.state.production_policy.source == "intake_questionnaire"

    record = json.loads((book.paths.brief_dir / "intake.json").read_text())
    assert record["confirmed_by"] == "Kieran"
    assert not (book.paths.brief_dir / "intake-draft.json").exists()
    task = next_task(book)
    assert task is not None and task.type != "intake"

    submitted = api.audit_history(book_id, root=workspace, event="intake_submitted")
    assert submitted[-1]["drafted_by"] == "chatgpt"
    assert submitted[-1]["confirmed_by"] == "Kieran"


def test_a_draft_never_completes_intake(workspace: Path) -> None:
    book_id = _start(workspace)
    _draft(workspace, book_id)

    book = Book.load(book_id, workspace)
    assert book.state.intake.completed is False
    assert (book.paths.brief_dir / "intake-draft.json").is_file()
    task = next_task(book)
    assert task.type == "intake"
    assert task.mode == "wait_for_operator"
    assert "colour_direction" in task.instructions
    assert "--confirm" in task.instructions
    assert api.status(book_id, root=workspace)["intake"]["draft_waiting"] is True


def test_a_draft_can_never_contain_the_production_policy(workspace: Path) -> None:
    book_id = _start(workspace)
    with pytest.raises(ValidationError) as caught:
        _draft(workspace, book_id, production_policy="autonomous")
    assert any("production_policy" in problem for problem in caught.value.problems)
    assert Book.load(book_id, workspace).state.intake.draft is None


def test_a_draft_must_answer_or_flag_every_question(workspace: Path) -> None:
    book_id = _start(workspace)
    answers = dict(DRAFT)
    del answers["buyer"]
    with pytest.raises(ValidationError) as caught:
        api.draft_intake(book_id, answers, by="chatgpt", unclear=["colour_direction"],
                         root=workspace)
    assert any("'buyer'" in problem for problem in caught.value.problems)


def test_a_draft_answer_must_be_a_valid_choice(workspace: Path) -> None:
    book_id = _start(workspace)
    with pytest.raises(ValidationError) as caught:
        _draft(workspace, book_id, humour_level="very rude")
    assert any("humour_level" in problem for problem in caught.value.problems)


def test_confirm_needs_every_unclear_answer(workspace: Path) -> None:
    book_id = _start(workspace)
    _draft(workspace, book_id)
    with pytest.raises(ValidationError) as caught:
        api.confirm_intake(book_id, by="Kieran", policy="visual_checkpoint", root=workspace)
    assert caught.value.problems == ["'colour_direction' is still unclear"]
    assert Book.load(book_id, workspace).state.intake.completed is False


def test_the_policy_cannot_arrive_as_a_correction(workspace: Path) -> None:
    book_id = _start(workspace)
    _draft(workspace, book_id)
    with pytest.raises(ValidationError):
        api.confirm_intake(book_id, by="Kieran", policy="checkpointed",
                           changes={"colour_direction": "muted",
                                    "production_policy": "autonomous"},
                           root=workspace)


def test_confirm_without_a_draft_is_refused(workspace: Path) -> None:
    book_id = _start(workspace)
    with pytest.raises(ValidationError, match="no drafted intake"):
        api.confirm_intake(book_id, by="Kieran", policy="checkpointed", root=workspace)


def test_nothing_can_be_drafted_once_intake_is_complete(workspace: Path) -> None:
    book_id = _start(workspace)
    _draft(workspace, book_id)
    api.confirm_intake(book_id, by="Kieran", policy="checkpointed",
                       changes={"colour_direction": "muted"}, root=workspace)
    with pytest.raises(ValidationError, match="already complete"):
        _draft(workspace, book_id)


def test_cli_draft_then_confirm(workspace: Path, tmp_path: Path, capsys) -> None:
    book_id = _start(workspace)
    draft_file = tmp_path / "draft.json"
    draft_file.write_text(json.dumps(dict(DRAFT, unclear=["colour_direction"])),
                          encoding="utf-8")

    assert main(["intake", book_id, "--draft", "--by", "chatgpt",
                 "--from-file", str(draft_file), "--root", str(workspace), "--json"]) == 0
    drafted = json.loads(capsys.readouterr().out)
    assert drafted["draft"]["unclear"] == ["colour_direction"]

    assert main(["intake", book_id, "--confirm", "--by", "Kieran",
                 "--policy", "visual_checkpoint", "--set", "colour_direction=muted",
                 "--root", str(workspace), "--json"]) == 0
    capsys.readouterr()
    assert Book.load(book_id, workspace).state.intake.completed is True


def test_cli_draft_accepts_nested_answers(workspace: Path, tmp_path: Path, capsys) -> None:
    book_id = _start(workspace)
    draft_file = tmp_path / "draft.json"
    draft_file.write_text(json.dumps({"answers": DRAFT, "unclear": ["colour_direction"]}),
                          encoding="utf-8")
    assert main(["intake", book_id, "--draft", "--by", "chatgpt",
                 "--from-file", str(draft_file), "--root", str(workspace), "--json"]) == 0
    capsys.readouterr()
    draft = Book.load(book_id, workspace).state.intake.draft
    assert draft["answers"]["buyer"] == DRAFT["buyer"]
    assert draft["unclear"] == ["colour_direction"]


def test_cli_confirm_needs_the_operator_and_the_policy(workspace: Path) -> None:
    book_id = _start(workspace)
    _draft(workspace, book_id)
    assert main(["intake", book_id, "--confirm", "--by", "Kieran",
                 "--root", str(workspace)]) == 2
    assert Book.load(book_id, workspace).state.intake.completed is False
