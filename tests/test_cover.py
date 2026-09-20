"""Cover gate and measurable print constraints."""

from __future__ import annotations

import pytest
from PIL import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from bookfactory.core import api, checksums, cover, gates, production, tasks
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import write_json


def _interior(book, pages=80):
    path = book.paths.interior_pdf
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(432, 648))
    for _ in range(pages):
        pdf.showPage()
    pdf.save()


def test_new_book_requires_cover_but_legacy_book_does_not(new_book, workspace):
    assert cover.required(new_book)
    assert "cover" in " ".join(gates.release_ready(new_book).reasons).lower()
    cover.path(new_book).unlink()
    legacy = Book.load("test-book", workspace)
    assert cover.release_reasons(legacy) == []
    assert cover.readiness(legacy)["cover"] == "legacy_not_required"


def test_wrap_dimensions_follow_final_pdf_and_paper(new_book):
    _interior(new_book, 80)
    white = cover.dimensions(new_book)
    assert white["spine_in"] == .18016
    assert white["width_in"] == 12.43016
    assert white["height_in"] == 9.25
    data = cover.load(new_book)
    data["paper"] = "cream"
    write_json(cover.path(new_book), data)
    assert cover.dimensions(new_book)["spine_in"] == .2


def test_recovered_preview_can_size_draft_without_claiming_interior_readiness(new_book):
    _interior(new_book, 80)
    preserved = new_book.paths.root / "releases/preserved-interior.pdf"
    preserved.parent.mkdir(parents=True, exist_ok=True)
    new_book.paths.interior_pdf.rename(preserved)
    data = cover.load(new_book)
    data["preview_interior"] = {"path": "releases/preserved-interior.pdf",
                                "sha256": checksums.sha256_file(preserved)}
    write_json(cover.path(new_book), data)

    assert cover.dimensions(new_book)["width_in"] == 12.43016
    assert cover.readiness(new_book)["interior"] == "pending"
    with pytest.raises(ValidationError, match="Assemble the final interior"):
        cover.finalize(new_book, "v1")

    preserved.write_bytes(preserved.read_bytes() + b"changed")
    with pytest.raises(ValidationError, match="missing or has changed"):
        cover.dimensions(new_book)


def test_artwork_native_height_is_checked_and_draft_is_preserved(new_book, workspace):
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    source = workspace / "short.png"
    Image.new("RGB", (1024, 1200), "white").save(source)
    draft = api.submit_asset("test-book", cover.ART_ID, source, kind="asset", root=workspace)
    assert new_book.asset_constraints(new_book.registry.get(cover.ART_ID))["min_pixels"] == 1020
    assert [e["constraint"] for e in draft["constraint_failures"]] == ["min_height_pixels"]
    assert new_book.paths.resolve(draft["path"]).is_file()


def test_cover_checkpoint_waits_even_with_visual_checkpoint_authorization(new_book, workspace):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(direction="Matched cover direction", author="A Writer",
                back_copy="Some book copy", drafts=[{"revision": "v1", "path": "cover/drafts/cover-v1.pdf"}])
    write_json(cover.path(new_book), data)
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    source = workspace / "adequate.png"
    Image.new("RGB", (1100, 1600), "white").save(source)
    api.submit_asset("test-book", cover.ART_ID, source, kind="asset", root=workspace)
    book = Book.load("test-book", workspace)
    book.state.production_policy.mode = "visual_checkpoint"
    book.state.production_policy.operator_authorized = True
    task = tasks._cover_task(book)
    assert task.gate == "cover_visual_checkpoint"
    assert production.compute_mode(book, task) == "wait_for_operator"


def test_status_reports_interior_and_cover_separately(new_book, workspace):
    result = api.status("test-book", root=workspace)
    assert result["readiness"] == {"interior": "pending", "cover": "in_production",
                                   "book": "pending"}


def test_wrong_wrap_box_and_missing_selectable_type_fail(new_book, workspace):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(author="A Writer", back_copy="Back-cover statement")
    write_json(cover.path(new_book), data)
    wrong = workspace / "wrong-wrap.pdf"
    pdf = canvas.Canvas(str(wrong), pagesize=(612, 792))
    pdf.drawString(30, 700, "A Writer")
    pdf.save()
    failures = cover.check_pdf(new_book, wrong)
    assert any("box" in issue for issue in failures)
    assert any("selectable" in issue for issue in failures)


def test_migrating_former_release_preserves_interior_stage_evidence(new_book, workspace):
    _interior(new_book)
    cover.path(new_book).unlink()
    book = Book.load("test-book", workspace)
    book.state.stage = "release_ready"
    book.save()
    cover.initialize(book)
    assert Book.load("test-book", workspace).state.stage == "cover_production"
    assert book.paths.interior_pdf.is_file()


def test_explicit_cover_approval_then_preflight(new_book, workspace):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(direction="Match locked art", author="A Writer", back_copy="Gift for runners")
    write_json(cover.path(new_book), data)
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    art = workspace / "native.png"
    Image.new("RGB", (1100, 1600), "yellow").save(art)
    api.submit_asset("test-book", cover.ART_ID, art, kind="asset", root=workspace)
    wrap = workspace / "full-wrap.pdf"
    dim = cover.dimensions(new_book)
    pdfmetrics.registerFont(TTFont("CoverTest", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdf = canvas.Canvas(str(wrap), pagesize=(dim["width_in"]*72, dim["height_in"]*72))
    pdf.setFont("CoverTest", 18)
    pdf.drawString(6.6*72, 8*72, "Test Book")
    pdf.drawString(6.6*72, .5*72, "A Writer")
    pdf.drawString(.5*72, 5*72, "Gift for runners")
    pdf.drawImage(str(art), 7*72, 1.3*72, width=3.4*72, height=5.1*72)
    pdf.save()
    book = Book.load("test-book", workspace)
    draft = cover.submit(book, wrap)
    assert cover.readiness(book)["cover"] == "awaiting_approval"
    assert not gates.release_ready(book).ok
    cover.approve(book, draft["revision"], by="Test Operator")
    assert cover.preflight(book)["status"] == "pass"
    assert cover.readiness(book)["cover"] == "ready"


def test_provisional_cover_approval_waits_for_matching_final_interior(new_book, workspace):
    _interior(new_book)
    preserved = new_book.paths.root / "releases/preserved.pdf"
    preserved.parent.mkdir(exist_ok=True)
    new_book.paths.interior_pdf.rename(preserved)
    data = cover.load(new_book)
    data.update(direction="Match locked art", author="A Writer", back_copy="Gift for runners",
                preview_interior={"path": "releases/preserved.pdf",
                                  "sha256": checksums.sha256_file(preserved)})
    write_json(cover.path(new_book), data)
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    art = workspace / "native.png"
    Image.new("RGB", (1100, 1600), "yellow").save(art)
    api.submit_asset("test-book", cover.ART_ID, art, kind="asset", root=workspace)
    wrap = workspace / "wrap.pdf"
    dim = cover.dimensions(new_book)
    pdfmetrics.registerFont(TTFont("CoverTestProvisional", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdf = canvas.Canvas(str(wrap), pagesize=(dim["width_in"]*72, dim["height_in"]*72))
    pdf.setFont("CoverTestProvisional", 18)
    pdf.drawString(6.6*72, 8*72, "Test Book")
    pdf.drawString(6.6*72, .5*72, "A Writer")
    pdf.drawString(.5*72, 5*72, "Gift for runners")
    pdf.drawImage(str(art), 7*72, 1.3*72, width=3.4*72, height=5.1*72)
    pdf.save()
    book = Book.load("test-book", workspace)
    draft = cover.submit(book, wrap)
    approval = cover.approve(book, draft["revision"], by="Operator")
    assert approval["status"] == "review_approved"
    assert cover.readiness(book)["cover"] == "awaiting_final_interior"
    assert not (book.paths.root / "output/cover.pdf").exists()
    with pytest.raises(ValidationError, match="Assemble the final interior"):
        cover.finalize(book, draft["revision"])
    _interior(book, 82)
    with pytest.raises(ValidationError, match="dimensions changed"):
        cover.finalize(book, draft["revision"])
    _interior(book, 80)
    assert cover.finalize(book, draft["revision"])["by"] == "Operator"
    assert cover.preflight(book)["status"] == "pass"
