"""The deterministic renderer."""

from __future__ import annotations

import pytest
from pypdf import PdfReader

from bookfactory.core import api
from bookfactory.core.book import PAGE, Book
from bookfactory.core.errors import RenderError
from bookfactory.render.renderer import page_side, render_page, render_page_html

POINTS_PER_INCH = 72.0


def test_page_renders_to_exactly_the_trim_size(planned_book):
    path = render_page(planned_book, "p001")
    box = PdfReader(str(path)).pages[0].mediabox
    assert float(box.width) == pytest.approx(6 * POINTS_PER_INCH, abs=0.5)
    assert float(box.height) == pytest.approx(9 * POINTS_PER_INCH, abs=0.5)


def test_rendering_is_deterministic(planned_book):
    from bookfactory.core import checksums

    first = checksums.sha256_file(render_page(planned_book, "p001"))
    second = checksums.sha256_file(render_page(planned_book, "p001"))
    assert first == second, "an unchanged page must re-render to identical bytes"


def test_render_writes_the_html_for_debugging(planned_book):
    render_page(planned_book, "p001")
    debug = planned_book.paths.renders_dir / "html" / "p001.html"
    assert debug.is_file()
    assert "The Assessment" in debug.read_text(encoding="utf-8")


def test_copy_is_set_as_real_type_not_drawn(planned_book):
    """Every word on the page comes from the spec and is typeset by the renderer."""
    html = render_page_html(planned_book, "p003")
    assert "There is a bag of compost in the car." in html
    assert "Severity assessment" in html
    assert "Two points is within normal limits." in html


def test_page_numbers_come_from_the_manifest(planned_book):
    html = render_page_html(planned_book, "p002")
    page = planned_book.manifest.get("p002")
    assert f'class="folio folio--verso">{page.printed_number}<' in html


def test_recto_and_verso_margins_are_mirrored(planned_book):
    from bookfactory.render.renderer import geometry

    recto = geometry(planned_book, side="recto")
    verso = geometry(planned_book, side="verso")
    assert recto["margin_left_in"] > recto["margin_right_in"], "gutter is on the left of a recto"
    assert verso["margin_right_in"] > verso["margin_left_in"], "gutter is on the right of a verso"
    assert recto["margin_left_in"] == verso["margin_right_in"]


def test_side_follows_the_printed_page_number(planned_book):
    for page in planned_book.manifest:
        expected = "recto" if (page.printed_number or page.sequence) % 2 else "verso"
        assert page_side(page) == expected


def test_renderer_refuses_to_use_unapproved_artwork(planned_book, workspace):
    """A page built from a draft is a page nobody can later prove was approved."""
    book = Book.load("test-book", workspace)
    asset = book.registry.get("fig-scope")
    asset.approved = None
    asset.status = "draft_submitted"
    book.save()

    book = Book.load("test-book", workspace)
    with pytest.raises(RenderError) as excinfo:
        render_page(book, "p002")
    assert "not approved" in excinfo.value.message


def test_overflowing_copy_fails_loudly_instead_of_being_clipped(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["body"] = ["A very long paragraph. " * 400]
    book.write_page_spec("p001", spec)
    book.save()

    with pytest.raises(RenderError) as excinfo:
        render_page(Book.load("test-book", workspace), "p001")
    assert "without copy the spec requires" in excinfo.value.message
    assert "will not ship a page that is missing approved words" in excinfo.value.remedy


def test_render_submit_registers_a_draft(planned_book, workspace):
    result = api.render("test-book", page_id="p001", submit=True, root=workspace)
    entry = result["rendered"][0]
    assert entry["draft"] == "v1"
    book = Book.load("test-book", workspace)
    assert book.manifest.get("p001").status == "draft_submitted"


def test_whole_book_render_skips_an_approved_page(planned_book, workspace):
    api.render("test-book", page_id="p001", submit=True, root=workspace)
    api.approve("test-book", "p001", kind=PAGE, root=workspace, by="tester")

    result = api.render("test-book", submit=True, root=workspace)

    assert {"page_id": "p001", "reason": "approved"} in result["skipped"]
    assert not any(entry["page_id"] == "p001" for entry in result["rendered"])
    book = Book.load("test-book", workspace)
    assert len(book.manifest.get("p001").drafts) == 1, "approved page must not gain a new draft"
    for page_id in ("p002", "p003", "p004"):
        assert any(entry["page_id"] == page_id for entry in result["rendered"])


def test_whole_book_render_skips_a_page_with_no_spec(planned_book, workspace):
    book = Book.load("test-book", workspace)
    page = book.manifest.get("p003")
    page.spec = None
    book.save()

    result = api.render("test-book", submit=True, root=workspace)

    assert {"page_id": "p003", "reason": "no spec"} in result["skipped"]
    for page_id in ("p001", "p002", "p004"):
        assert any(entry["page_id"] == page_id for entry in result["rendered"])


def test_whole_book_render_carries_on_past_a_failed_page(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["body"] = ["A very long paragraph. " * 400]
    book.write_page_spec("p001", spec)
    book.save()

    result = api.render("test-book", submit=True, root=workspace)

    failed = {entry["page_id"]: entry for entry in result["failed"]}
    assert "p001" in failed
    assert "without copy the spec requires" in failed["p001"]["error"]
    assert "remedy" in failed["p001"]
    for page_id in ("p002", "p003", "p004"):
        assert any(entry["page_id"] == page_id and entry.get("draft")
                   for entry in result["rendered"])
    book = Book.load("test-book", workspace)
    assert book.manifest.get("p002").status == "draft_submitted"


def test_single_page_render_still_raises_on_failure(planned_book, workspace):
    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["body"] = ["A very long paragraph. " * 400]
    book.write_page_spec("p001", spec)
    book.save()

    with pytest.raises(RenderError):
        api.render("test-book", page_id="p001", root=workspace)


def test_cli_render_exits_nonzero_when_a_page_fails(planned_book, workspace):
    from bookfactory.cli.main import main

    book = Book.load("test-book", workspace)
    spec = book.read_page_spec("p001")
    spec["copy"]["body"] = ["A very long paragraph. " * 400]
    book.write_page_spec("p001", spec)
    book.save()

    code = main(["--root", str(workspace), "render", "test-book", "--submit"])
    assert code == 1


def test_every_page_type_has_a_template():
    from bookfactory.render.templates import page_template_names
    from bookfactory.qa.content import REQUIRED_COPY

    templates = set(page_template_names())
    assert set(REQUIRED_COPY) <= templates, "a page type with no template cannot be produced"
