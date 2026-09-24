"""The `activity` page type: a numbered panel built from typeset blocks.

Every block (tick boxes, score boxes, write-in lines, fill-in tables, case
notes, the gauge and the cycle diagrams, cut-out cards, signature lines) is
real type from the page spec, so every word must be findable in the PDF text
in both render backends.

The page manifest does not list `activity` as a page type yet, so these
tests render from a spec directly rather than through a planned page.
"""

from __future__ import annotations

import pytest

from bookfactory.core.errors import RenderError
from bookfactory.core.models import PageRecord
from bookfactory.qa import content
from bookfactory.render import backends
from bookfactory.render.renderer import _normalise, build_context
from bookfactory.render.templates import render_page_template

BACKENDS = [
    pytest.param("weasyprint", marks=pytest.mark.skipif(
        not backends.weasyprint_available(), reason="WeasyPrint is not installed")),
    pytest.param("chromium", marks=pytest.mark.skipif(
        not backends.chromium_available(), reason="no Chromium binary")),
]

# Every block type, split over two panels so each fits one 6x9 page.
PANEL_ONE = {
    "eyebrow": "Stage One",
    "heading": "Arrival kit and household",
    "subheading": "A test of the furniture",
    "panel_number": "No. 07",
    "panel_kind": "Assessment",
    "instructions": "Award yourself one point for each statement that is true.",
    "body": ["The Programme asks you to complete the following in pen, at the kitchen table."],
    "blocks": [
        {"type": "prose", "text": "Read each statement slowly before ticking anything."},
        {"type": "ticks", "start": 3,
         "items": ["You have gone out for a quick nine and come back in the dark.",
                   "You have mentioned the seventh hole at a christening."]},
        {"type": "score", "label": "Points", "out_of": 10},
        {"type": "checklist", "items": ["One front door key, behind the ball marker.",
                                        "One pair of indoor shoes without spikes."]},
        {"type": "lines", "count": 2, "label": "What did Poppy do this year?"},
        {"type": "table", "headers": ["Family member", "Name", "Seen today"],
         "widths": ["40%", "35%", "25%"],
         "rows": [["Your wife", "", "[ ]"], ["The dog", "Biscuit", "[ ] by the bins"]]},
        {"type": "casenote", "label": "Case notes (Sue), Day 3",
         "text": "He asked where we keep the Calpol at two in the morning."},
    ],
    "footnote": "Sue will check your answers.",
}

PANEL_TWO = {
    "heading": "The quick nine cycle",
    "panel_number": "No. 08",
    "panel_kind": "Diagram",
    "blocks": [
        {"type": "cycle", "steps": ["Just popping out", "Might as well play eighteen",
                                    "Quick one in the bar", "Car park debrief",
                                    "Back home, surprised anyone noticed"]},
        {"type": "gauge", "bands": [{"range": "0 to 2", "label": "Wrong house entirely"},
                                    {"range": "3 to 6", "label": "Moderate case"},
                                    {"range": "7 to 9", "label": "Severe case"},
                                    {"range": "10", "label": "Report immediately"}]},
        {"type": "cutout", "heading": "Keep in wallet",
         "text": ["Hear the question.", "Answer it briefly and ask one back."]},
        {"type": "signature", "fields": ["Participant", "Case sponsor"]},
    ],
}

# A typical Golf Addict's Guide activity: ten statements and a score box.
GOLF_ASSESSMENT = {
    "panel_number": "No. 01", "panel_kind": "Assessment",
    "heading": "Initial assessment",
    "instructions": "Award yourself one point for each statement that is true. "
                    "Sue will check your answers.",
    "blocks": [
        {"type": "ticks", "items": [
            "You have gone out for \"a quick nine\" and come back in the dark.",
            "You have practised your swing with an umbrella in the queue at the post office, "
            "and the queue moved back.",
            "You know the date of next year's club medal, and not the date of your wedding "
            "anniversary.",
            "You checked the forecast for Saturday's tee time and did not notice it was also "
            "your daughter's fourth birthday party.",
            "There is a golf bag in the downstairs loo, and you consider this a storage "
            "solution.",
            "You have watched golf on the telly on a Sunday afternoon, having played golf all "
            "Sunday morning, and fallen asleep before the back nine.",
            "You have mentioned the 7th hole at a christening.",
            "You have shared your views on the new committee with somebody who is not a member "
            "of the club, such as the man who came to read the meter.",
            "You chose the family holiday in the Algarve because there \"happened to be\" a "
            "course nearby. There were three. You played all of them.",
            "You are reading this list and still think the 7th was a genuinely unlucky lip-out.",
        ]},
        {"type": "score", "out_of": 10},
    ],
}

# A typical Golf worksheet: a seven-row fill-in table.
GOLF_WORKSHEET = {
    "panel_number": "No. 02", "panel_kind": "Worksheet",
    "heading": "Who lives here?",
    "instructions": "Fill in the table without looking at the fridge, a phone or a "
                    "Christmas card.",
    "blocks": [
        {"type": "table",
         "headers": ["Family member", "Name", "Age", "Something they did this year"],
         "widths": ["26%", "22%", "12%", "40%"],
         "rows": [[who, "", "", ""] for who in (
             "Your wife", "Your son", "Your daughter", "The dog", "Your mother-in-law",
             "The neighbour", "The window cleaner")]},
    ],
    "footnote": "If you have written \"the little one\" or \"mate\" in the name column, "
                "that counts as blank.",
}


def _page(copy: dict) -> PageRecord:
    return PageRecord(page_id="p010", sequence=10, title=copy.get("heading") or "Activity",
                      type="activity", chapter=1, printed_number=10)


def _html(book, copy: dict) -> str:
    spec = {"page_id": "p010", "type": "activity", "title": "Activity", "copy": copy}
    return render_page_template("activity", build_context(book, _page(copy), spec))


def _render(book, copy: dict, backend: str, tmp_path):
    destination = tmp_path / f"activity-{backend}.pdf"
    backends.render_html_to_pdf(_html(book, copy), destination,
                                base_url=book.paths.root, backend=backend)
    return destination


def _pdf_pages_text(path) -> list[str]:
    import pymupdf

    with pymupdf.open(str(path)) as doc:
        return [page.get_text() for page in doc]


def _copy_strings(copy: dict) -> list[str]:
    """Every word of copy the page must carry, tick-box markers removed."""
    strings = []
    for key in ("eyebrow", "heading", "subheading", "panel_number", "panel_kind",
                "instructions", "footnote"):
        if copy.get(key):
            strings.append(copy[key])
    body = copy.get("body") or []
    strings.extend([body] if isinstance(body, str) else body)
    for text in content._block_text(copy.get("blocks") or []):
        text = text[3:] if text.startswith("[ ]") else text
        if text.strip():
            strings.append(text)
    return strings


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("copy", [PANEL_ONE, PANEL_TWO, GOLF_ASSESSMENT, GOLF_WORKSHEET],
                         ids=["blocks-1", "blocks-2", "golf-ticks-score", "golf-table"])
def test_every_word_of_an_activity_is_set_as_real_type(new_book, tmp_path, backend, copy):
    pages = _pdf_pages_text(_render(new_book, copy, backend, tmp_path))
    assert len(pages) == 1, f"the activity overflowed onto {len(pages)} pages"
    haystack = _normalise(pages[0])
    missing = [text for text in _copy_strings(copy) if _normalise(text) not in haystack]
    assert not missing, f"{backend} rendered without: {missing}"


def test_every_block_type_is_covered_by_the_render_tests():
    used = {block["type"] for copy in (PANEL_ONE, PANEL_TWO) for block in copy["blocks"]}
    assert used == {"prose", "ticks", "checklist", "score", "lines", "table", "casenote",
                    "gauge", "cycle", "cutout", "signature"}


def test_blocks_render_in_order_with_their_furniture(new_book):
    html = _html(new_book, PANEL_ONE)
    assert "No. 07 · Assessment" in html
    assert html.index("Read each statement slowly") < html.index("quick nine") \
        < html.index("One front door key") < html.index("Calpol")
    assert '<td class="blk-ticks__n">3</td>' in html, "ticks honour their start number"
    assert html.count('class="blk-lines__rule"') == 2
    assert '<td class="blk-table__blank"></td>' in html, "an empty cell is a write-in cell"
    assert html.count('class="blk-table__tick"') == 2
    assert "/ 10" in html and "Points" in html


def test_diagrams_are_typeset_never_images(new_book):
    html = _html(new_book, PANEL_TWO)
    panel = html[html.index('class="activity'):]
    assert "<img" not in panel
    assert html.count('class="blk-cycle__step"') == 5
    assert 'class="blk-cycle__return"' in html, "the cycle loops back to step 1"
    shades = [part.split(")")[0] for part in html.split("background-color: rgb(")[1:]]
    levels = [int(shade.split(",")[0]) for shade in shades]
    assert len(levels) == 4 and levels == sorted(levels, reverse=True), \
        "gauge segments grade from light to dark"


def test_copy_is_escaped_not_trusted_as_html(new_book):
    copy = {"heading": "Keith's <b>takeaway</b>",
            "blocks": [{"type": "ticks", "items": ["<script>x</script> & friends"]},
                       {"type": "table", "headers": ["<i>Who</i>"], "rows": [["<u>Sue</u>"]]}]}
    html = _html(new_book, copy)
    assert "<b>takeaway</b>" not in html and "&lt;b&gt;takeaway&lt;/b&gt;" in html
    assert "<script>" not in html and "&amp; friends" in html
    assert "<i>Who</i>" not in html and "<u>Sue</u>" not in html


def test_an_unknown_block_type_fails_loudly_naming_it(new_book):
    copy = {"heading": "Broken", "blocks": [{"type": "prose", "text": "Fine."},
                                            {"type": "scorecard", "items": []}]}
    with pytest.raises(RenderError) as caught:
        _html(new_book, copy)
    message = str(caught.value)
    assert "Unknown activity block type 'scorecard'" in message
    assert "gauge" in message, "the error lists the block types that do exist"


def _qa_activity(book, monkeypatch, copy: dict):
    """Content QA over the planned book with p003 turned into an activity page."""
    page = book.manifest.get("p003")
    monkeypatch.setattr(page, "type", "activity")
    real_read = book.read_page_spec

    def read(page_id):
        if page_id == "p003":
            return {"page_id": "p003", "type": "activity", "title": page.title, "copy": copy}
        return real_read(page_id)

    monkeypatch.setattr(book, "read_page_spec", read)
    return [f for f in content.check(book).findings if f.page_id == "p003"]


def test_required_copy_rejects_an_activity_with_no_blocks(planned_book, monkeypatch):
    assert content.REQUIRED_COPY["activity"] == ["blocks"]
    findings = _qa_activity(planned_book, monkeypatch, {"heading": "Empty panel", "blocks": []})
    assert any(f.code == "content.missing_copy" and "'blocks'" in f.message for f in findings)


def test_content_qa_reads_the_words_inside_blocks(planned_book, monkeypatch):
    copy = {"heading": "Nested copy",
            "blocks": [{"type": "table", "headers": ["Stage"],
                        "rows": [["Little did he know the 7th was waiting."]]},
                       {"type": "gauge", "bands": [{"range": "0", "label": "Time to leverage the"
                                                                         " back nine"}]},
                       {"type": "cycle", "steps": ["TODO write this step"]}]}
    codes = {f.code for f in _qa_activity(planned_book, monkeypatch, copy)}
    assert "content.banned_phrase" in codes, "a banned phrase inside a table cell is caught"
    assert "content.ai_tell" in codes, "corporate vocabulary inside a gauge band is caught"
    assert "content.placeholder" in codes, "placeholder copy inside a cycle step is caught"
    assert "content.missing_copy" not in codes


def test_block_structure_is_not_read_as_copy():
    text = content._copy_text({"blocks": [{"type": "lines", "count": 3},
                                          {"type": "table", "widths": ["30%"], "rows": []}]})
    assert text == ""


def test_the_render_copy_check_covers_text_inside_blocks():
    from bookfactory.render.renderer import _flatten_copy

    copy = {"heading": "Garage inventory", "blocks": [
        {"type": "ticks", "items": ["Golf bags in the downstairs loo"]},
        {"type": "table", "headers": ["Item", "Number"],
         "rows": [["[ ] Putters behind the sofa", ""]], "widths": ["70%", "30%"]},
        {"type": "score", "out_of": 10},
    ]}
    strings = _flatten_copy(copy)
    assert "Golf bags in the downstairs loo" in strings
    assert "Putters behind the sofa" in strings   # the "[ ]" tick box is not copy
    assert "70%" not in strings                   # structure keys are not copy


def test_the_copy_check_reads_ligatures_as_their_letters():
    """Chromium sets "ff" in "official" as one ligature glyph; the words are
    still all there, so the render check must not report them missing."""
    assert _normalise("An oﬀicial proﬁle") == _normalise("An official profile")


def test_an_activity_without_a_panel_number_is_a_plain_text_page(new_book):
    """Only numbered activities are boxed; a prose section that needs a block
    (a case note, a table) renders as an ordinary page with no box or tab."""
    plain = _html(new_book, {"heading": "Why you are here", "blocks": [
        {"type": "prose", "text": "Your family has applied for your return."},
        {"type": "casenote", "label": "Case notes (Sue), Day 1", "text": "Back at twenty to seven."},
    ]})
    assert 'class="activity activity--plain"' in plain
    assert 'class="activity__tab"' not in plain
    boxed = _html(new_book, {"panel_number": "No. 01", "heading": "Initial assessment",
                             "blocks": [{"type": "score", "out_of": 10}]})
    assert 'class="activity activity--tabbed"' in boxed
    assert 'class="activity activity--plain"' not in boxed
