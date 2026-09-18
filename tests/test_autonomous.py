"""Autonomous ChatGPT production mode: intake, production policy, the
continuation-mode contract, and the generative/deterministic reference split.
"""

from __future__ import annotations

import pytest

from bookfactory.core import api, production
from bookfactory.core.book import ASSET, Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.tasks import next_task

GOOD_ANSWERS = {
    "idea": "A fake rehabilitation manual for men addicted to golf.",
    "buyer": "His wife.",
    "recipient": "Dave, aged 52.",
    "recognition_trigger": "He irons his golf trousers before he irons his shirts.",
    "humour_level": "medium",
    "visual_feel": "classic_editorial_caricature",
    "colour_direction": "muted",
    "main_character": "user_description",
    "length": "80",
    "must_include": "the electric trolley",
    "must_avoid": "anything about his golf handicap",
    "production_policy": "autonomous",
}


# ----------------------------------------------------------------------
# Intake
# ----------------------------------------------------------------------


def test_a_book_started_from_an_idea_requires_the_questionnaire(workspace):
    result = api.create_from_idea("A rehabilitation manual for golf addicts.", root=workspace)
    book = Book.load(result["book_id"], workspace)
    assert book.state.intake.required is True
    assert book.state.intake.completed is False

    task = next_task(book)
    assert task.type == "intake"
    assert task.gate == "intake"
    assert task.mode == production.WAIT_FOR_OPERATOR


def test_a_book_created_the_old_way_never_needs_the_questionnaire(new_book):
    assert new_book.state.intake.required is False
    task = next_task(new_book)
    assert task.type != "intake"


def test_questionnaire_answers_are_persisted_and_never_asked_again(workspace):
    result = api.create_from_idea("A rehabilitation manual for golf addicts.", root=workspace)
    book_id = result["book_id"]

    api.submit_intake(book_id, GOOD_ANSWERS, root=workspace)

    book = Book.load(book_id, workspace)
    assert book.state.intake.completed is True
    assert book.state.intake.answers["idea"] == GOOD_ANSWERS["idea"]
    assert (book.paths.brief_dir / "intake.json").is_file()

    #: A fresh load must not ask again.
    fresh = Book.load(book_id, workspace)
    task = next_task(fresh)
    assert task.type != "intake"


def test_incomplete_answers_are_rejected_with_the_specific_problem(workspace):
    result = api.create_from_idea("A rehabilitation manual for golf addicts.", root=workspace)
    bad = dict(GOOD_ANSWERS)
    del bad["recognition_trigger"]
    with pytest.raises(ValidationError) as excinfo:
        api.submit_intake(result["book_id"], bad, root=workspace)
    assert any("recognition_trigger" in p for p in excinfo.value.problems)


# ----------------------------------------------------------------------
# Production policy
# ----------------------------------------------------------------------


def test_production_policy_is_derived_from_the_questionnaire_and_persisted(workspace):
    result = api.create_from_idea("A rehabilitation manual for golf addicts.", root=workspace)
    api.submit_intake(result["book_id"], GOOD_ANSWERS, root=workspace)

    book = Book.load(result["book_id"], workspace)
    policy = book.state.production_policy
    assert policy.mode == "autonomous"
    assert policy.operator_authorized is True
    assert policy.visual_checkpoint is False
    assert policy.major_gate_checkpoints is False
    assert policy.source == "intake_questionnaire"
    assert policy.authorized_at is not None


def test_checkpointed_policy_keeps_the_operator_in_the_loop(workspace):
    result = api.create_from_idea("A rehabilitation manual for golf addicts.", root=workspace)
    answers = dict(GOOD_ANSWERS, production_policy="checkpointed")
    api.submit_intake(result["book_id"], answers, root=workspace)

    book = Book.load(result["book_id"], workspace)
    policy = book.state.production_policy
    assert policy.mode == "checkpointed"
    assert policy.operator_authorized is False
    assert not production.is_autonomous(policy)


# ----------------------------------------------------------------------
# Continuation mode
# ----------------------------------------------------------------------


def _autonomous_book(locked_book, workspace):
    """A fully locked, planned book with autonomous authorization recorded."""
    book = Book.load(locked_book.state.book_id, workspace)
    book.state.intake.required = True
    book.state.intake.completed = True
    book.state.production_policy = production.policy_from_choice("autonomous")
    book.save()
    return Book.load(book.state.book_id, workspace)


def test_autonomous_mode_advances_approval_tasks_without_asking(locked_book, workspace, planned_book):
    book = _autonomous_book(planned_book, workspace)
    task = next_task(book)
    if task.type == "approval":
        assert task.mode == production.CONTINUE_AUTOMATICALLY
    else:
        #: Whatever it is, plain production work is never held for a human.
        assert task.mode in (production.CONTINUE_AUTOMATICALLY, production.REMEDIATE)


def test_checkpointed_mode_still_waits_for_the_operator_on_an_approval(produced_book, workspace):
    from tests.conftest import make_image

    api.revise(produced_book.state.book_id, "fig-scope", kind="asset", root=workspace)
    art = make_image(workspace / "staging" / "fig-scope-v2.png", (1800, 1800), seed=3)
    api.submit_asset(produced_book.state.book_id, "fig-scope", art, kind=ASSET, root=workspace)

    book = Book.load(produced_book.state.book_id, workspace)
    task = next_task(book)
    assert task.type == "approval"
    assert task.mode == production.WAIT_FOR_OPERATOR


def test_a_hard_constraint_failure_produces_remediation_not_an_approval(produced_book, workspace):
    from tests.conftest import make_image

    api.revise(produced_book.state.book_id, "fig-scope", kind="asset", root=workspace)
    too_small = make_image(workspace / "staging" / "fig-scope-tiny.png", (300, 300), seed=4)
    api.submit_asset(produced_book.state.book_id, "fig-scope", too_small, kind=ASSET, root=workspace)

    book = Book.load(produced_book.state.book_id, workspace)
    task = next_task(book)
    assert task.type == "illustration"
    assert task.remediation is True
    assert task.mode == production.REMEDIATE


def test_repeated_failures_stop_for_the_operator_instead_of_looping_forever(produced_book, workspace):
    from tests.conftest import make_image

    book_id = produced_book.state.book_id
    api.revise(book_id, "fig-scope", kind="asset", root=workspace)
    for i in range(production.RETRY_LIMIT):
        bad = make_image(workspace / "staging" / f"fig-scope-bad-{i}.png", (300, 300), seed=10 + i)
        api.submit_asset(book_id, "fig-scope", bad, kind=ASSET, root=workspace)

    book = Book.load(book_id, workspace)
    task = next_task(book)
    assert task.remediation is True
    assert task.retry_count >= production.RETRY_LIMIT
    assert task.mode == production.WAIT_FOR_OPERATOR


def test_a_blocked_book_always_reports_blocked(produced_book, workspace):
    api.block(produced_book.state.book_id, "IP concern with no clearly safe resolution", root=workspace)
    book = Book.load(produced_book.state.book_id, workspace)
    task = next_task(book)
    assert task.mode == production.BLOCKED


def test_a_finished_book_reports_complete(produced_book, workspace):
    #: `next_task` returning None is itself the completion signal; verify the
    #: continuation-mode function agrees, independent of whether this
    #: particular fixture book (four pages) is large enough for KDP.
    book = Book.load(produced_book.state.book_id, workspace)
    assert production.compute_mode(book, None) == production.COMPLETE


# ----------------------------------------------------------------------
# Autonomous approval authorization
# ----------------------------------------------------------------------


def test_autonomous_approval_requires_a_recorded_authorization(planned_book, workspace):
    from tests.conftest import make_image

    api.render(planned_book.state.book_id, page_id="p001", submit=True, root=workspace)
    with pytest.raises(ValidationError):
        api.approve(planned_book.state.book_id, "p001", root=workspace, autonomous=True)


def test_autonomous_approval_is_recorded_in_the_audit_trail(planned_book, workspace):
    book_id = planned_book.state.book_id
    book = Book.load(book_id, workspace)
    book.state.production_policy = production.policy_from_choice("autonomous")
    book.save()

    api.render(book_id, page_id="p001", submit=True, root=workspace)
    result = api.approve(book_id, "p001", root=workspace, autonomous=True)
    assert result["authorization"] == "autonomous_production_policy:autonomous"

    history = api.audit_history(book_id, event="approved", root=workspace)
    assert history[-1]["authorization"] == "autonomous_production_policy:autonomous"


# ----------------------------------------------------------------------
# Generative vs deterministic references
# ----------------------------------------------------------------------


def test_deterministic_fixtures_never_reach_a_generative_task(planned_book, workspace):
    from tests.conftest import make_image

    book_id = planned_book.state.book_id
    api.register_asset(book_id, "ref-fixture", root=workspace, kind="layout_reference",
                       title="Renderer geometry fixture", reference_role="deterministic_layout")
    fixture_art = make_image(workspace / "staging" / "ref-fixture.png", (1800, 1800), seed=5)
    api.submit_asset(book_id, "ref-fixture", fixture_art, kind=ASSET, root=workspace)
    api.approve(book_id, "ref-fixture", kind=ASSET, root=workspace, by="tester")

    api.register_asset(book_id, "ref-style", root=workspace, kind="layout_reference",
                       title="Real style example")
    style_art = make_image(workspace / "staging" / "ref-style.png", (1800, 1800), seed=6)
    api.submit_asset(book_id, "ref-style", style_art, kind=ASSET, root=workspace)
    api.approve(book_id, "ref-style", kind=ASSET, root=workspace, by="tester")

    book = Book.load(book_id, workspace)
    paths = book.reference_paths(["ref-fixture", "ref-style"], generative_only=True)
    assert not any("ref-fixture" in p for p in paths)
    assert any("ref-style" in p for p in paths)

    #: Without the filter, both are legitimately retrievable - the guarantee is
    #: specific to generative tasks, not a blanket ban on reading the file.
    unfiltered = book.reference_paths(["ref-fixture", "ref-style"])
    assert any("ref-fixture" in p for p in unfiltered)


def test_reference_role_rejects_unknown_values(planned_book, workspace):
    with pytest.raises(ValidationError):
        api.register_asset(planned_book.state.book_id, "ref-bad", root=workspace,
                           kind="layout_reference", reference_role="not-a-real-role")


# ----------------------------------------------------------------------
# Fresh-session resumability
# ----------------------------------------------------------------------


def test_a_fresh_load_after_intake_resumes_without_asking_again(workspace):
    result = api.create_from_idea("A rehabilitation manual for golf addicts.", root=workspace)
    api.submit_intake(result["book_id"], GOOD_ANSWERS, root=workspace)

    #: Simulate a brand new session: nothing but Book.load.
    fresh = Book.load(result["book_id"], workspace)
    assert fresh.state.production_policy.mode == "autonomous"
    task = next_task(fresh)
    assert task.type == "authoring"
    assert "brief" in task.summary.lower()


# ----------------------------------------------------------------------
# Existing immutability guarantees are untouched
# ----------------------------------------------------------------------


def test_approved_work_is_still_immutable_under_the_new_fields(planned_book, workspace):
    from bookfactory.core.errors import ImmutableAssetError
    from tests.conftest import make_image

    art = make_image(workspace / "staging" / "fig-scope-again.png", (1800, 1800), seed=7)
    with pytest.raises(ImmutableAssetError):
        api.submit_asset(planned_book.state.book_id, "fig-scope", art, kind=ASSET, root=workspace)
