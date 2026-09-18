"""Hard constraints on submitted artwork.

The scenario throughout is the one the cross-agent smoke test hit: artwork came
back too small to print, and the system offered it for approval anyway.
"""

from __future__ import annotations

import json

import pytest

from bookfactory.core import api, constraints
from bookfactory.core.book import ASSET, PAGE, Book
from bookfactory.core.errors import HardConstraintViolation
from tests.conftest import make_image


def _undersized(workspace, width=1254, height=1254):
    """The size ChatGPT actually returned during the smoke test."""
    return make_image(workspace / "staging" / f"small-{width}x{height}.png",
                      (width, height), seed=41)


def _submit_undersized(workspace):
    api.revise("test-book", "fig-scope", kind=ASSET, reason="Composition", root=workspace)
    return api.submit_asset("test-book", "fig-scope", _undersized(workspace),
                            kind=ASSET, root=workspace, source="chatgpt-image")


# ----------------------------------------------------------------------
# What the task promises is what gets measured
# ----------------------------------------------------------------------


def test_the_task_publishes_the_constraint_that_will_be_enforced(produced_book, workspace):
    api.revise("test-book", "fig-scope", kind=ASSET, root=workspace)
    task = api.next_task("test-book", root=workspace)
    book = Book.load("test-book", workspace)
    asset = book.registry.get("fig-scope")
    assert task["constraints"]["min_pixels"] == book.asset_constraints(asset)["min_pixels"]


def test_min_pixels_follows_the_placement_on_the_page(produced_book, workspace):
    """A spot illustration prints small, so it needs fewer pixels. Holding it to
    the full-page bar would reject usable artwork."""
    book = Book.load("test-book", workspace)
    asset = book.registry.get("fig-scope")
    full_page = constraints.expected_constraints(book, asset, placement="full_page")
    spot = constraints.expected_constraints(book, asset, placement="spot")
    assert full_page["min_pixels"] == 1530
    assert spot["min_pixels"] == 630
    assert spot["min_pixels"] < full_page["min_pixels"]


def test_the_threshold_matches_what_visual_qa_will_later_enforce(produced_book, workspace):
    from bookfactory.qa.visual import PLACEMENT_COVERAGE

    assert PLACEMENT_COVERAGE is constraints.PLACEMENT_COVERAGE


# ----------------------------------------------------------------------
# Submission
# ----------------------------------------------------------------------


def test_a_failing_draft_is_still_registered_and_kept(produced_book, workspace):
    draft = _submit_undersized(workspace)
    assert draft["revision"] == "v2"

    book = Book.load("test-book", workspace)
    record = book.registry.get("fig-scope").draft("v2")
    assert record is not None
    assert record.status == "draft"
    assert book.paths.resolve(record.path).is_file(), "a failed draft is evidence, not rubbish"


def test_the_failure_is_recorded_explicitly_with_expected_and_actual(produced_book, workspace):
    draft = _submit_undersized(workspace)
    failures = draft["constraint_failures"]
    assert len(failures) == 1
    failure = failures[0]
    assert failure["constraint"] == "min_pixels"
    assert failure["expected"] == 1530
    assert failure["actual"] == 1254
    assert "1254" in failure["message"] and "1530" in failure["message"]
    assert failure["remedy"]


def test_a_conforming_draft_records_no_failures(produced_book, workspace):
    api.revise("test-book", "fig-scope", kind=ASSET, root=workspace)
    art = make_image(workspace / "staging" / "big.png", (1800, 1350), seed=42)
    draft = api.submit_asset("test-book", "fig-scope", art, kind=ASSET, root=workspace)
    assert draft["constraint_failures"] == []


def test_an_unreadable_image_is_caught_generically(produced_book, workspace):
    """min_pixels is not special-cased; the registry drives the checks."""
    api.revise("test-book", "fig-scope", kind=ASSET, root=workspace)
    broken = workspace / "staging" / "broken.png"
    broken.parent.mkdir(parents=True, exist_ok=True)
    broken.write_bytes(b"this is not a PNG")
    draft = api.submit_asset("test-book", "fig-scope", broken, kind=ASSET, root=workspace)
    assert [f["constraint"] for f in draft["constraint_failures"]] == ["readable_image"]


def test_every_hard_check_is_published_as_a_constraint(produced_book, workspace):
    """A hard check nobody is told about is a trap."""
    book = Book.load("test-book", workspace)
    published = book.asset_constraints(book.registry.get("fig-scope"))
    assert set(constraints.HARD_CHECKS) <= set(published)


# ----------------------------------------------------------------------
# `next` routes a failure to remediation, not to review
# ----------------------------------------------------------------------


def test_next_does_not_offer_a_failing_draft_for_approval(produced_book, workspace):
    _submit_undersized(workspace)
    task = api.next_task("test-book", root=workspace)
    assert task["type"] != "approval", "a draft that cannot be used must never reach review"
    assert task["type"] == "illustration"


def test_the_remediation_task_states_the_exact_failure(produced_book, workspace):
    _submit_undersized(workspace)
    task = api.next_task("test-book", root=workspace)
    assert "failed a hard constraint" in task["summary"]
    assert "min_pixels" in task["instructions"]
    assert "1254" in task["instructions"] and "1530" in task["instructions"]
    assert "do not overwrite it" in task["instructions"]
    assert task["asset_id"] == "fig-scope"
    assert task["output"]["destination"] == "assets/drafts/fig-scope/"


def test_a_conforming_draft_still_reaches_approval(produced_book, workspace):
    api.revise("test-book", "fig-scope", kind=ASSET, root=workspace)
    art = make_image(workspace / "staging" / "good.png", (1800, 1350), seed=43)
    api.submit_asset("test-book", "fig-scope", art, kind=ASSET, root=workspace)
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "approval"
    assert task["asset_id"] == "fig-scope"


def test_soft_constraints_never_block_approval(produced_book, workspace):
    """Style and character judgements are the operator's, not the system's."""
    book = Book.load("test-book", workspace)
    published = book.asset_constraints(book.registry.get("fig-scope"))
    soft = {"maintain_style", "maintain_character_identity", "colour", "embedded_text"}
    assert soft.isdisjoint(set(constraints.HARD_CHECKS))

    api.revise("test-book", "fig-scope", kind=ASSET, root=workspace)
    art = make_image(workspace / "staging" / "soft.png", (1800, 1350), seed=44)
    api.submit_asset("test-book", "fig-scope", art, kind=ASSET, root=workspace)
    approval = api.approve("test-book", "fig-scope", kind=ASSET, root=workspace, by="operator")
    assert approval["revision"] == "v2"


def test_a_corrected_resubmission_clears_the_way(produced_book, workspace):
    _submit_undersized(workspace)
    api.reject("test-book", "fig-scope", kind=ASSET, revision="v2",
               reason="Too small", root=workspace)
    art = make_image(workspace / "staging" / "fixed.png", (1800, 1350), seed=45)
    api.submit_asset("test-book", "fig-scope", art, kind=ASSET, root=workspace)
    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "approval"
    assert api.approve("test-book", "fig-scope", kind=ASSET,
                       root=workspace)["revision"] == "v3"


# ----------------------------------------------------------------------
# Approval refuses independently
# ----------------------------------------------------------------------


def test_approve_refuses_a_draft_that_failed_a_hard_constraint(produced_book, workspace):
    _submit_undersized(workspace)
    with pytest.raises(HardConstraintViolation) as excinfo:
        api.approve("test-book", "fig-scope", kind=ASSET, revision="v2", root=workspace)
    assert "min_pixels" in excinfo.value.message
    assert excinfo.value.failures[0]["actual"] == 1254
    assert "Submit a corrected draft" in excinfo.value.remedy
    assert excinfo.value.exit_code == 12


def test_approve_remeasures_the_file_rather_than_trusting_the_registry(
        produced_book, workspace):
    """"Even if state is somehow inconsistent" - a hand-cleared verdict must not
    talk an unusable file through the gate."""
    _submit_undersized(workspace)

    book = Book.load("test-book", workspace)
    book.registry.get("fig-scope").draft("v2").constraint_failures = []
    book.save()
    stored = json.loads(book.paths.asset_registry.read_text())
    asset = next(a for a in stored["assets"] if a["asset_id"] == "fig-scope")
    assert next(d for d in asset["drafts"] if d["revision"] == "v2")["constraint_failures"] == []

    with pytest.raises(HardConstraintViolation):
        api.approve("test-book", "fig-scope", kind=ASSET, revision="v2", root=workspace)


def test_a_refused_approval_leaves_the_approved_version_untouched(produced_book, workspace):
    before = Book.load("test-book", workspace).registry.get("fig-scope").approved.sha256
    _submit_undersized(workspace)
    with pytest.raises(HardConstraintViolation):
        api.approve("test-book", "fig-scope", kind=ASSET, revision="v2", root=workspace)

    book = Book.load("test-book", workspace)
    asset = book.registry.get("fig-scope")
    assert asset.approved.revision == "v1"
    assert asset.approved.sha256 == before
    assert book.verify_approved() == []


def test_the_cli_reports_the_refusal_as_structured_json(capsys, produced_book, workspace):
    from bookfactory.cli.main import main

    _submit_undersized(workspace)
    capsys.readouterr()
    code = main(["approve", "test-book", "fig-scope", "--kind", "asset",
                 "--root", str(workspace), "--json"])
    assert code == 12
    data = json.loads(capsys.readouterr().out)
    assert data["error"] == "HardConstraintViolation"
    assert data["constraint_failures"][0]["constraint"] == "min_pixels"
    assert data["remedy"]


def test_page_drafts_are_unaffected(produced_book, workspace):
    """Pages come from our own renderer, which already refuses to emit a bad page."""
    book = Book.load("test-book", workspace)
    for page in book.manifest:
        for draft in page.drafts:
            assert draft.constraint_failures == []
