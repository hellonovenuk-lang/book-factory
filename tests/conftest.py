"""Shared fixtures.

The fixtures build real book projects on disk - real files, real checksums,
real rendered PDFs - because the failures this system exists to prevent are
all filesystem failures. A mocked filesystem would test nothing worth testing.
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import pytest

from bookfactory.core import api
from bookfactory.core.book import ASSET, PAGE, Book

REPO_ROOT = Path(__file__).resolve().parent.parent

BRIEF = """# Book Brief - Test Book

## The idea in one sentence

A small book used to prove the production system works.

## Target buyer

Somebody running the test suite, and nobody else at all.

## Gift recipient

Nobody. This book is never printed and never given to anyone.

## Recognition trigger

1. Runs the tests before committing.
2. Reads the failure output rather than re-running it.
3. Keeps fixtures small enough to stay fast.
4. Deletes tests that no longer prove anything.
5. Writes the assertion before the fix.

## Humour angle

The frame is a field manual, held straight throughout.

## Commercial rationale

None. This is a fixture and has no commercial purpose whatsoever.

## Constraints

Must stay small so the suite stays quick.
"""

VOICE = """# Voice Bible - Test Book

## The voice in one paragraph

Flat, institutional and entirely serious about a trivial subject. Short
sentences because the form is short. No warmth that is not accidental.

## Rules - do

- Be specific about ordinary objects.
- Keep the register intact.

## Rules - do not

- No motivational language.
- No corporate register.

## Banned phrases

- little did he know

## Spelling and conventions

British English throughout.
"""

SAMPLE = """# Writing Sample - Test Book

## Sample one

The subject is observed holding a mug and looking at a garden. No plan results
from this. The behaviour is recorded and no action is taken.

## Sample two

Inspectors should record the severity score and proceed without discussing it
with the subject.
"""

MANUSCRIPT = """# Test Book

## Chapter 1 - The Assessment

The subject acquired a garden without wishing to. This manual applies to that
person and to nobody who wanted one. Every garden arrives carrying the previous
owner's opinions, and those opinions are now the subject's problem.

The subject is observed at the window each morning, holding a mug. This is not
planning. No plan results from it. The garden has been winning since March and
shows no sign of stopping.

## Chapter 2 - The Response

The manual does not recommend enthusiasm. Enthusiasm produces a raised bed in
month two and a covered raised bed in month nine. The minimum viable response
is the smallest action that keeps the situation from becoming visible to the
neighbours, performed at a frequency the subject will not honour.
"""

VISUAL = """# Visual Bible - Test Book

## Medium and rendering

Ink line with flat matte fills on visible paper tone. No gradients.

## Line style

Single weight, confident, closing outlines.

## Palette

Warm paper, near-black ink, one brick accent. Nothing outside this set.

## Characters

### subject - The Subject

- **Clothing:** Fleece gilet, checked shirt, indoor shoes worn outdoors.
- **Never:** Shown smiling. Shown without the mug.

## Prohibited deviations

- No text of any kind inside generated artwork.
- No new palette colours.
"""


def make_image(path: Path, size: tuple[int, int] = (1800, 1350), seed: int = 1) -> Path:
    """A deterministic stand-in for artwork.

    Every seed produces visibly different pixels, because two references that
    are byte-identical are a real finding and the fixtures must not trip it.
    """
    import random

    from PIL import Image, ImageDraw

    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, (251, 248, 241))
    draw = ImageDraw.Draw(image)
    rng = random.Random(seed)
    for _ in range(6):
        x = rng.randrange(0, size[0] - 200)
        y = rng.randrange(0, size[1] - 200)
        draw.rectangle([x, y, x + rng.randrange(40, 200), y + rng.randrange(40, 200)],
                       fill=(140, 59, 46), outline=(28, 26, 23))
    image.save(path, "PNG")
    return path


def force_remove(path: Path) -> None:
    for item in path.rglob("*"):
        if item.is_file():
            os.chmod(item, stat.S_IWUSR | stat.S_IRUSR)
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "books").mkdir()
    yield tmp_path
    for candidate in (tmp_path / "books").glob("*"):
        if candidate.is_dir():
            force_remove(candidate)


@pytest.fixture
def new_book(workspace: Path) -> Book:
    """A book that has just been created and nothing else."""
    api.create_book("Test Book", book_id="test-book", root=workspace,
                    idea="A small book used to prove the production system works.")
    return Book.load("test-book", workspace)


@pytest.fixture
def locked_book(workspace: Path) -> Book:
    """A book with concept, voice, manuscript and visual style all locked."""
    api.create_book("Test Book", book_id="test-book", root=workspace,
                    idea="A small book used to prove the production system works.")
    book = Book.load("test-book", workspace)
    book.paths.brief_file.write_text(BRIEF, encoding="utf-8")
    book.paths.voice_bible.write_text(VOICE, encoding="utf-8")
    book.paths.writing_sample_file.write_text(SAMPLE, encoding="utf-8")
    book.paths.manuscript_file.write_text(MANUSCRIPT, encoding="utf-8")
    book.paths.visual_bible.write_text(VISUAL, encoding="utf-8")
    book.save()

    api.lock("test-book", "concept", root=workspace, by="tester")
    api.lock("test-book", "voice", root=workspace, by="tester")
    api.lock("test-book", "manuscript", root=workspace, by="tester")

    book = Book.load("test-book", workspace)
    staging = workspace / "staging"
    for index, item in enumerate(book.reference_set()["required"]):
        asset_id = item["asset_id"]
        api.register_asset("test-book", asset_id, root=workspace, kind=item["kind"],
                           title=item["title"], description=item["description"])
        art = make_image(staging / f"{asset_id}.png", (1800, 1800), seed=index)
        api.submit_asset("test-book", asset_id, art, kind=ASSET, root=workspace)
        api.approve("test-book", asset_id, kind=ASSET, root=workspace, by="tester")

    api.lock("test-book", "visual", root=workspace, by="tester")
    return Book.load("test-book", workspace)


PAGE_PLAN = [
    {"title": "The Assessment", "type": "chapter_opener", "chapter": 1,
     "spec": {"copy": {"eyebrow": "Chapter one", "heading": "The Assessment",
                       "subheading": "In which the garden is measured.",
                       "body": ["Every garden arrives with the previous owner's opinions "
                                "still in it, and they are now the subject's problem."]}}},
    {"title": "Scope of the manual", "type": "editorial_illustration", "chapter": 1,
     "required_assets": ["fig-scope"],
     "spec": {"copy": {"eyebrow": "1.1", "heading": "Scope",
                       "body": ["This manual applies to any person who acquired a garden "
                                "without wishing to."],
                       "caption": "Fig. 1.1 - The garden, as inherited."},
              "illustration": {"asset_id": "fig-scope", "concept": "A neglected garden.",
                               "placement": "top", "embedded_text": False}}},
    {"title": "Severity assessment", "type": "checklist", "chapter": 1,
     "spec": {"copy": {"eyebrow": "1.2", "heading": "Severity assessment",
                       "items": [{"label": "There is a bag of compost in the car."},
                                 {"label": "The shed came before the spade."}],
                       "footnote": "Two points is within normal limits."}}},
    {"title": "Closing note", "type": "quote", "chapter": 1,
     "spec": {"copy": {"quote": "The garden will outlast the subject's interest in it.",
                       "attribution": "Section 2.6"}}},
]


@pytest.fixture
def planned_book(locked_book: Book, workspace: Path) -> Book:
    """A locked book with a four page plan, specs written, artwork approved."""
    pages = [{k: v for k, v in page.items() if k != "spec"} for page in PAGE_PLAN]
    api.plan_pages("test-book", pages, root=workspace)

    book = Book.load("test-book", workspace)
    for index, page in enumerate(PAGE_PLAN, start=1):
        book.write_page_spec(f"p{index:03d}", page["spec"])
    book.save()

    staging = workspace / "staging"
    api.register_asset("test-book", "fig-scope", root=workspace, kind="illustration",
                       title="Scope", page_id="p002")
    art = make_image(staging / "fig-scope.png", (1800, 1350), seed=9)
    api.submit_asset("test-book", "fig-scope", art, kind=ASSET, root=workspace)
    api.approve("test-book", "fig-scope", kind=ASSET, root=workspace, by="tester")
    return Book.load("test-book", workspace)


@pytest.fixture
def produced_book(planned_book: Book, workspace: Path) -> Book:
    """Every page rendered and approved - ready to assemble."""
    for index in range(1, len(PAGE_PLAN) + 1):
        page_id = f"p{index:03d}"
        api.render("test-book", page_id=page_id, submit=True, root=workspace)
        api.approve("test-book", page_id, kind=PAGE, root=workspace, by="tester")
    return Book.load("test-book", workspace)


@pytest.fixture(autouse=True)
def _quiet_weasyprint():
    """WeasyPrint logs every CSS property it does not implement. Those exist for
    the Chromium backend and are harmless; the noise buries real failures."""
    import logging

    logger = logging.getLogger("weasyprint")
    previous = logger.level
    logger.setLevel(logging.ERROR)
    yield
    logger.setLevel(previous)
