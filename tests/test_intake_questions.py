"""The four big-decision intake questions added in Phase 18 (task 18.1):
title, main_character_details, print_colour, cover_style.

See `PLAN.md` for why: on the Golf Addict's Guide these all changed late,
costing rework and picture credits, so intake asks them up front.
"""

from __future__ import annotations

from bookfactory.core.intake import (
    COVER_STYLES,
    PRINT_COLOURS,
    QUESTIONNAIRE,
    questionnaire_text,
    validate_answers,
    validate_draft,
)

GOOD_ANSWERS = {
    "idea": "A fake rehabilitation manual for men addicted to golf.",
    "title": "The Golf Addict's Guide to Recovery",
    "buyer": "His wife.",
    "recipient": "Dave, aged 52.",
    "recognition_trigger": "He irons his golf trousers before he irons his shirts.",
    "humour_level": "medium",
    "visual_feel": "classic_editorial_caricature",
    "colour_direction": "muted",
    "main_character": "user_description",
    "main_character_details": "Dave, 52, married to Sue, two grown-up kids, a flat cap.",
    "length": "80",
    "must_include": "the electric trolley",
    "must_avoid": "anything about his golf handicap",
    "print_colour": "colour",
    "cover_style": "picture",
    "production_policy": "autonomous",
}


def _keys() -> list[str]:
    return [question["key"] for question in QUESTIONNAIRE]


def test_print_colours_and_cover_styles_export_the_stated_choices() -> None:
    assert PRINT_COLOURS == ("colour", "black_and_white")
    assert COVER_STYLES == ("big_lettering", "picture", "let_book_factory_decide")


def test_the_four_questions_exist_in_the_stated_order_positions() -> None:
    keys = _keys()
    assert keys.index("title") == keys.index("idea") + 1
    assert keys.index("main_character_details") == keys.index("main_character") + 1
    assert keys.index("print_colour") == keys.index("colour_direction") + 1
    assert keys.index("cover_style") == keys.index("print_colour") + 1
    assert keys[-1] == "production_policy"


def test_valid_answers_pass() -> None:
    assert validate_answers(GOOD_ANSWERS) == []


def test_missing_title_fails() -> None:
    answers = dict(GOOD_ANSWERS)
    del answers["title"]
    problems = validate_answers(answers)
    assert any("'title'" in problem for problem in problems)


def test_empty_title_fails() -> None:
    answers = dict(GOOD_ANSWERS, title="   ")
    problems = validate_answers(answers)
    assert any("'title'" in problem for problem in problems)


def test_missing_main_character_details_fails() -> None:
    answers = dict(GOOD_ANSWERS)
    del answers["main_character_details"]
    problems = validate_answers(answers)
    assert any("'main_character_details'" in problem for problem in problems)


def test_empty_main_character_details_fails() -> None:
    answers = dict(GOOD_ANSWERS, main_character_details="")
    problems = validate_answers(answers)
    assert any("'main_character_details'" in problem for problem in problems)


def test_bad_print_colour_fails() -> None:
    answers = dict(GOOD_ANSWERS, print_colour="sepia")
    problems = validate_answers(answers)
    assert any("'print_colour'" in problem for problem in problems)


def test_bad_cover_style_fails() -> None:
    answers = dict(GOOD_ANSWERS, cover_style="holographic")
    problems = validate_answers(answers)
    assert any("'cover_style'" in problem for problem in problems)


def test_a_draft_listing_the_new_keys_as_unclear_validates() -> None:
    answers = dict(GOOD_ANSWERS)
    del answers["production_policy"]
    unclear = ["title", "main_character_details", "print_colour", "cover_style"]
    for key in unclear:
        del answers[key]
    assert validate_draft(answers, unclear) == []


def test_questionnaire_text_shows_the_new_questions() -> None:
    text = questionnaire_text()
    assert "exact title" in text
    assert "family" in text
    assert "Print colour" in text
    assert "Cover style" in text
