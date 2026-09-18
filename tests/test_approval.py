"""Drafts, approvals, immutability and revisions.

These are the tests that matter most: every failure they describe actually
happened during the golf project.
"""

from __future__ import annotations

import os
import stat

import pytest

from bookfactory.core import api, checksums
from bookfactory.core.book import ASSET, PAGE, Book
from bookfactory.core.errors import ChecksumMismatch, ImmutableAssetError, ValidationError
from tests.conftest import make_image


def _submit(workspace, book_id="test-book", asset_id="fig-extra", seed=3):
    art = make_image(workspace / "staging" / f"{asset_id}-{seed}.png", (1800, 1350), seed=seed)
    return api.submit_asset(book_id, asset_id, art, kind=ASSET, root=workspace)


def test_submit_records_a_checksummed_draft(locked_book, workspace):
    api.register_asset("test-book", "fig-extra", root=workspace, kind="illustration")
    draft = _submit(workspace)
    assert draft["revision"] == "v1"
    assert len(draft["sha256"]) == 64
    path = locked_book.paths.resolve(draft["path"])
    assert path.is_file()
    assert checksums.sha256_file(path) == draft["sha256"]


def test_draft_revisions_increment_and_are_never_overwritten(locked_book, workspace):
    api.register_asset("test-book", "fig-extra", root=workspace, kind="illustration")
    first = _submit(workspace, seed=1)
    second = _submit(workspace, seed=2)
    third = _submit(workspace, seed=3)
    assert [first["revision"], second["revision"], third["revision"]] == ["v1", "v2", "v3"]
    book = Book.load("test-book", workspace)
    for draft in book.registry.get("fig-extra").drafts:
        assert book.paths.resolve(draft.path).is_file()


def test_approval_promotes_the_named_draft_and_locks_it(planned_book, workspace):
    api.render("test-book", page_id="p001", submit=True, root=workspace)
    approval = api.approve("test-book", "p001", kind=PAGE, root=workspace, by="operator")

    book = Book.load("test-book", workspace)
    page = book.manifest.get("p001")
    assert page.status == "approved"
    assert page.approved.approved_by == "operator"
    assert page.approved.path.startswith("pages/approved/")

    path = book.paths.resolve(approval["path"])
    assert checksums.sha256_file(path) == approval["sha256"]
    assert checksums.is_immutable(path), "approved artefacts must be read-only"


def test_approved_artefact_cannot_be_overwritten_by_a_new_submission(produced_book, workspace):
    """Submitting over approved work is the exact failure that destroyed artwork."""
    art = make_image(workspace / "staging" / "replacement.png", (1800, 1350), seed=7)
    with pytest.raises(ImmutableAssetError) as excinfo:
        api.submit_asset("test-book", "p001", art, kind=PAGE, root=workspace)
    assert "revise" in excinfo.value.remedy


def test_approving_twice_without_a_revision_is_refused(produced_book, workspace):
    with pytest.raises(ImmutableAssetError):
        api.approve("test-book", "p001", kind=PAGE, root=workspace)


def test_approved_file_is_write_protected_on_disk(produced_book):
    """Layer one of immutability: the OS refuses the write.

    Root ignores permission bits, which is exactly why this is only layer one -
    the checksum in the manifest is what actually guarantees the artefact, and
    the tampering test below is the one that must never be weakened.
    """
    path = produced_book.paths.resolve(produced_book.manifest.get("p001").approved.path)
    assert not os.stat(path).st_mode & stat.S_IWUSR

    if os.geteuid() == 0:
        pytest.skip("running as root; permission bits do not stop root writes")
    with pytest.raises(PermissionError):
        path.write_bytes(b"clobbered")


def test_tampering_with_an_approved_file_is_detected(produced_book, workspace):
    page = produced_book.manifest.get("p001")
    path = produced_book.paths.resolve(page.approved.path)
    os.chmod(path, 0o644)
    path.write_bytes(b"%PDF-1.4 not the approved page")

    problems = Book.load("test-book", workspace).verify_approved()
    assert any("checksum mismatch" in problem for problem in problems)

    result = api.validate("test-book", root=workspace)
    assert result["ok"] is False


def test_checksum_verify_raises_with_both_hashes(produced_book):
    page = produced_book.manifest.get("p001")
    path = produced_book.paths.resolve(page.approved.path)
    os.chmod(path, 0o644)
    path.write_bytes(b"different")
    with pytest.raises(ChecksumMismatch) as excinfo:
        checksums.verify(path, page.approved.sha256)
    assert page.approved.sha256 in str(excinfo.value)


def test_relock_restores_permissions_after_a_git_checkout(produced_book, workspace):
    path = produced_book.paths.resolve(produced_book.manifest.get("p001").approved.path)
    os.chmod(path, 0o644)
    result = api.relock("test-book", root=workspace)
    assert result["relocked"] == 1
    assert checksums.is_immutable(path)


def test_rejected_drafts_are_kept_not_deleted(locked_book, workspace):
    api.register_asset("test-book", "fig-extra", root=workspace, kind="illustration")
    draft = _submit(workspace, seed=5)
    api.reject("test-book", "fig-extra", kind=ASSET, revision=draft["revision"],
               reason="Character is wearing the wrong coat", root=workspace)

    book = Book.load("test-book", workspace)
    asset = book.registry.get("fig-extra")
    record = asset.draft("v1")
    assert record.status == "rejected"
    assert record.note == "Character is wearing the wrong coat"
    assert book.paths.resolve(record.path).is_file(), "rejected work is history, not rubbish"


def test_an_approved_draft_cannot_be_rejected(produced_book, workspace):
    with pytest.raises(ImmutableAssetError):
        api.reject("test-book", "p001", kind=PAGE, revision="v1", root=workspace)


def test_revision_keeps_the_approved_version_live_until_the_replacement_lands(
        produced_book, workspace):
    before = produced_book.manifest.get("p001").approved.sha256

    result = api.revise("test-book", "p001", kind=PAGE, reason="Tighten the standfirst",
                        root=workspace)
    assert result["next_revision"] == "v2"

    book = Book.load("test-book", workspace)
    page = book.manifest.get("p001")
    assert page.revision_open is True
    assert page.approved is not None, "the book must stay assemblable during a revision"
    assert page.approved.sha256 == before


def test_revision_archives_the_previous_approval_and_never_deletes_it(produced_book, workspace):
    original = produced_book.manifest.get("p001").approved.sha256
    api.revise("test-book", "p001", kind=PAGE, root=workspace)

    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["subheading"] = "In which the garden is measured again."
    book.write_page_spec("p001", spec)
    book.save()

    api.render("test-book", page_id="p001", submit=True, root=workspace)
    api.approve("test-book", "p001", kind=PAGE, root=workspace, by="operator")

    book = Book.load("test-book", workspace)
    page = book.manifest.get("p001")
    assert page.approved.revision == "v2"
    assert page.revision_open is False
    assert page.approved.sha256 != original

    assert len(page.approval_history) == 1
    archived = page.approval_history[0]
    assert archived.sha256 == original
    assert archived.superseded_at is not None
    archived_path = book.paths.resolve(archived.path)
    assert archived_path.is_file()
    assert "_history" in archived.path


def test_revising_something_unapproved_is_refused(planned_book, workspace):
    with pytest.raises(ValidationError):
        api.revise("test-book", "p001", kind=PAGE, root=workspace)


def test_approving_a_tampered_draft_is_refused(locked_book, workspace):
    api.register_asset("test-book", "fig-extra", root=workspace, kind="illustration")
    draft = _submit(workspace, seed=11)
    path = locked_book.paths.resolve(draft["path"])
    path.write_bytes(b"swapped after submission")
    with pytest.raises(ChecksumMismatch):
        api.approve("test-book", "fig-extra", kind=ASSET, root=workspace)


def test_approving_an_unknown_revision_lists_what_exists(locked_book, workspace):
    api.register_asset("test-book", "fig-extra", root=workspace, kind="illustration")
    _submit(workspace, seed=4)
    with pytest.raises(ValidationError) as excinfo:
        api.approve("test-book", "fig-extra", kind=ASSET, revision="v9", root=workspace)
    assert "v1" in excinfo.value.remedy


def test_approving_replacement_artwork_reopens_the_pages_that_use_it(produced_book, workspace):
    """New artwork means the page showing it is out of date.

    Leaving the page approved would show the old picture while the registry
    claimed the new one was canonical - drift, written into the book.
    """
    api.revise("test-book", "fig-scope", kind=ASSET, reason="Composition", root=workspace)
    art = make_image(workspace / "staging" / "fig-scope-v2.png", (1800, 1350), seed=31)
    api.submit_asset("test-book", "fig-scope", art, kind=ASSET, root=workspace)
    api.approve("test-book", "fig-scope", kind=ASSET, by="operator", root=workspace)

    book = Book.load("test-book", workspace)
    page = book.manifest.get("p002")
    assert "fig-scope" in page.required_assets
    assert page.revision_open is True, "the page using the replaced artwork must be reopened"
    assert page.approved is not None, "its approved render stays canonical until re-approved"

    untouched = book.manifest.get("p001")
    assert untouched.revision_open is False, "pages that do not use the asset are left alone"

    task = api.next_task("test-book", root=workspace)
    assert task["type"] == "page_render"
    assert task["page_id"] == "p002"


def test_first_approval_of_artwork_does_not_reopen_anything(planned_book, workspace):
    """Only a *replacement* reopens pages. A first approval has nothing to invalidate."""
    api.render("test-book", page_id="p002", submit=True, root=workspace)
    api.approve("test-book", "p002", kind=PAGE, root=workspace)
    book = Book.load("test-book", workspace)
    assert book.manifest.get("p002").revision_open is False
