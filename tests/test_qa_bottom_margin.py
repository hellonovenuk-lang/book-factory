"""Body text below the bottom margin is a defect, even when every word is present.

On the padel book five chapter openers printed their last line over the page
number; the fit test, QA and preflight all passed them. `bottom_margin_overflow_words`
is the shared check; `qa.technical` reports it as `technical.bottom_margin`.
"""

from __future__ import annotations

import pymupdf

from bookfactory.core.book import Book
from bookfactory.qa import technical
from bookfactory.render.fit import bottom_margin_overflow_words
from bookfactory.render.renderer import geometry


def _pdf(path, book, *, body_bottom_in_from_foot: float) -> None:
    """A one-page PDF at the book's trim with a body line and a folio."""
    geo = geometry(book, side="recto")
    width = geo["page_width_in"] * 72
    height = geo["page_height_in"] * 72
    doc = pymupdf.open()
    page = doc.new_page(width=width, height=height)
    page.insert_text((72, 100), "A heading near the top", fontsize=11)
    page.insert_text((72, height - body_bottom_in_from_foot * 72), "watch for it.", fontsize=11)
    page.insert_text((width - 72, height - 0.4 * 72), "14", fontsize=8)  # the folio
    doc.save(str(path))
    doc.close()


def test_text_below_the_bottom_margin_is_found(produced_book, workspace, tmp_path):
    book = Book.load("test-book", workspace)
    margin = geometry(book, side="recto")["margin_bottom_in"]
    bad = tmp_path / "bad.pdf"
    _pdf(bad, book, body_bottom_in_from_foot=margin - 0.25)
    words = bottom_margin_overflow_words(book, bad)
    assert "watch" in words
    assert "14" not in words  # the folio is not body text


def test_text_above_the_bottom_margin_passes(produced_book, workspace, tmp_path):
    book = Book.load("test-book", workspace)
    margin = geometry(book, side="recto")["margin_bottom_in"]
    good = tmp_path / "good.pdf"
    _pdf(good, book, body_bottom_in_from_foot=margin + 0.5)
    assert bottom_margin_overflow_words(book, good) == []


def test_qa_reports_no_bottom_margin_errors_on_a_clean_book(produced_book, workspace):
    book = Book.load("test-book", workspace)
    result = technical.check(book)
    codes = [finding.code for finding in result.findings]
    assert "technical.bottom_margin" not in codes
