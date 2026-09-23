"""`bookfactory cover build`: typesetting the full-wrap cover from cover/cover.json."""

from __future__ import annotations

import pytest
from PIL import Image
from reportlab.pdfgen import canvas

from bookfactory.core import api, cover
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from bookfactory.render import cover as cover_render


def _interior(book, pages=80):
    path = book.paths.interior_pdf
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(432, 648))
    for _ in range(pages):
        pdf.showPage()
    pdf.save()


def _set_cover_fields(book, **overrides):
    data = cover.load(book)
    data.update(author="A Writer",
                back_copy="Paragraph one about the book.\n\nParagraph two, with more detail.")
    data.update(overrides)
    cover.save(book, data)


def _native_artwork(workspace, book):
    api.register_asset("test-book", cover.ART_ID, root=workspace, kind="cover_artwork")
    art = workspace / "cover-art.png"
    Image.new("RGB", (1100, 1600), "yellow").save(art)
    api.submit_asset("test-book", cover.ART_ID, art, kind="asset", root=workspace)


def test_native_cover_builds_and_passes_checks(new_book, workspace):
    _interior(new_book, 80)
    _set_cover_fields(new_book, subtitle="A field guide")
    _native_artwork(workspace, new_book)
    book = Book.load("test-book", workspace)
    result = cover_render.build(book)
    assert result["problems"] == []
    assert book.paths.resolve(result["pdf"]).is_file()
    for preview in result["previews"]:
        assert book.paths.resolve(preview).is_file()
    assert result["submitted"] is None


def test_text_only_cover_builds_with_no_image(new_book, workspace):
    _interior(new_book, 80)
    _set_cover_fields(new_book)
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    book = Book.load("test-book", workspace)
    result = cover_render.build(book)
    assert result["problems"] == []


def test_submit_creates_a_draft_but_never_approves(new_book, workspace):
    _interior(new_book, 80)
    _set_cover_fields(new_book)
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    result = api.cover_build("test-book", submit=True, root=workspace)
    assert result["problems"] == []
    assert result["submitted"]["revision"] == "v1"
    data = cover.load(Book.load("test-book", workspace))
    assert data["drafts"][0]["status"] == "draft"
    assert data["approved"] is None


def test_missing_back_copy_raises_with_remedy(new_book, workspace):
    _interior(new_book, 80)
    data = cover.load(new_book)
    data.update(author="A Writer")
    cover.save(new_book, data)
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    book = Book.load("test-book", workspace)
    with pytest.raises(ValidationError, match="back_copy") as excinfo:
        cover_render.build(book)
    assert excinfo.value.remedy


def test_spine_text_left_off_when_page_count_too_low(new_book, workspace):
    _interior(new_book, 40)
    _set_cover_fields(new_book, spine_text=True)
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    book = Book.load("test-book", workspace)
    result = cover_render.build(book)
    assert any("spine" in note.lower() for note in result["notes"])
    # cover.json still records the request, so check_pdf's own spine rule still
    # flags it - the note explains why the build left it off the artwork.
    assert any("Spine text cannot fit" in problem for problem in result["problems"])


def test_spine_text_is_set_vertically_inside_the_spine(new_book, workspace):
    import fitz

    _interior(new_book, 200)
    _set_cover_fields(new_book, spine_text="Spine Title")
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    book = Book.load("test-book", workspace)
    result = cover_render.build(book)
    assert result["problems"] == []
    dim = result["dimensions"]
    back_fold = (dim["bleed_in"] + dim["trim_width_in"]) * 72
    front_fold = back_fold + dim["spine_in"] * 72
    with fitz.open(str(book.paths.resolve(result["pdf"]))) as doc:
        lines = [line for block in doc[0].get_text("dict")["blocks"]
                 for line in block.get("lines", [])
                 if "Spine Title" in "".join(s["text"] for s in line["spans"])]
    assert lines, "spine text must be real, selectable type"
    box = fitz.Rect(lines[0]["bbox"])
    assert lines[0]["dir"] == (0.0, 1.0), "spine text reads top to bottom"
    assert back_fold < box.x0 and box.x1 < front_fold, "spine text stays within the spine"


def test_design_font_outside_the_book_is_rejected(new_book, workspace):
    _interior(new_book, 80)
    _set_cover_fields(new_book, design={"title_font": "/etc/some-system-font.ttf"})
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    book = Book.load("test-book", workspace)
    with pytest.raises(ValidationError, match="outside the book project"):
        cover_render.build(book)


def test_cli_cover_build_reports_problems_and_exits_nonzero(new_book, workspace, monkeypatch):
    from bookfactory.cli.main import main as cli

    _interior(new_book, 80)
    _set_cover_fields(new_book)
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    monkeypatch.setattr(cover, "check_pdf", lambda book, file: ["synthetic failure"])
    assert cli(["cover", "build", "test-book", "--root", str(workspace)]) == 1


def test_cli_cover_build_exits_zero_when_clean(new_book, workspace):
    from bookfactory.cli.main import main as cli

    _interior(new_book, 80)
    _set_cover_fields(new_book)
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    assert cli(["cover", "build", "test-book", "--root", str(workspace)]) == 0
