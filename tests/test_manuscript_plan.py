"""Parsing a manuscript into page-plan pages (`bookfactory.core.manuscript_plan`).

Small hand-written manuscripts prove each mapping. The Golf Addict's Guide's
real manuscript is parsed and compared, page by page, with its hand-checked
71-page plan, so a regression in any convention shows up as a named
difference.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from bookfactory.core import api, schema
from bookfactory.core.manuscript_plan import parse_manuscript, parse_manuscript_file
from bookfactory.core.models import PageRecord
from bookfactory.render.renderer import build_context
from bookfactory.render.templates import render_page_template

REPO = Path(__file__).resolve().parents[1]
GOLF = REPO / "books" / "golf-addicts-guide-to-family-reintegration"
GOLF_MANUSCRIPT = GOLF / "manuscript" / "manuscript.md"

KNOWN_BLOCKS = {"prose", "ticks", "checklist", "score", "lines", "table", "casenote",
                "gauge", "cycle", "cutout", "signature"}


def _full_spec(spec: dict, number: int = 1) -> dict:
    """The spec as plan_pages/write_page_spec would complete it."""
    return {**spec, "schema_version": "1.0", "book_id": "test-book",
            "page_id": f"p{number:03d}"}


def _assert_valid(pages: list[dict]) -> None:
    for number, page in enumerate(pages, start=1):
        assert set(page) == {"title", "type", "chapter", "spec"}
        spec = page["spec"]
        assert set(spec) == {"type", "title", "chapter", "copy", "illustration"}
        assert (spec["type"], spec["title"], spec["chapter"]) == \
            (page["type"], page["title"], page["chapter"])
        schema.validate("page-spec", _full_spec(spec, number), context=page["title"])
        if page["type"] == "activity":
            assert spec["copy"]["blocks"], page["title"]
            for block in spec["copy"]["blocks"]:
                assert block["type"] in KNOWN_BLOCKS, (page["title"], block)


def _page(result: dict, title: str) -> dict:
    matches = [page for page in result["pages"] if page["title"] == title]
    assert len(matches) == 1, [page["title"] for page in result["pages"]]
    return matches[0]


def _parse(text: str) -> dict:
    result = parse_manuscript(text)
    _assert_valid(result["pages"])
    return result


# ---------------------------------------------------------------------------
# Front matter, chapters, openers


FRONT = """# A Book

> The manuscript. Locked by `bookfactory lock manuscript`, which snapshots this
> file into `manuscript/versions/` and checksums it.

<!-- Notes for the page plan. -->

## Front matter

### Title page

The Book of Things

A subtitle that explains the book.

### A note on the text

First paragraph of the note.

Second paragraph, with a line
that wraps.

### Contents

- Chapter 1 - Beginnings
- Chapter 2 - Endings

## Chapter 1 - Beginnings

### Chapter opener

Chapter 1 - Beginnings

A standfirst.

The first body paragraph.

The second body paragraph.

[Picture: chapter opener. A man at a gate.]

## Back matter

### About the author

She lives by the sea.
"""


def test_front_matter_title_page_contents_and_text_pages():
    result = _parse(FRONT)
    assert result["warnings"] == []
    types = [(p["type"], p["title"], p["chapter"]) for p in result["pages"]]
    assert types == [
        ("front_matter", "Title page", None),
        ("text_illustration", "A note on the text", None),
        ("contents", "Contents", None),
        ("chapter_opener", "Chapter 1 - Beginnings", 1),
        ("text_illustration", "About the author", None),
    ]
    title = _page(result, "Title page")["spec"]["copy"]
    assert title == {"heading": "The Book of Things",
                     "subheading": "A subtitle that explains the book."}
    note = _page(result, "A note on the text")["spec"]["copy"]
    assert note == {"heading": "A note on the text",
                    "body": ["First paragraph of the note.",
                             "Second paragraph, with a line that wraps."]}
    contents = _page(result, "Contents")["spec"]["copy"]
    assert contents["items"] == ["Chapter 1 - Beginnings", "Chapter 2 - Endings"]


def test_chapter_opener_takes_eyebrow_heading_standfirst_body_and_picture():
    text = """## Stage One: Arrival

### Chapter opener

Stage One: Arrival

Induction for returning golfers.

Welcome home.

Take your cap off.

[Picture: chapter opener. Dave on the doorstep with his golf bag.]
"""
    page = _parse(text)["pages"][0]
    assert page["type"] == "chapter_opener" and page["chapter"] == 1
    assert page["spec"]["copy"] == {
        "eyebrow": "Stage One", "heading": "Arrival",
        "subheading": "Induction for returning golfers.",
        # Not split: fitting an overflowing opener is a later step.
        "body": ["Welcome home.", "Take your cap off."],
    }
    assert page["spec"]["illustration"] == {
        "asset_id": "art-stage-01-opener",
        "concept": "Dave on the doorstep with his golf bag.",
        "placement": "inline",
    }


def test_opener_asset_id_follows_the_chapter_word_and_number():
    result = _parse(FRONT)
    opener = _page(result, "Chapter 1 - Beginnings")["spec"]
    assert opener["illustration"]["asset_id"] == "art-chapter-01-opener"
    assert opener["copy"]["eyebrow"] is None
    assert opener["copy"]["heading"] == "Chapter 1 - Beginnings"
    assert opener["copy"]["subheading"] == "A standfirst."


def test_chapters_are_numbered_in_order_and_back_matter_has_none():
    text = """## Part One: Up

### Going up

Up we go.

## Part Two: Down

### Going down

Down we come.

## Back matter

### Thanks

Thank you.
"""
    result = _parse(text)
    assert [(p["title"], p["chapter"]) for p in result["pages"]] == [
        ("Going up", 1), ("Going down", 2), ("Thanks", None)]


def test_an_opener_without_a_picture_is_planned_with_a_warning():
    text = """## Stage One: Arrival

### Chapter opener

Stage One: Arrival

A standfirst.
"""
    result = _parse(text)
    assert result["pages"][0]["spec"]["illustration"] is None
    assert len(result["warnings"]) == 1
    assert "Chapter opener" in result["warnings"][0]
    assert "no [Picture" in result["warnings"][0]


# ---------------------------------------------------------------------------
# Ordinary sections


def test_plain_paragraphs_make_a_text_page_with_bold_lead_ins_set_plain():
    text = """## Stage One: Arrival

### Your household

Some members have changed.

**Sue.** Your wife and case sponsor.

**The dog.** Answers to Biscuit.
"""
    page = _parse(text)["pages"][0]
    assert page["type"] == "text_illustration"
    assert page["spec"]["copy"] == {
        "heading": "Your household",
        "body": ["Some members have changed.", "Sue. Your wife and case sponsor.",
                 "The dog. Answers to Biscuit."],
    }


def test_a_section_with_a_case_note_and_a_list_becomes_an_activity_page():
    text = """## Stage One: Arrival

### Why you are here

Your family has applied for your return.

> **Case notes (Sue), Day 1.** Said he'd be back by one.
> Back at twenty to seven.

Families discuss the following.

- Other people's holidays.
- Whether the car is making
  a noise.
"""
    page = _parse(text)["pages"][0]
    assert page["type"] == "activity"
    copy = page["spec"]["copy"]
    assert "panel_number" not in copy and copy["heading"] == "Why you are here"
    assert copy["blocks"] == [
        {"type": "prose", "text": "Your family has applied for your return."},
        {"type": "casenote", "label": "Case notes (Sue), Day 1",
         "text": "Said he'd be back by one. Back at twenty to seven."},
        {"type": "prose", "text": "Families discuss the following."},
        {"type": "prose", "text": ["• Other people's holidays.",
                                   "• Whether the car is making a noise."]},
    ]


# ---------------------------------------------------------------------------
# Numbered panels


def test_an_assessment_panel_has_ticks_and_a_score():
    text = """## Stage One: Arrival

### No. 01 · Assessment: Initial assessment

Award yourself one point for each statement that is true.

1. You have gone out for "a quick nine".
2. You have practised your swing
   with an umbrella.

Score: ____ out of 2
"""
    page = _parse(text)["pages"][0]
    assert (page["type"], page["title"]) == ("activity", "Initial assessment")
    assert page["spec"]["copy"] == {
        "panel_number": "No. 01", "panel_kind": "Assessment",
        "heading": "Initial assessment",
        "instructions": "Award yourself one point for each statement that is true.",
        "blocks": [
            {"type": "ticks", "items": ["You have gone out for \"a quick nine\".",
                                        "You have practised your swing with an umbrella."]},
            {"type": "score", "label": "Score", "out_of": 2},
        ],
    }


def test_checklist_signature_and_write_in_lines():
    text = """## Stage Three: The Household

### No. 09 · Checklist: Jobs I can do

Tick each job you have done.

- [ ] Put the bins out.
- [ ] Hoovered, including under things.

Countersigned (Sue): ______________________

Total hours missing: ______

Signed: ______________________ Witnessed (Sue): ______________________
"""
    blocks = _parse(text)["pages"][0]["spec"]["copy"]["blocks"]
    assert blocks == [
        {"type": "checklist", "items": ["Put the bins out.", "Hoovered, including under things."]},
        {"type": "signature", "fields": ["Countersigned (Sue)"]},
        {"type": "lines", "count": 1, "label": "Total hours missing"},
        {"type": "signature", "fields": ["Signed", "Witnessed (Sue)"]},
    ]


def test_numbered_blanks_become_write_in_lines():
    text = """## Stage Eight: Graduation

### No. 24 · Worksheet: Promises

Write three promises.

1. _________________________________________
2. _________________________________________
3. _________________________________________

Signed: ______________________ Date: ______________________
"""
    blocks = _parse(text)["pages"][0]["spec"]["copy"]["blocks"]
    assert blocks == [{"type": "lines", "count": 3},
                      {"type": "signature", "fields": ["Signed", "Date"]}]


def test_tables_keep_blank_write_in_rows_and_tick_cells():
    text = """## Stage Four: Time

### No. 12 · Worksheet: Which comes first?

Tick the one that matters more.

| Option A | Option B |
| --- | --- |
| [ ] Your anniversary | [ ] The midweek medal |
| | |
| | |

If you ticked column B, see Stage Seven.
"""
    copy = _parse(text)["pages"][0]["spec"]["copy"]
    assert copy["instructions"] == "Tick the one that matters more."
    assert copy["blocks"] == [
        {"type": "table", "headers": ["Option A", "Option B"],
         "rows": [["[ ] Your anniversary", "[ ] The midweek medal"], ["", ""], ["", ""]]},
        {"type": "prose", "text": "If you ticked column B, see Stage Seven."},
    ]


def test_a_comparison_table_keeps_its_blank_corner_header():
    text = """## Stage Six: Holidays

### No. 18 · Comparison: Golf holiday or family holiday?

| | Golf holiday | Family holiday |
| --- | --- | --- |
| Getting up | 6am | Twenty to six |
"""
    page = _parse(text)["pages"][0]
    assert "instructions" not in page["spec"]["copy"]
    assert page["spec"]["copy"]["blocks"] == [
        {"type": "table", "headers": ["", "Golf holiday", "Family holiday"],
         "rows": [["Getting up", "6am", "Twenty to six"]]}]


def test_a_cut_out_card():
    text = """## Stage Two: Communication

### No. 05 · Cut-out card: Emergency putt card

[Dashed cut-out card.]

**I am about to mention the 7th.**

Instead, I will say:
"Anyway, how are you?"

Keep this card in your wallet.
"""
    copy = _parse(text)["pages"][0]["spec"]["copy"]
    assert copy["panel_kind"] == "Cut-out card"
    assert copy["blocks"] == [{
        "type": "cutout", "heading": "I am about to mention the 7th.",
        "text": ["Instead, I will say: \"Anyway, how are you?\"",
                 "Keep this card in your wallet."],
    }]


def test_a_quiz_with_lettered_answers():
    text = """## Stage Two: Communication

### No. 04 · Quiz: What was the question?

Circle the answer the family is looking for.

1. "How was your day?"
   a) "Good, thanks."
   b) "Well, the 7th..."
2. "Did you remember the bread?"
   a) "Yes."
   b) "Keith was on the
   practice green."
"""
    copy = _parse(text)["pages"][0]["spec"]["copy"]
    assert copy["instructions"] == "Circle the answer the family is looking for."
    assert copy["blocks"] == [
        {"type": "prose", "text": "1. \"How was your day?\""},
        {"type": "checklist", "items": ["a) \"Good, thanks.\"", "b) \"Well, the 7th...\""]},
        {"type": "prose", "text": "2. \"Did you remember the bread?\""},
        {"type": "checklist", "items": ["a) \"Yes.\"", "b) \"Keith was on the practice green.\""]},
    ]


def test_typeset_gauge_and_cycle_diagrams():
    text = """## Stage Four: Time

### Reading your score

[Typeset diagram: a severity gauge running from 0 to 10.]

- **0 to 2:** Wrong house.
- **3 to 6:** Moderate.
- **10:** Report immediately.

### The quick nine

A quick nine is five hours.

[Typeset diagram: the quick nine cycle: "Just popping out" to "Eighteen" to "Car park debrief", and back to "Just popping out".]
"""
    result = _parse(text)
    assert result["warnings"] == []
    gauge = _page(result, "Reading your score")["spec"]["copy"]["blocks"]
    assert gauge == [{"type": "gauge", "bands": [
        {"range": "0 to 2", "label": "Wrong house."},
        {"range": "3 to 6", "label": "Moderate."},
        {"range": "10", "label": "Report immediately."}]}]
    cycle = _page(result, "The quick nine")["spec"]["copy"]["blocks"]
    assert cycle == [
        {"type": "prose", "text": "A quick nine is five hours."},
        {"type": "cycle", "steps": ["Just popping out", "Eighteen", "Car park debrief"]},
    ]


def test_a_one_paragraph_section_before_a_panel_becomes_its_intro():
    text = """## Stage One: Arrival

### Your welcome pack

On arrival you will be issued with the following.

### No. 03 · Checklist: Arrival kit

- [ ] One front door key.

### Packing

Pack clothes first.

Then the suncream.

### No. 17 · Checklist: The packing list

- [ ] Swimming shorts.
"""
    result = _parse(text)
    assert [p["title"] for p in result["pages"]] == [
        "Arrival kit", "Packing", "The packing list"]
    kit = _page(result, "Arrival kit")["spec"]["copy"]
    assert kit["eyebrow"] == "Your welcome pack"
    assert kit["body"] == ["On arrival you will be issued with the following."]
    assert "eyebrow" not in _page(result, "The packing list")["spec"]["copy"]


def test_a_certificate():
    text = """## Stage Eight: Graduation

### Certificate of Reintegration

[Bordered full page with signature lines.]

Certificate of Reintegration

This is to certify that

______________________

has completed the Programme.

Signed (Case sponsor): ______________________

Date: ______________________
"""
    page = _parse(text)["pages"][0]
    assert page["type"] == "certificate"
    assert page["spec"]["copy"] == {
        "heading": "Certificate of Reintegration",
        "body": ["This is to certify that", "______________________",
                 "has completed the Programme."],
        "items": ["Signed (Case sponsor)", "Date"],
    }


# ---------------------------------------------------------------------------
# Nothing is dropped silently


UNMAPPED = """Some stray notes before any chapter.

## Stage One: Arrival

A paragraph straight under the chapter heading.

### Odd things

[Typeset diagram: a Venn diagram of golf and family.]

[Picture: Dave asleep on the sofa.]

[Printed upside down.]

> A quotation with no bold label.

### Gauge without bands

[Typeset diagram: a severity gauge.]

Just a paragraph.

### Empty

### Contents

Some words that are not a list.

- Entry one
"""


def test_unmapped_text_is_kept_on_a_page_and_named_in_a_warning():
    result = _parse(UNMAPPED)
    warnings = result["warnings"]
    joined = "\n".join(warnings)
    for expected in ("before the first ## heading", "under the ## heading",
                     "unrecognised typeset diagram", "picture outside a chapter opener",
                     "unrecognised layout note", "no bold label",
                     "a gauge diagram needs", "section is empty",
                     "contents page holds only a list"):
        assert expected in joined, expected
    assert len(warnings) == 9
    # Each warning names the section it is about.
    assert any('"### Odd things" in "## Stage One: Arrival"' in w for w in warnings)

    everything = json.dumps([p["spec"]["copy"] for p in result["pages"]])
    for words in ("Some stray notes", "straight under the chapter heading",
                  "Venn diagram", "Dave asleep on the sofa", "Printed upside down",
                  "A quotation with no bold label", "a severity gauge",
                  "Some words that are not a list"):
        assert words in everything, words
    odd = _page(result, "Odd things")
    assert odd["spec"]["illustration"] is None  # a stray picture is never planned as artwork


# ---------------------------------------------------------------------------
# The Golf Addict's Guide


# Pages in the real plan that exist only because a chapter opener's body
# overflowed its page and was split by hand. The parser puts the whole body on
# the opener; splitting is the fit-testing step's job.
GOLF_SPLIT_PAGES = [
    ("text_illustration", "Stage One: Arrival (introduction)", 1),
    ("text_illustration", "Stage Seven: Relapse Prevention (introduction)", 7),
    ("text_illustration", "Stage Eight: Graduation (introduction)", 8),
]


def _golf_manifest() -> list[dict]:
    return json.loads((GOLF / "pages" / "manifest.json").read_text(encoding="utf-8"))["pages"]


@pytest.fixture(scope="module")
def golf() -> dict:
    return parse_manuscript_file(GOLF_MANUSCRIPT)


def test_golf_manuscript_parses_to_the_real_plan_except_the_opener_splits(golf):
    assert golf["warnings"] == []
    _assert_valid(golf["pages"])
    real = [(p["type"], p["title"], p["chapter"]) for p in _golf_manifest()]
    ours = [(p["type"], p["title"], p["chapter"]) for p in golf["pages"]]

    expected = [page for page in real if page not in GOLF_SPLIT_PAGES]
    assert len(expected) == len(real) - len(GOLF_SPLIT_PAGES)
    # The one chapter difference: the real plan filed the back matter's
    # "About this programme" under chapter 8; the parser gives back matter no
    # chapter, so its running head is the book title, not "Graduation".
    about = ("text_illustration", "About this programme", 8)
    expected[expected.index(about)] = ("text_illustration", "About this programme", None)
    assert ours == expected


def test_golf_openers_carry_the_whole_body_and_the_picture(golf):
    real_specs = {p["title"]: json.loads((GOLF / p["spec"]).read_text(encoding="utf-8"))
                  for p in _golf_manifest()}
    for page in golf["pages"]:
        if page["type"] != "chapter_opener":
            continue
        real = real_specs[page["title"]]
        ours = page["spec"]
        for key in ("eyebrow", "heading", "subheading"):
            assert ours["copy"][key] == real["copy"][key]
        split = real_specs.get(f"{page['title']} (introduction)")
        real_body = real["copy"]["body"] + (split["copy"]["body"] if split else [])
        assert ours["copy"]["body"] == real_body
        assert ours["illustration"]["asset_id"] == real["illustration"]["asset_id"]
        assert ours["illustration"]["concept"] == real["illustration"]["concept"]


def test_golf_copy_matches_the_real_specs_where_they_made_the_same_choice(golf):
    """Every page's copy equals the hand-checked spec, except the few pages
    where the parser deliberately does better (listed with the reason)."""
    # "My triggers" and "Relapse diary" used to differ too (the old script
    # dropped their blank write-in rows); the Golf pages were fixed to match.
    deliberate = {
        # The first quiz question stays in the blocks, not the instructions.
        "What was the question?",
        # The cycle diagram stays where the manuscript puts it, after the prose.
        "The quick nine",
    }
    real_specs = {p["title"]: json.loads((GOLF / p["spec"]).read_text(encoding="utf-8"))
                  for p in _golf_manifest()}
    differing = {page["title"] for page in golf["pages"]
                 if page["type"] != "chapter_opener"
                 and page["spec"]["copy"] != real_specs[page["title"]]["copy"]}
    assert differing == deliberate


def test_no_golf_manuscript_word_is_lost(golf):
    text = GOLF_MANUSCRIPT.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    words = set()
    for line in text.splitlines()[6:]:  # after the title and the template note
        stripped = line.strip()
        if stripped.startswith("#") or (stripped.startswith("[") and stripped.endswith("]")):
            continue
        words.update(re.findall(r"[A-Za-z0-9£']+", stripped))
    output = json.dumps([p["spec"] for p in golf["pages"]], ensure_ascii=False)
    found = set(re.findall(r"[A-Za-z0-9£']+", output))
    assert words - found == set()


def test_golf_plan_is_accepted_by_plan_pages(new_book, workspace, golf):
    result = api.plan_pages("test-book", golf["pages"], root=workspace)
    assert result["total"] == len(golf["pages"]) == 68
    assert result["specs"] == 68
    assert sorted(result["assets_registered"]) == [
        f"art-stage-{n:02d}-opener" for n in range(1, 9)]


def test_every_golf_page_renders_to_html(new_book, golf):
    for number, page in enumerate(golf["pages"], start=1):
        spec = _full_spec({**page["spec"], "illustration": None}, number)
        record = PageRecord(page_id=spec["page_id"], sequence=number, title=page["title"],
                            type=page["type"], chapter=page["chapter"], printed_number=number)
        html = render_page_template(page["type"], build_context(new_book, record, spec))
        assert "<html" in html, page["title"]
