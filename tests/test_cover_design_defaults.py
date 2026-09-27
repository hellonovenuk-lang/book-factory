"""Task 20.5: cover fonts ship with Book Factory, and a big-lettering cover
starts with a ready design block instead of one copied by hand from another
book.

See PLAN.md task 20.5.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfgen import canvas

from bookfactory.core import api, cover
from bookfactory.core.api import _default_big_lettering_design
from bookfactory.core.book import Book
from bookfactory.render import cover as cover_render

IDEA = "A fake rehabilitation manual for men addicted to golf."

FULL_ANSWERS = {
    "idea": IDEA,
    "buyer": "His partner.",
    "recipient": "The golf addict himself.",
    "recognition_trigger": "He irons his golf trousers before his work shirts.",
    "humour_level": "medium",
    "visual_feel": "classic_editorial_caricature",
    "colour_direction": "colourful",
    "main_character": "book_factory_invents",
    "main_character_details": "A stubborn man in his fifties who still owns his school jumper.",
    "length": "80",
    "must_include": "none",
    "must_avoid": "none",
    "title": "The Golf Addict's Guide",
    "print_colour": "black_and_white",
    "cover_style": "big_lettering",
    "production_policy": "checkpointed",
}


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


def test_bundled_font_is_used_when_the_book_has_no_font_file(new_book, workspace):
    _interior(new_book, 80)
    _set_cover_fields(new_book, design={
        "title_font": "style/fonts/Anton-Regular.ttf",
        "body_font": "style/fonts/Archivo-Regular.ttf",
    })
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Operator")
    book = Book.load("test-book", workspace)
    assert not (book.paths.root / "style/fonts/Anton-Regular.ttf").exists()
    result = cover_render.build(book)
    assert result["problems"] == []


def test_book_own_font_still_wins_over_the_bundled_one(new_book, workspace):
    from bookfactory.render.cover import BUNDLED_FONTS_DIR, _book_font

    fonts_dir = new_book.paths.root / "style/fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    own_font = fonts_dir / "Anton-Regular.ttf"
    # Deliberately a different file, so a match proves it did NOT fall through
    # to the bundled copy.
    own_font.write_bytes((BUNDLED_FONTS_DIR / "Archivo-Regular.ttf").read_bytes())

    resolved = _book_font(new_book, "style/fonts/Anton-Regular.ttf", field="title_font")

    assert resolved == own_font.resolve()


def _start(workspace: Path, book_id: str = "golf") -> str:
    return api.create_from_idea(IDEA, root=workspace, book_id=book_id)["book_id"]


def test_confirming_big_lettering_intake_writes_a_design_block(workspace: Path) -> None:
    book_id = _start(workspace)
    api.submit_intake(book_id, dict(FULL_ANSWERS), root=workspace)

    book = Book.load(book_id, workspace)
    data = cover.load(book)
    assert data["artwork"] == cover.TEXT_ONLY
    design = data["design"]
    assert design["title_font"] == "style/fonts/Anton-Regular.ttf"
    assert design["body_font"] == "style/fonts/Archivo-Regular.ttf"
    assert design["title_lines"]
    joined = "".join(c for c in "".join(l["text"] for l in design["title_lines"]).casefold()
                     if c.isalnum())
    wanted = "".join(c for c in book.state.title.casefold() if c.isalnum())
    assert joined == wanted
    for line in design["title_lines"]:
        assert 12 <= line["size_pt"] <= 160

    events = api.audit_history(book_id, root=workspace, event="cover_design_defaulted")
    assert len(events) == 1


def test_existing_design_block_is_never_overwritten(new_book, workspace) -> None:
    custom_design = {"background": "#000000"}
    data = cover.load(new_book)
    data["design"] = custom_design
    cover.save(new_book, data)

    _default_big_lettering_design(new_book, by="tester")

    assert cover.load(new_book)["design"] == custom_design


def test_default_design_for_the_padel_title_builds_with_no_safety_problems(new_book, workspace) -> None:
    book = new_book
    book.state.title = ("The Padel Addict's Guide to Talking About Anything Else")
    book.save()
    _interior(book, 80)
    _set_cover_fields(book)
    _default_big_lettering_design(book, by="tester")
    cover.set_artwork(book, cover.TEXT_ONLY, by="Operator")

    book = Book.load("test-book", workspace)
    result = cover_render.build(book)
    assert result["problems"] == []


def test_default_design_for_a_long_wide_title_builds_with_no_safety_problems(new_book, workspace) -> None:
    """Sizing by measured width, not letter count: a long title with wide
    capitals once pushed "COMPLETELY UNREASONABLE" into the spine margin."""
    book = new_book
    book.state.title = ("The Extremely Long And Completely Unreasonable Guide To "
                        "Something Nobody Asked About")
    book.save()
    _interior(book, 80)
    _set_cover_fields(book)
    _default_big_lettering_design(book, by="tester")
    cover.set_artwork(book, cover.TEXT_ONLY, by="Operator")

    book = Book.load("test-book", workspace)
    result = cover_render.build(book)
    assert result["problems"] == []
