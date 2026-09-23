"""`bookfactory approve --all-passing`: batch approval of every ready draft.

See PLAN.md "Phase 7: Batch approval" for the contract this implements.
"""

from __future__ import annotations

import pytest

from bookfactory.core import api, production
from bookfactory.core.book import ASSET, PAGE, Book
from bookfactory.core.errors import ValidationError
from tests.conftest import make_image


def _new_asset(workspace, book_id, asset_id, *, kind="illustration", seed=20, size=(1800, 1350)):
    api.register_asset(book_id, asset_id, root=workspace, kind=kind, title=asset_id)
    art = make_image(workspace / "staging" / f"{asset_id}.png", size, seed=seed)
    return api.submit_asset(book_id, asset_id, art, kind=ASSET, root=workspace)


def test_approves_every_passing_page_and_asset_draft_in_one_call(planned_book, workspace):
    book_id = "test-book"
    api.render(book_id, page_id="p001", submit=True, root=workspace)
    api.render(book_id, page_id="p002", submit=True, root=workspace)
    _new_asset(workspace, book_id, "fig-extra", seed=21)

    result = api.approve_passing(book_id, by="operator", root=workspace)

    assert not result["failed"]
    approved_ids = {(e["kind"], e["id"]) for e in result["approved"]}
    assert (PAGE, "p001") in approved_ids
    assert (PAGE, "p002") in approved_ids
    assert (ASSET, "fig-extra") in approved_ids

    book = Book.load(book_id, workspace)
    for kind, identifier in approved_ids:
        record = book.registry.get(identifier) if kind == ASSET else book.manifest.get(identifier)
        assert record.is_approved
        assert record.approved.approved_by == "operator"
        assert book.paths.resolve(record.approved.path).is_file()


def test_dry_run_approves_nothing_and_lists_candidates(planned_book, workspace):
    book_id = "test-book"
    api.render(book_id, page_id="p001", submit=True, root=workspace)

    result = api.approve_passing(book_id, by="operator", dry_run=True, root=workspace)

    assert result["dry_run"] is True
    assert result["approved"] == []
    assert any(e["id"] == "p001" for e in result["would_approve"])

    book = Book.load(book_id, workspace)
    assert not book.manifest.get("p001").is_approved


def test_a_draft_that_fails_min_pixels_is_not_approved_while_others_are(produced_book, workspace):
    book_id = "test-book"
    api.revise(book_id, "fig-scope", kind=ASSET, root=workspace)
    too_small = make_image(workspace / "staging" / "fig-scope-tiny.png", (300, 300), seed=4)
    api.submit_asset(book_id, "fig-scope", too_small, kind=ASSET, root=workspace)

    _new_asset(workspace, book_id, "fig-extra", seed=22)

    result = api.approve_passing(book_id, by="operator", root=workspace)

    assert not result["failed"]
    assert any(e["id"] == "fig-scope" for e in result["not_ready"])
    assert any(e["id"] == "fig-extra" for e in [{"id": a["id"]} for a in result["approved"]])

    book = Book.load(book_id, workspace)
    fig_scope = book.registry.get("fig-scope")
    assert fig_scope.revision_open is True, "still open: the replacement never passed"
    assert book.registry.get("fig-extra").is_approved


def test_already_approved_items_are_left_alone(produced_book, workspace):
    book_id = "test-book"
    before = Book.load(book_id, workspace).manifest.get("p001").approved.sha256

    result = api.approve_passing(book_id, by="operator", root=workspace)

    assert not any(e["id"] == "p001" for e in result["approved"])
    after = Book.load(book_id, workspace).manifest.get("p001").approved.sha256
    assert after == before


def test_an_open_revision_with_a_new_passing_draft_is_included(produced_book, workspace):
    book_id = "test-book"
    api.revise(book_id, "p001", kind=PAGE, root=workspace)
    api.render(book_id, page_id="p001", submit=True, root=workspace)

    result = api.approve_passing(book_id, by="operator", root=workspace)

    assert any(e["id"] == "p001" and e["revision"] == "v2" for e in result["approved"])
    book = Book.load(book_id, workspace)
    assert book.manifest.get("p001").revision_open is False
    assert book.manifest.get("p001").approved.revision == "v2"


def test_cover_front_artwork_is_never_included(planned_book, workspace):
    from bookfactory.core import cover

    book_id = "test-book"
    book = Book.load(book_id, workspace)
    book.register_asset(cover.ART_ID, kind="cover_artwork")
    book.save()
    art = make_image(workspace / "staging" / "cover-art.png", (3000, 4500), seed=30)
    api.submit_asset(book_id, cover.ART_ID, art, kind=ASSET, root=workspace)

    result = api.approve_passing(book_id, by="operator", root=workspace)

    assert not any(e["id"] == cover.ART_ID for e in result["approved"])
    assert not any(e["id"] == cover.ART_ID for e in result["not_ready"])
    book = Book.load(book_id, workspace)
    assert not book.registry.get(cover.ART_ID).is_approved


def test_autonomous_refused_on_a_checkpointed_book(planned_book, workspace):
    book_id = "test-book"
    api.render(book_id, page_id="p001", submit=True, root=workspace)

    with pytest.raises(ValidationError):
        api.approve_passing(book_id, by="operator", autonomous=True, root=workspace)

    book = Book.load(book_id, workspace)
    assert not book.manifest.get("p001").is_approved


def test_autonomous_allowed_and_recorded_where_policy_authorizes(planned_book, workspace):
    book_id = "test-book"
    book = Book.load(book_id, workspace)
    book.state.production_policy = production.policy_from_choice("autonomous")
    book.save()

    api.render(book_id, page_id="p001", submit=True, root=workspace)

    result = api.approve_passing(book_id, by="agent", autonomous=True, root=workspace)

    assert any(e["id"] == "p001" for e in result["approved"])
    book = Book.load(book_id, workspace)
    approval = book.manifest.get("p001").approved
    assert approval.authorization == "autonomous_production_policy:autonomous"


def test_missing_by_is_refused(planned_book, workspace):
    with pytest.raises(ValidationError):
        api.approve_passing("test-book", by=None, root=workspace)
    with pytest.raises(ValidationError):
        api.approve_passing("test-book", by="   ", root=workspace)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def test_cli_all_passing_approves_and_exits_zero(planned_book, workspace):
    from bookfactory.cli.main import main as cli

    api.render("test-book", page_id="p001", submit=True, root=workspace)
    assert cli(["approve", "test-book", "--all-passing", "--by", "operator",
               "--root", str(workspace)]) == 0
    assert Book.load("test-book", workspace).manifest.get("p001").is_approved


def test_cli_id_and_all_passing_together_is_an_error(planned_book, workspace):
    from bookfactory.cli.main import main as cli

    assert cli(["approve", "test-book", "p001", "--all-passing", "--by", "operator",
               "--root", str(workspace)]) != 0


def test_cli_single_approve_still_works(planned_book, workspace):
    from bookfactory.cli.main import main as cli

    api.render("test-book", page_id="p001", submit=True, root=workspace)
    assert cli(["approve", "test-book", "p001", "--by", "operator",
               "--root", str(workspace)]) == 0
    assert Book.load("test-book", workspace).manifest.get("p001").is_approved
