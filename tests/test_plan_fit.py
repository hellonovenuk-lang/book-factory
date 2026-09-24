"""`bookfactory.render.fit.fit_pages`.

Fits a page plan (task 17.1's output) against every render engine before it
is loaded into a book, splitting an overflowing `chapter_opener` or
`text_illustration` page into an opener/lead page plus continuation pages -
the same shape the Golf Addict's Guide's p005/p006 were split into by hand -
and naming anything else that overflows instead of splitting it.
"""

from __future__ import annotations

import pytest

from bookfactory.render import backends
from bookfactory.render.fit import fit_pages

AVAILABLE_ENGINES = backends.available_backends()

#: Padding long enough that a handful of paragraphs overflow a 6x9 page, and
#: short enough to keep the test suite fast.
FILLER = ("Sentence number filler word count padding text here to occupy space on the "
         "page and see how much room a single paragraph really needs when set at "
         "normal body size.")


def _paragraphs(n: int) -> list[str]:
    return [f"Paragraph {i}. {FILLER}" for i in range(n)]


def test_a_short_page_fits(locked_book):
    pages = [{"title": "Stage One: Arrival", "type": "chapter_opener", "chapter": 1,
             "spec": {"type": "chapter_opener", "chapter": 1, "title": "Stage One: Arrival",
                      "copy": {"eyebrow": "Stage One", "heading": "Arrival",
                              "subheading": "Induction for returning golfers.",
                              "body": ["Welcome home. Please leave your clubs at the door."]},
                      "illustration": None}}]

    result = fit_pages(locked_book, pages)

    assert len(result["report"]) == 1
    entry = result["report"][0]
    assert entry["status"] == "fits"
    assert entry["index"] == 0
    assert entry["title"] == "Stage One: Arrival"
    for engine in AVAILABLE_ENGINES:
        assert engine in entry["detail"]
    assert result["pages"] == pages


def test_an_overflowing_opener_splits_keeping_every_paragraph_in_order(locked_book):
    body = _paragraphs(8)  # overflows a chapter_opener at 6 in both engines (see task notes)
    pages = [{"title": "Stage One: Arrival", "type": "chapter_opener", "chapter": 1,
             "spec": {"type": "chapter_opener", "chapter": 1, "title": "Stage One: Arrival",
                      "copy": {"eyebrow": "Stage One", "heading": "Arrival",
                              "subheading": "Induction for returning golfers.", "body": body},
                      "illustration": None}}]

    result = fit_pages(locked_book, pages)

    assert len(result["report"]) == 1
    entry = result["report"][0]
    assert entry["status"] == "split"
    assert entry["index"] == 0

    out = result["pages"]
    assert len(out) >= 2, "the opener should have split into at least two pages"

    # The first part keeps the opener's own type, title and chapter.
    assert out[0]["type"] == "chapter_opener"
    assert out[0]["title"] == "Stage One: Arrival"
    assert out[0]["chapter"] == 1

    # Every later part is a "(continued)" text_illustration page, same chapter.
    for part in out[1:]:
        assert part["type"] == "text_illustration"
        assert part["chapter"] == 1
        assert "(continued" in part["title"]
        assert part["spec"]["illustration"] is None

    # No paragraph was dropped, reordered, or split mid-paragraph.
    rebuilt: list[str] = []
    for part in out:
        rebuilt.extend(part["spec"]["copy"]["body"])
    assert rebuilt == body

    # Every part actually fits, in every engine that ran.
    for part in out:
        title = part["title"]
        sub = fit_pages(locked_book, [{"title": title, "type": part["type"],
                                       "chapter": part["chapter"], "spec": part["spec"]}])
        assert sub["report"][0]["status"] == "fits", f"split part {title!r} still overflows"


def test_an_overflowing_activity_page_is_reported_too_long_not_split(locked_book):
    items = [f"Statement number {i} about something specific that happened this year."
            for i in range(20)]  # overflows in both engines (see task notes)
    pages = [{"title": "Initial assessment", "type": "activity", "chapter": 1,
             "spec": {"type": "activity", "chapter": 1, "title": "Initial assessment",
                      "copy": {"panel_number": "No. 01", "panel_kind": "Assessment",
                              "heading": "Initial assessment",
                              "blocks": [{"type": "ticks", "items": items}]},
                      "illustration": None}}]

    result = fit_pages(locked_book, pages)

    assert len(result["report"]) == 1
    entry = result["report"][0]
    assert entry["status"] == "too_long"
    assert "activity" in entry["detail"]
    # Left exactly as given: not split into extra pages.
    assert result["pages"] == pages


def test_fit_pages_writes_nothing_under_the_book(locked_book):
    body = _paragraphs(8)
    pages = [{"title": "Stage One: Arrival", "type": "chapter_opener", "chapter": 1,
             "spec": {"type": "chapter_opener", "chapter": 1, "title": "Stage One: Arrival",
                      "copy": {"eyebrow": "Stage One", "heading": "Arrival", "body": body},
                      "illustration": None}}]
    before = {p.relative_to(locked_book.paths.root) for p in locked_book.paths.root.rglob("*")
             if p.is_file()}
    asset_ids_before = {a.asset_id for a in locked_book.registry.assets}

    fit_pages(locked_book, pages)

    after = {p.relative_to(locked_book.paths.root) for p in locked_book.paths.root.rglob("*")
            if p.is_file()}
    assert after == before, "fit_pages must not write anything under the book folder"
    assert {a.asset_id for a in locked_book.registry.assets} == asset_ids_before, (
        "any placeholder illustration stub must be removed again, not left on the registry")


def test_fit_pages_registers_no_placeholder_when_a_real_asset_is_already_approved(locked_book):
    """An illustration already approved in the book (e.g. a locked reference) is
    used as-is; fit_pages must not shadow it with a placeholder."""
    pages = [{"title": "Chapter opener example", "type": "chapter_opener", "chapter": 1,
             "spec": {"type": "chapter_opener", "chapter": 1, "title": "Chapter opener example",
                      "copy": {"heading": "Chapter opener example"},
                      "illustration": {"asset_id": "ref-character-main",
                                       "placement": "full_page"}}}]

    result = fit_pages(locked_book, pages)

    assert result["report"][0]["status"] == "fits"
    assert "placeholder" not in result["report"][0]["detail"]


@pytest.mark.skipif(not AVAILABLE_ENGINES, reason="no render backend is available")
def test_report_names_not_checked_engines_are_recorded(locked_book):
    pages = [{"title": "Stage One: Arrival", "type": "chapter_opener", "chapter": 1,
             "spec": {"type": "chapter_opener", "chapter": 1, "title": "Stage One: Arrival",
                      "copy": {"heading": "Arrival", "body": ["Welcome home."]},
                      "illustration": None}}]
    only_first = fit_pages(locked_book, pages, backends=[AVAILABLE_ENGINES[0]])
    assert AVAILABLE_ENGINES[0] in only_first["report"][0]["detail"]


def test_fit_pages_reports_not_checked_when_no_backend_is_available(locked_book, monkeypatch):
    pages = [{"title": "Stage One: Arrival", "type": "chapter_opener", "chapter": 1,
             "spec": {"type": "chapter_opener", "chapter": 1, "title": "Stage One: Arrival",
                      "copy": {"heading": "Arrival", "body": ["Welcome home."]},
                      "illustration": None}}]
    result = fit_pages(locked_book, pages, backends=[])
    assert result["report"][0]["status"] == "not_checked"
    assert result["pages"] == pages


def test_an_opener_can_hand_its_only_paragraph_to_the_next_page(locked_book):
    # The Golf Addict's Guide's Stage Seven and Eight openers: one paragraph too
    # long to sit under the picture, so the opener keeps an empty body.
    paragraph = " ".join([FILLER] * 10)
    pages = [{"title": "Stage Seven: Relapse", "type": "chapter_opener", "chapter": 7,
              "spec": {"type": "chapter_opener", "chapter": 7, "title": "Stage Seven: Relapse",
                       "copy": {"eyebrow": "Stage Seven", "heading": "Relapse",
                                "subheading": "Keeping him home.", "body": [paragraph]},
                       "illustration": {"asset_id": "art-stage-07-opener", "concept": "x",
                                        "placement": "inline"}}}]

    result = fit_pages(locked_book, pages, backends=AVAILABLE_ENGINES)

    assert [e["status"] for e in result["report"]] == ["split"]
    opener, continued = result["pages"]
    assert opener["type"] == "chapter_opener"
    assert opener["spec"]["copy"]["body"] == []
    assert opener["spec"]["illustration"]["asset_id"] == "art-stage-07-opener"
    assert continued["type"] == "text_illustration"
    assert continued["spec"]["copy"]["body"] == [paragraph]
