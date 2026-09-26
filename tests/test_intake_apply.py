"""Task 18.2: confirming intake applies its big decisions to the book.

See PLAN.md task 18.2. `title`, `print_colour` and `cover_style` are applied
by `_complete_intake`; `main_character_details` is left untouched here (task
18.3 uses it in writing tasks).
"""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import api, cover
from bookfactory.core.book import Book

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
    "cover_style": "let_book_factory_decide",
    "production_policy": "checkpointed",
}


def _start(workspace: Path, book_id: str = "golf") -> str:
    return api.create_from_idea(IDEA, root=workspace, book_id=book_id)["book_id"]


def test_title_is_applied_and_audited(workspace: Path) -> None:
    book_id = _start(workspace)
    original_title = Book.load(book_id, workspace).state.title
    answers = dict(FULL_ANSWERS)
    api.submit_intake(book_id, answers, root=workspace)

    book = Book.load(book_id, workspace)
    assert book.state.title == "The Golf Addict's Guide"

    events = api.audit_history(book_id, root=workspace, event="intake_title_set")
    assert len(events) == 1
    assert events[0]["previous_title"] == original_title
    assert events[0]["title"] == "The Golf Addict's Guide"


def test_title_unchanged_when_answer_matches_is_not_logged(workspace: Path) -> None:
    book_id = _start(workspace)
    current_title = Book.load(book_id, workspace).state.title
    answers = dict(FULL_ANSWERS, title=current_title)
    api.submit_intake(book_id, answers, root=workspace)

    assert api.audit_history(book_id, root=workspace, event="intake_title_set") == []


def test_black_and_white_sets_colour_false_and_is_audited(workspace: Path) -> None:
    book_id = _start(workspace)
    answers = dict(FULL_ANSWERS, print_colour="black_and_white")
    api.submit_intake(book_id, answers, root=workspace)

    book = Book.load(book_id, workspace)
    assert book.state.format.colour is False

    events = api.audit_history(book_id, root=workspace, event="intake_print_colour_set")
    assert len(events) == 1
    assert events[0]["previous_colour"] is True
    assert events[0]["colour"] is False


def test_colour_sets_colour_true_and_is_audited(workspace: Path) -> None:
    book_id = _start(workspace)
    book = Book.load(book_id, workspace)
    book.state.format.colour = False
    book.save()

    answers = dict(FULL_ANSWERS, print_colour="colour")
    api.submit_intake(book_id, answers, root=workspace)

    book = Book.load(book_id, workspace)
    assert book.state.format.colour is True

    events = api.audit_history(book_id, root=workspace, event="intake_print_colour_set")
    assert len(events) == 1
    assert events[0]["previous_colour"] is False
    assert events[0]["colour"] is True


def test_big_lettering_records_text_only_cover_for_confirmed_operator(workspace: Path) -> None:
    book_id = _start(workspace)
    draft_answers = {k: v for k, v in FULL_ANSWERS.items()
                     if k not in ("production_policy", "cover_style")}
    api.draft_intake(book_id, draft_answers, by="chatgpt", unclear=["cover_style"],
                     root=workspace)
    api.confirm_intake(book_id, by="Kieran", policy="checkpointed",
                       changes={"cover_style": "big_lettering"}, root=workspace)

    data = cover.load(Book.load(book_id, workspace))
    assert data["artwork"] == cover.TEXT_ONLY
    assert data["approved"] is None

    events = api.audit_history(book_id, root=workspace, event="cover_artwork_mode_set")
    assert len(events) == 1
    assert events[0]["mode"] == cover.TEXT_ONLY
    assert events[0]["by"] == "Kieran"
    assert "big_lettering" in events[0]["reason"]


def test_big_lettering_by_names_the_uncorrected_operator(workspace: Path) -> None:
    book_id = _start(workspace)
    answers = dict(FULL_ANSWERS, cover_style="big_lettering")
    api.submit_intake(book_id, answers, root=workspace)

    events = api.audit_history(book_id, root=workspace, event="cover_artwork_mode_set")
    assert len(events) == 1
    assert events[0]["by"] == "operator (intake questionnaire)"


def test_picture_and_let_book_factory_decide_leave_artwork_unchanged(workspace: Path) -> None:
    for suffix, style in (("picture", "picture"), ("decide", "let_book_factory_decide")):
        book_id = _start(workspace, book_id=f"golf-{suffix}")
        answers = dict(FULL_ANSWERS, cover_style=style)
        api.submit_intake(book_id, answers, root=workspace)

        book = Book.load(book_id, workspace)
        assert cover.load(book)["artwork"] == cover.NATIVE
        assert api.audit_history(book_id, root=workspace,
                                 event="cover_artwork_mode_set") == []


def test_apply_tolerates_answers_that_predate_the_new_keys(workspace: Path) -> None:
    """A caller whose answers predate title/print_colour/cover_style (an older
    intake submission, or a future loosening of validate_answers) must not
    make `_apply_intake_answers` itself fall over or change anything."""
    from bookfactory.core.api import _apply_intake_answers

    book_id = _start(workspace)
    book = Book.load(book_id, workspace)
    original_title = book.state.title
    answers = {k: v for k, v in FULL_ANSWERS.items()
              if k not in ("title", "print_colour", "cover_style", "main_character_details")}

    _apply_intake_answers(book, answers, by="operator (intake questionnaire)")

    assert book.state.title == original_title
    assert book.state.format.colour is True
    assert cover.load(book)["artwork"] == cover.NATIVE
    assert api.audit_history(book_id, root=workspace,
                             event="intake_title_set") == []
    assert api.audit_history(book_id, root=workspace,
                             event="intake_print_colour_set") == []
    assert api.audit_history(book_id, root=workspace,
                             event="cover_artwork_mode_set") == []
