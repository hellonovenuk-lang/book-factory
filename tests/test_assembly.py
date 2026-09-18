"""Assembly. The rule is fail closed: never substitute the closest file."""

from __future__ import annotations

import os

import pytest
from pypdf import PdfReader

from bookfactory.core import api
from bookfactory.core.book import PAGE, Book
from bookfactory.core.errors import AssemblyError


def test_assembly_produces_one_pdf_page_per_manifest_page(produced_book, workspace):
    record = api.assemble("test-book", root=workspace)
    assert record["page_count"] == len(produced_book.manifest)
    reader = PdfReader(str(produced_book.paths.interior_pdf))
    assert len(reader.pages) == len(produced_book.manifest)


def test_assembly_preserves_manifest_order(produced_book, workspace):
    record = api.assemble("test-book", root=workspace)
    order = [entry["page_id"] for entry in record["pages"]]
    assert order == [page.page_id for page in produced_book.manifest]
    assert [entry["position"] for entry in record["pages"]] == [1, 2, 3, 4]


def test_assembly_records_exactly_which_file_became_which_page(produced_book, workspace):
    """The question nobody could answer last time: which file is page 58?"""
    api.assemble("test-book", root=workspace)
    manifest = produced_book.paths.interior_pdf.with_suffix(".manifest.json")
    assert manifest.is_file()

    from bookfactory.core.jsonio import read_json

    record = read_json(manifest)
    for entry, page in zip(record["pages"], produced_book.manifest):
        assert entry["source"] == page.approved.path
        assert entry["sha256"] == page.approved.sha256


def test_assembly_is_blocked_by_an_unapproved_page(planned_book, workspace):
    api.render("test-book", page_id="p001", submit=True, root=workspace)
    api.approve("test-book", "p001", kind=PAGE, root=workspace)
    with pytest.raises(AssemblyError) as excinfo:
        api.assemble("test-book", root=workspace)
    assert "p002" in excinfo.value.message
    assert "not approved" in excinfo.value.message


def test_assembly_is_blocked_by_a_checksum_mismatch(produced_book, workspace):
    page = produced_book.manifest.get("p002")
    path = produced_book.paths.resolve(page.approved.path)
    os.chmod(path, 0o644)
    path.write_bytes(b"%PDF-1.4 tampered")

    with pytest.raises(AssemblyError) as excinfo:
        api.assemble("test-book", root=workspace)
    assert "checksum" in excinfo.value.message


def test_assembly_refuses_a_draft_substituted_for_an_approved_page(produced_book, workspace):
    """Pointing the manifest at a draft must not quietly work."""
    book = Book.load("test-book", workspace)
    page = book.manifest.get("p003")
    draft = page.drafts[0]
    page.approved.path = draft.path
    page.approved.sha256 = draft.sha256
    book.save()

    with pytest.raises(AssemblyError) as excinfo:
        api.assemble("test-book", root=workspace)
    assert "not inside pages/approved" in excinfo.value.message


def test_assembly_is_blocked_by_a_missing_approved_file(produced_book, workspace):
    page = produced_book.manifest.get("p004")
    path = produced_book.paths.resolve(page.approved.path)
    os.chmod(path, 0o644)
    path.unlink()
    with pytest.raises(AssemblyError) as excinfo:
        api.assemble("test-book", root=workspace)
    assert "missing" in excinfo.value.message


def test_assembly_is_blocked_by_a_gap_in_the_page_sequence(produced_book, workspace):
    book = Book.load("test-book", workspace)
    book.manifest.get("p004").sequence = 9
    book.save()
    with pytest.raises(AssemblyError) as excinfo:
        api.assemble("test-book", root=workspace)
    assert "gaps in page sequence" in excinfo.value.message


def test_assembly_never_regenerates_a_page(produced_book, workspace):
    """Assembly must be purely mechanical."""
    import bookfactory.render.renderer as renderer

    original = renderer.render_page

    def explode(*args, **kwargs):  # pragma: no cover - only runs on failure
        raise AssertionError("assembly must never render anything")

    renderer.render_page = explode
    try:
        api.assemble("test-book", root=workspace)
    finally:
        renderer.render_page = original


def test_assembly_is_byte_stable_for_unchanged_input(produced_book, workspace):
    first = api.assemble("test-book", root=workspace)["output_sha256"]
    second = api.assemble("test-book", root=workspace)["output_sha256"]
    assert first == second


def test_review_output_uses_existing_renders_only(produced_book, workspace):
    result = api.review("test-book", root=workspace)
    outputs = result["outputs"]
    assert "contact_sheet" in outputs
    assert "full_book_review" in outputs
    assert "chapter_01" in outputs
    sheet = produced_book.paths.resolve(outputs["contact_sheet"])
    assert sheet.is_file()
    assert len(PdfReader(str(sheet)).pages) >= 1
    status = produced_book.paths.resolve(outputs["production_status"])
    assert "Production status" in status.read_text(encoding="utf-8")


def test_open_revision_is_reported_but_uses_the_approved_version(produced_book, workspace):
    api.revise("test-book", "p002", kind=PAGE, reason="Caption reads oddly", root=workspace)
    record = api.assemble("test-book", root=workspace)
    assert record["page_count"] == 4

    from bookfactory.qa import assembly as assembly_qa

    findings = assembly_qa.check(Book.load("test-book", workspace)).findings
    assert any(finding.code == "assembly.open_revision" for finding in findings)
