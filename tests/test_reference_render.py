"""`bookfactory reference render` and the `palette_sheet` page type.

These typeset the reference-set samples a book's visual reference set needs
before it has a page plan (a chapter opener, a checklist/diagnostic page, an
editorial page, a palette sheet). The sample spec is a real page spec, but it
never joins the page manifest, and the picture budget does not apply to it.
"""

from __future__ import annotations

import pytest
from pypdf import PdfReader

from bookfactory.core import api
from bookfactory.core.book import ASSET, Book
from bookfactory.core.errors import ValidationError
from bookfactory.render.renderer import render_reference_page

PALETTE_SPEC = {
    "type": "palette_sheet",
    "copy": {"heading": "Palette and type", "body": "One sheet, so nobody has to guess."},
}


def test_reference_render_produces_an_asset_draft_at_300_dpi(new_book, workspace):
    api.register_asset("test-book", "ref-palette", root=workspace, kind="palette_reference",
                       reference_role="palette", title="Palette, type and layout rules")

    result = api.render_reference("test-book", "ref-palette", PALETTE_SPEC, root=workspace)

    assert result["asset_id"] == "ref-palette"
    assert result["revision"] == "v1"
    assert result["width"] == 1800
    assert result["height"] == 2700

    book = Book.load("test-book", workspace)
    asset = book.registry.get("ref-palette")
    draft = asset.draft("v1")
    assert draft is not None
    png_path = book.paths.resolve(draft.path)
    assert png_path.is_file()


def test_reference_render_refuses_an_unregistered_asset(new_book, workspace):
    with pytest.raises(ValidationError) as excinfo:
        api.render_reference("test-book", "ref-not-registered", PALETTE_SPEC, root=workspace)
    assert "not registered" in excinfo.value.message
    assert "bookfactory asset add test-book ref-not-registered" in excinfo.value.remedy


def test_reference_sample_never_joins_the_page_manifest(new_book, workspace):
    api.register_asset("test-book", "ref-palette", root=workspace, kind="palette_reference",
                       reference_role="palette")

    api.render_reference("test-book", "ref-palette", PALETTE_SPEC, root=workspace)

    book = Book.load("test-book", workspace)
    assert len(book.manifest) == 0
    assert book.manifest.find("p000") is None
    assert not book.paths.spec_file("p000").exists()


def test_reference_render_places_an_approved_illustration(locked_book, workspace):
    """An approved reference (e.g. the main character) can appear in a sample."""
    spec = {
        "type": "chapter_opener",
        "chapter": 1,
        "copy": {"heading": "Chapter opener example"},
        "illustration": {"asset_id": "ref-character-main", "placement": "full_page"},
    }
    pdf_path = render_reference_page(locked_book, spec,
                                     destination=workspace / "ref-layout-chapter-opener.pdf")
    assert pdf_path.is_file()
    # The rendered page embeds the approved artwork as an image, not as text.
    assert len(PdfReader(str(pdf_path)).pages[0].images) >= 1


def test_palette_sheet_renders_the_hex_values_as_real_type(locked_book, workspace):
    pdf_path = render_reference_page(locked_book, PALETTE_SPEC,
                                     destination=workspace / "ref-palette.pdf")
    text = PdfReader(str(pdf_path)).pages[0].extract_text() or ""
    tokens = locked_book.design_tokens()
    for hex_value in tokens["palette"].values():
        assert hex_value in text, f"{hex_value} missing from the rendered palette sheet"


def test_reference_render_ignores_the_picture_budget(locked_book, workspace):
    """A reference is never a page picture (AGENTS.md section 5a)."""
    api.set_pictures("test-book", "chapter_openers", by="tester", root=workspace)
    spec = {
        "type": "editorial_illustration",  # not a chapter_opener: would break this budget
        "copy": {"heading": "Editorial page example"},
        "illustration": {"asset_id": "ref-character-main", "placement": "top"},
    }
    book = Book.load("test-book", workspace)
    # Would be refused for a real page: the budget must not even be consulted here.
    pdf_path = render_reference_page(book, spec, destination=workspace / "ref-page-editorial.pdf")
    assert pdf_path.is_file()


def test_reference_render_requires_a_type(new_book):
    with pytest.raises(ValidationError) as excinfo:
        render_reference_page(new_book, {"copy": {"heading": "No type here"}})
    assert "needs a" in excinfo.value.message
    assert "\"type\"" in excinfo.value.message


def test_reference_render_cli_help_lists_the_command():
    from bookfactory.cli.main import build_parser

    parser = build_parser()
    help_text = parser.format_help()
    assert "reference" in help_text
