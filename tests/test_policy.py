"""Choosing a production policy: required at `create`, switchable by the operator.

A book's autonomy is always the operator's explicit choice. `create` has no
default policy, and `policy set` records who changed it, when and why.
"""

from __future__ import annotations

import json

import pytest

from bookfactory.cli.main import main as cli
from bookfactory.core import api, production
from bookfactory.core.book import ASSET, Book
from bookfactory.core.errors import ValidationError


def _history(book_id, workspace, event):
    return api.audit_history(book_id, event=event, root=workspace)


# ----------------------------------------------------------------------
# create requires --policy
# ----------------------------------------------------------------------


def test_api_create_without_a_policy_is_refused(workspace):
    with pytest.raises(TypeError):
        api.create_book("Test Book", book_id="test-book", root=workspace)  # type: ignore[call-arg]
    for missing in (None, "", "  "):
        with pytest.raises(ValidationError, match="production policy is required"):
            api.create_book("Test Book", policy=missing, book_id="test-book", root=workspace)
    assert not (workspace / "books" / "test-book").exists()


def test_api_create_rejects_an_unknown_policy(workspace):
    with pytest.raises(ValidationError, match="Unknown production policy"):
        api.create_book("Test Book", policy="yolo", book_id="test-book", root=workspace)
    assert not (workspace / "books" / "test-book").exists()


def test_cli_create_without_policy_fails_with_a_clear_message(capsys, workspace):
    code = cli(["create", "Test Book", "--id", "test-book", "--root", str(workspace)])
    captured = capsys.readouterr()
    assert code != 0
    text = captured.out + captured.err
    assert "production policy is required" in text
    assert "visual_checkpoint is recommended" in text
    assert not (workspace / "books" / "test-book").exists()

    code = cli(["create", "Test Book", "--id", "test-book", "--root", str(workspace), "--json"])
    error = json.loads(capsys.readouterr().out)
    assert code != 0
    assert error["error"] == "ValidationError"


def test_cli_create_rejects_an_invalid_policy(capsys, workspace):
    with pytest.raises(SystemExit) as exc:
        cli(["create", "Test Book", "--policy", "yolo", "--root", str(workspace)])
    assert exc.value.code != 0
    assert "invalid choice" in capsys.readouterr().err


def test_create_help_recommends_visual_checkpoint(capsys):
    with pytest.raises(SystemExit):
        cli(["create", "--help"])
    out = capsys.readouterr().out
    assert "--policy" in out
    assert "recommended" in out
    for mode in ("visual_checkpoint", "checkpointed", "autonomous"):
        assert mode in out


@pytest.mark.parametrize("choice", ["checkpointed", "visual_checkpoint", "autonomous"])
def test_create_records_each_policy_explicitly(workspace, choice):
    code = cli(["create", "Test Book", "--id", "test-book", "--policy", choice,
                "--root", str(workspace)])
    assert code == 0
    policy = Book.load("test-book", workspace).state.production_policy
    expected = production.policy_from_choice(choice)
    assert policy.mode == choice
    assert policy.operator_authorized is expected.operator_authorized
    assert policy.visual_checkpoint is expected.visual_checkpoint
    assert policy.major_gate_checkpoints is expected.major_gate_checkpoints
    assert policy.source == "create_command"
    assert policy.authorized_at is not None

    recorded = _history("test-book", workspace, "production_policy_recorded")
    assert len(recorded) == 1
    assert recorded[0]["production_policy"] == choice
    assert recorded[0]["source"] == "create_command"


def test_a_book_on_disk_without_a_recorded_policy_still_loads_as_checkpointed(new_book, workspace):
    data = json.loads(new_book.paths.state_file.read_text(encoding="utf-8"))
    del data["production_policy"]
    new_book.paths.state_file.write_text(json.dumps(data), encoding="utf-8")
    policy = Book.load("test-book", workspace).state.production_policy
    assert policy.mode == "checkpointed"
    assert policy.source is None
    assert not production.is_autonomous(policy)


# ----------------------------------------------------------------------
# policy set
# ----------------------------------------------------------------------


def _awaiting_asset_approval(produced_book, workspace) -> str:
    """A produced (checkpointed) book whose next task is an artwork approval."""
    from tests.conftest import make_image

    book_id = produced_book.state.book_id
    api.revise(book_id, "fig-scope", kind=ASSET, root=workspace)
    art = make_image(workspace / "staging" / "fig-scope-v2.png", (1800, 1800), seed=3)
    api.submit_asset(book_id, "fig-scope", art, kind=ASSET, root=workspace)
    return book_id


def test_policy_set_switches_the_next_task_mode_immediately(produced_book, workspace, capsys):
    book_id = _awaiting_asset_approval(produced_book, workspace)
    task = api.next_task(book_id, root=workspace)
    assert task["type"] == "approval"
    assert task["mode"] == production.WAIT_FOR_OPERATOR

    code = cli(["policy", "set", book_id, "visual_checkpoint", "--by", "Operator",
                "--reason", "Fewer stops for this book", "--root", str(workspace), "--json"])
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["previous_mode"] == "checkpointed"
    assert result["production_policy"]["mode"] == "visual_checkpoint"
    assert result["mode"] == production.CONTINUE_AUTOMATICALLY

    task = api.next_task(book_id, root=workspace)
    assert task["type"] == "approval"
    assert task["mode"] == production.CONTINUE_AUTOMATICALLY

    policy = Book.load(book_id, workspace).state.production_policy
    assert policy.mode == "visual_checkpoint"
    assert policy.operator_authorized is True
    assert policy.source == "policy_set_command"
    assert policy.authorized_at is not None

    changes = _history(book_id, workspace, "production_policy_changed")
    assert len(changes) == 1
    change = changes[0]
    assert change["old_mode"] == "checkpointed"
    assert change["new_mode"] == "visual_checkpoint"
    assert change["by"] == "Operator"
    assert change["reason"] == "Fewer stops for this book"
    assert change["at"]


def test_policy_set_requires_by(new_book, workspace, capsys):
    with pytest.raises(SystemExit) as exc:
        cli(["policy", "set", "test-book", "autonomous", "--root", str(workspace)])
    assert exc.value.code != 0
    assert "--by" in capsys.readouterr().err
    for missing in ("", "   ", None):
        with pytest.raises(ValidationError, match="operator's name"):
            api.set_policy("test-book", "autonomous", by=missing, root=workspace)
    assert Book.load("test-book", workspace).state.production_policy.mode == "checkpointed"
    assert _history("test-book", workspace, "production_policy_changed") == []


def test_policy_set_rejects_an_invalid_mode(new_book, workspace, capsys):
    with pytest.raises(SystemExit):
        cli(["policy", "set", "test-book", "yolo", "--by", "Operator", "--root", str(workspace)])
    assert "invalid choice" in capsys.readouterr().err
    with pytest.raises(ValidationError, match="Unknown production policy"):
        api.set_policy("test-book", "yolo", by="Operator", root=workspace)
    assert Book.load("test-book", workspace).state.production_policy.mode == "checkpointed"


def test_policy_set_leaves_an_unanswered_intake_to_the_questionnaire(workspace):
    result = api.create_from_idea("A manual for men addicted to golf.", root=workspace)
    with pytest.raises(ValidationError, match="intake questionnaire"):
        api.set_policy(result["book_id"], "autonomous", by="Operator", root=workspace)


def test_policy_show_is_read_only(new_book, workspace, capsys):
    before = new_book.paths.state_file.read_bytes()
    code = cli(["policy", "show", "test-book", "--root", str(workspace), "--json"])
    assert code == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["production_policy"]["mode"] == "checkpointed"
    assert shown["production_policy"]["source"] == "create_command"
    assert "mode" in shown
    assert new_book.paths.state_file.read_bytes() == before


def test_switching_back_to_checkpointed_withdraws_autonomous_authority(produced_book, workspace):
    book_id = _awaiting_asset_approval(produced_book, workspace)
    with pytest.raises(ValidationError):
        api.approve(book_id, "fig-scope", kind=ASSET, autonomous=True, root=workspace)

    api.set_policy(book_id, "autonomous", by="Operator", root=workspace)
    api.set_policy(book_id, "checkpointed", by="Operator", reason="Want to see every page",
                   root=workspace)
    assert api.next_task(book_id, root=workspace)["mode"] == production.WAIT_FOR_OPERATOR
    with pytest.raises(ValidationError, match="does not authorize autonomous approval"):
        api.approve(book_id, "fig-scope", kind=ASSET, autonomous=True, root=workspace)
    code = cli(["approve", book_id, "fig-scope", "--kind", "asset", "--autonomous",
                "--root", str(workspace)])
    assert code != 0

    changes = _history(book_id, workspace, "production_policy_changed")
    assert [(c["old_mode"], c["new_mode"]) for c in changes] == [
        ("checkpointed", "autonomous"), ("autonomous", "checkpointed")]


def test_switching_back_to_checkpointed_refuses_an_autonomous_lock(workspace):
    from tests.conftest import BRIEF

    api.create_book("Test Book", policy="autonomous", book_id="test-book", root=workspace)
    book = Book.load("test-book", workspace)
    book.paths.brief_file.write_text(BRIEF, encoding="utf-8")
    book.save()

    api.set_policy("test-book", "checkpointed", by="Operator", root=workspace)
    code = cli(["lock", "concept", "test-book", "--autonomous", "--root", str(workspace)])
    assert code != 0
    with pytest.raises(ValidationError, match="does not authorize an autonomous concept lock"):
        api.lock("test-book", "concept", autonomous=True, root=workspace)
    assert not Book.load("test-book", workspace).state.concept.locked

    api.set_policy("test-book", "autonomous", by="Operator", root=workspace)
    api.lock("test-book", "concept", autonomous=True, root=workspace)
    assert Book.load("test-book", workspace).state.concept.locked
