"""Quality assurance layers."""

from __future__ import annotations

import os

from bookfactory.core import api
from bookfactory.core.book import Book
from bookfactory.qa import content, technical, visual
from tests.conftest import make_image


def _codes(result) -> list[str]:
    return [finding.code for finding in result.findings]


def test_clean_book_passes_every_layer(produced_book, workspace):
    report = api.qa("test-book", root=workspace)
    assert report["summary"]["status"] == "pass", report["layers"]
    assert report["summary"]["errors"] == 0


def test_qa_stamps_each_page_in_the_manifest(produced_book, workspace):
    api.qa("test-book", root=workspace)
    book = Book.load("test-book", workspace)
    for page in book.manifest:
        assert page.qa["content"] == "pass"
        assert page.qa["technical"] == "pass"


def test_content_qa_catches_placeholder_copy(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["body"] = ["TODO: write this bit."]
    book.write_page_spec("p001", spec)
    book.save()
    assert "content.placeholder" in _codes(content.check(Book.load("test-book", workspace)))


def test_content_qa_catches_missing_copy_for_the_page_type(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p003")
    spec["copy"]["items"] = []
    book.write_page_spec("p003", spec)
    book.save()
    assert "content.missing_copy" in _codes(content.check(Book.load("test-book", workspace)))


def test_content_qa_catches_a_repeated_page_concept(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p002")
    spec["copy"]["heading"] = "The Assessment"
    book.write_page_spec("p002", spec)
    book.save()
    assert "content.duplicate_heading" in _codes(content.check(Book.load("test-book", workspace)))


def test_content_qa_flags_the_ai_constructions_the_voice_bible_bans(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["body"] = ["It's not a garden, it's a commitment nobody signed."]
    book.write_page_spec("p001", spec)
    book.save()
    assert "content.ai_tell" in _codes(content.check(Book.load("test-book", workspace)))


def test_content_qa_flags_phrases_banned_in_the_voice_bible(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["body"] = ["The subject went inside, and little did he know what August held."]
    book.write_page_spec("p001", spec)
    book.save()
    assert "content.banned_phrase" in _codes(content.check(Book.load("test-book", workspace)))


def test_content_qa_notices_copy_written_against_an_older_manuscript(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["source"] = {"manuscript_version": "v0", "visual_style_version": "v1"}
    book.write_page_spec("p001", spec)
    book.save()
    assert "content.manuscript_drift" in _codes(content.check(Book.load("test-book", workspace)))


def test_content_qa_always_asks_a_human_to_read_the_book(produced_book):
    findings = content.check(produced_book).findings
    assert any(finding.needs_human for finding in findings)


def test_visual_qa_catches_artwork_below_print_resolution(planned_book, workspace):
    small = make_image(workspace / "staging" / "small.png", (400, 300), seed=2)
    api.register_asset("test-book", "fig-small", root=workspace, kind="illustration",
                       page_id="p002")
    api.submit_asset("test-book", "fig-small", small, kind="asset", root=workspace)
    api.approve("test-book", "fig-small", kind="asset", root=workspace)

    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p002")
    spec["illustration"]["asset_id"] = "fig-small"
    book.write_page_spec("p002", spec)
    page = book.manifest.get("p002")
    page.required_assets = ["fig-small"]
    book.save()

    codes = _codes(visual.check(Book.load("test-book", workspace)))
    assert "visual.low_resolution" in codes


def test_visual_qa_catches_a_page_pointing_at_unapproved_artwork(planned_book, workspace):
    book = Book.load("test-book", workspace)
    asset = book.registry.get("fig-scope")
    asset.approved = None
    asset.status = "draft_submitted"
    book.save()
    assert "visual.asset_not_approved" in _codes(visual.check(Book.load("test-book", workspace)))


def test_visual_qa_warns_when_a_spec_permits_generated_text(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p002")
    spec["illustration"]["embedded_text"] = True
    book.write_page_spec("p002", spec)
    book.save()
    assert "visual.embedded_text" in _codes(visual.check(Book.load("test-book", workspace)))


def test_visual_qa_catches_the_same_picture_used_twice(planned_book, workspace):
    art = workspace / "staging" / "fig-scope.png"
    api.register_asset("test-book", "fig-copy", root=workspace, kind="illustration")
    api.submit_asset("test-book", "fig-copy", art, kind="asset", root=workspace)
    api.approve("test-book", "fig-copy", kind="asset", root=workspace)
    assert "visual.duplicate_artwork" in _codes(visual.check(Book.load("test-book", workspace)))


def test_technical_qa_catches_a_tampered_approved_page(produced_book, workspace):
    page = produced_book.manifest.get("p001")
    path = produced_book.paths.resolve(page.approved.path)
    os.chmod(path, 0o644)
    path.write_bytes(b"%PDF-1.4 tampered")
    assert "technical.checksum_mismatch" in _codes(
        technical.check(Book.load("test-book", workspace)))


def test_technical_qa_catches_a_gutter_too_small_for_the_page_count(produced_book, workspace):
    from bookfactory.core.jsonio import read_json, write_json

    tokens = read_json(produced_book.paths.design_tokens)
    tokens["margins_in"]["inner"] = 0.2
    write_json(produced_book.paths.design_tokens, tokens)
    assert "technical.gutter_too_small" in _codes(
        technical.check(Book.load("test-book", workspace)))


def test_technical_qa_catches_a_page_at_the_wrong_trim(produced_book, workspace):
    book = Book.load("test-book", workspace)
    book.state.format.trim = "8.5x11"
    book.save()
    codes = _codes(technical.check(Book.load("test-book", workspace)))
    assert "technical.wrong_trim" in codes


def test_qa_report_is_written_and_readable(produced_book, workspace):
    api.qa("test-book", root=workspace)
    assert produced_book.paths.qa_latest.is_file()
    assert list(produced_book.paths.qa_reports_dir.glob("*-qa.json"))
