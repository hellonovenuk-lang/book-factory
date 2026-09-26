"""Task instructions carry the big decisions fixed at intake (task 18.3).

`bookfactory next` / `task` must tell a writing agent, in the task's own
instructions, which decisions the operator already fixed at intake - so the
brief, the visual bible, the character references and the cover follow them
instead of drifting, as happened on the Golf Addict's Guide.
"""

from __future__ import annotations

from reportlab.pdfgen import canvas

from bookfactory.core import api, clock, tasks
from bookfactory.core.book import Book
from tests.conftest import BRIEF, MANUSCRIPT, SAMPLE, VOICE


def _complete_intake(book, answers: dict) -> None:
    book.state.intake.required = True
    book.state.intake.completed = True
    book.state.intake.completed_at = clock.timestamp()
    book.state.intake.answers = dict(answers)
    book.save()


FULL_ANSWERS = {
    "idea": "A small book used to prove the production system works.",
    "title": "The Exact Cover Title",
    "buyer": "A tester.",
    "recipient": "A tester.",
    "recognition_trigger": "Runs the tests before committing.",
    "humour_level": "mild",
    "visual_feel": "let_book_factory_decide",
    "colour_direction": "let_book_factory_decide",
    "main_character": "user_description",
    "main_character_details": "Dave, 45, married to Sue, two kids under seven, a flat cap.",
    "length": "system_decides",
    "must_include": "A scene at the allotment.",
    "must_avoid": "none",
    "print_colour": "black_and_white",
    "cover_style": "big_lettering",
    "production_policy": "checkpointed",
}


def _interior(book, pages: int = 4) -> None:
    path = book.paths.interior_pdf
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(432, 648))
    for _ in range(pages):
        pdf.showPage()
    pdf.save()


def test_a_book_without_intake_shows_no_decisions(new_book):
    task = tasks._brief_task(new_book)
    assert task is not None
    assert "Fixed at intake" not in task.instructions


def test_brief_task_shows_decisions_fixed_at_intake(new_book):
    _complete_intake(new_book, FULL_ANSWERS)
    task = tasks._brief_task(new_book)
    assert task is not None
    assert "Fixed at intake - do not change without the operator" in task.instructions
    assert 'Title: exactly "The Exact Cover Title"' in task.instructions
    assert "Dave, 45, married to Sue" in task.instructions
    assert "Print colour: black and white" in task.instructions
    assert "Cover style: big lettering" in task.instructions
    assert "Must include: A scene at the allotment." in task.instructions
    #: must_avoid was answered "none" - it must not be listed
    assert "Must avoid" not in task.instructions


def test_visual_bible_task_shows_decisions_fixed_at_intake(workspace):
    #: brief, voice and manuscript locked; visual bible still has its default
    #: TODOs, so the visual-bible authoring task is next.
    api.create_book("Test Book", policy="checkpointed", book_id="test-book", root=workspace,
                    idea="A small book used to prove the production system works.")
    book = Book.load("test-book", workspace)
    book.paths.brief_file.write_text(BRIEF, encoding="utf-8")
    book.paths.voice_bible.write_text(VOICE, encoding="utf-8")
    book.paths.writing_sample_file.write_text(SAMPLE, encoding="utf-8")
    book.paths.manuscript_file.write_text(MANUSCRIPT, encoding="utf-8")
    book.save()
    api.lock("test-book", "concept", root=workspace, by="tester")
    api.lock("test-book", "voice", root=workspace, by="tester")
    api.lock("test-book", "manuscript", root=workspace, by="tester")

    book = Book.load("test-book", workspace)
    _complete_intake(book, FULL_ANSWERS)
    book = Book.load("test-book", workspace)
    task = tasks._visual_reference_task(book)
    assert task is not None
    assert task.task_id.endswith("visual-bible")
    assert "Fixed at intake - do not change without the operator" in task.instructions
    assert "Dave, 45, married to Sue" in task.instructions
    assert "Cover style: big lettering" in task.instructions


def test_cover_direction_task_shows_decisions_fixed_at_intake(new_book, workspace):
    _interior(new_book)
    _complete_intake(new_book, FULL_ANSWERS)
    book = Book.load("test-book", workspace)
    task = tasks._cover_task(book)
    assert task is not None
    assert task.task_id.endswith("cover-direction")
    assert "Fixed at intake - do not change without the operator" in task.instructions
    assert "Cover style: big lettering" in task.instructions
    assert "Print colour: black and white" in task.instructions
