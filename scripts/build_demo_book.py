#!/usr/bin/env python3
"""Build the synthetic demo book from scratch.

Run from the repository root:

    python scripts/build_demo_book.py

It walks the entire production process - brief, locks, references, page plan,
specs, artwork, rendering, approval, a revision, QA, assembly, review,
preflight and the full-wrap print cover - so the fixture in `books/demo-book/`
is always reproducible rather than a directory somebody once hand-made.

The script plays the operator as well as the producing agent, so it runs the
commands that need the operator's authority (`approve`, `lock`, `cover
approve`, `advance`). Those steps are labelled as the operator's. An agent
driving a real book must not copy them - see AGENTS.md sections 3 and 9a.

This script is a fixture builder. It is not part of Book Factory and nothing in
`bookfactory/` imports it.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import demo_art  # noqa: E402
import demo_content as content  # noqa: E402

from bookfactory.core import api, cover  # noqa: E402
from bookfactory.core.book import ASSET, PAGE, Book  # noqa: E402
from bookfactory.core.paths import BookPaths  # noqa: E402

BOOK_ID = "demo-book"
TITLE = "The Reluctant Gardener"
OPERATOR = "demo-operator"
AUTHOR = "The Garden Standards Office"
BACK_COPY = ("You did not ask for a garden. The garden did not ask for you. This "
             "field manual sets out the minimum standard of care expected of the "
             "subject, and the tests the subject will fail.")


#: The finished book is left with exactly one open illustration task, so a fresh
#: ChatGPT session can be handed the repository and asked to produce real
#: artwork against the locked references. The approved artwork stays canonical
#: throughout, so the book remains assemblable while the smoke test runs.
SMOKE_TEST_ASSET = "p007-window"

#: Pixel sizes chosen so every image clears 300 DPI at its printed size.
ART_SIZES = {
    "full_page": (1800, 1500),
    "top": (1800, 1350),
    "bottom": (1800, 1350),
    "spot": (900, 900),
    "reference": (1800, 1800),
}

REFERENCE_DESCRIPTIONS = {
    "ref-character-main": "The Subject: rear and three-quarter rear view, fleece gilet, mug.",
    "ref-character-support": "The Inspector: a clipboard, a pen and a pair of hands. No face.",
    "ref-layout-chapter-opener": "Approved chapter opener layout at 6x9.",
    "ref-page-editorial": "Approved internal editorial page at 6x9.",
    "ref-page-diagnostic": "Approved structured-content page: checklist and test styling.",
    "ref-palette": "Palette swatches and the type hierarchy on one sheet.",
}


def log(message: str) -> None:
    print(f"  {message}")


def step(number: int, message: str) -> None:
    print(f"\n[{number:02d}] {message}")


def build(*, clean: bool = True) -> Book:
    paths = BookPaths.for_book(BOOK_ID, REPO_ROOT)
    if clean and paths.root.exists():
        _force_remove(paths.root)

    step(1, "Create the project")
    api.create_book(TITLE, book_id=BOOK_ID, root=REPO_ROOT, trim="6x9", colour=True,
                    target_page_count=24,
                    subtitle="A field manual issued to persons who did not want one",
                    idea="A straight-faced field manual for someone who inherited a garden.")
    book = Book.load(BOOK_ID, REPO_ROOT)
    log(f"created {book.paths.root}")

    step(2, "Write the brief, concept, audience and outline")
    book.paths.brief_file.write_text(content.BRIEF, encoding="utf-8")
    book.paths.concept_file.write_text(content.CONCEPT, encoding="utf-8")
    book.paths.audience_file.write_text(content.AUDIENCE, encoding="utf-8")
    book.paths.outline_file.write_text(content.OUTLINE, encoding="utf-8")
    book.save()

    step(3, "Lock the concept")
    api.lock(BOOK_ID, "concept", by=OPERATOR, root=REPO_ROOT)

    step(4, "Write the voice bible and the calibration sample, then lock the voice")
    book = Book.load(BOOK_ID, REPO_ROOT)
    book.paths.voice_bible.write_text(content.VOICE_BIBLE, encoding="utf-8")
    book.paths.writing_sample_file.write_text(content.WRITING_SAMPLE, encoding="utf-8")
    book.save()
    api.lock(BOOK_ID, "voice", version="v1", by=OPERATOR, root=REPO_ROOT)

    step(5, "Write the manuscript and lock it")
    book = Book.load(BOOK_ID, REPO_ROOT)
    book.paths.manuscript_file.write_text(content.MANUSCRIPT, encoding="utf-8")
    book.save()
    api.lock(BOOK_ID, "manuscript", version="v1", by=OPERATOR, root=REPO_ROOT)

    step(6, "Write the visual bible and build the locked reference set")
    book = Book.load(BOOK_ID, REPO_ROOT)
    book.paths.visual_bible.write_text(content.VISUAL_BIBLE, encoding="utf-8")
    book.save()

    for item in book.reference_set()["required"]:
        asset_id = item["asset_id"]
        api.register_asset(BOOK_ID, asset_id, root=REPO_ROOT, kind=item["kind"],
                           title=item["title"],
                           description=REFERENCE_DESCRIPTIONS.get(asset_id, item["description"]))
        width, height = ART_SIZES["reference"]
        draft = _make_art(asset_id, width, height)
        api.submit_asset(BOOK_ID, asset_id, draft, kind=ASSET, root=REPO_ROOT,
                         source="demo-fixture", note="Synthetic placeholder reference.")
        api.approve(BOOK_ID, asset_id, kind=ASSET, by=OPERATOR, root=REPO_ROOT,
                    note="Reference approved for the locked set.")
        log(f"reference approved: {asset_id}")

    step(7, "Lock the visual style - mass page production is now permitted")
    api.lock(BOOK_ID, "visual", version="v1", by=OPERATOR, root=REPO_ROOT)

    step(8, "Create the page plan and write every page spec")
    pages = [{"title": page["title"], "type": page["type"], "chapter": page.get("chapter"),
              "required_assets": page.get("assets", [])} for page in content.PAGES]
    result = api.plan_pages(BOOK_ID, pages, root=REPO_ROOT, front_matter_pages=2)
    log(f"{result['total']} pages planned")

    book = Book.load(BOOK_ID, REPO_ROOT)
    for index, page in enumerate(content.PAGES, start=1):
        page_id = f"p{index:03d}"
        book.write_page_spec(page_id, page["spec"])
    book.save()
    log(f"{len(content.PAGES)} page specs written")

    step(9, "Generate, submit and approve the illustration artwork")
    book = Book.load(BOOK_ID, REPO_ROOT)
    for index, page in enumerate(content.PAGES, start=1):
        for asset_id in page.get("assets", []):
            illustration = page["spec"]["illustration"]
            api.register_asset(BOOK_ID, asset_id, root=REPO_ROOT, kind="illustration",
                               title=page["title"], description=illustration["concept"],
                               page_id=f"p{index:03d}",
                               characters=illustration.get("characters"),
                               references=illustration.get("references"))
            width, height = ART_SIZES[illustration.get("placement", "full_page")]
            draft = _make_art(asset_id, width, height)
            api.submit_asset(BOOK_ID, asset_id, draft, kind=ASSET, root=REPO_ROOT,
                             source="demo-fixture")
            api.approve(BOOK_ID, asset_id, kind=ASSET, by=OPERATOR, root=REPO_ROOT)
            log(f"artwork approved: {asset_id}")

    step(10, "Render every page deterministically and approve it")
    for index in range(1, len(content.PAGES) + 1):
        page_id = f"p{index:03d}"
        api.render(BOOK_ID, page_id=page_id, submit=True, root=REPO_ROOT)
        api.approve(BOOK_ID, page_id, kind=PAGE, by=OPERATOR, root=REPO_ROOT)
    log(f"{len(content.PAGES)} pages rendered and approved")

    step(11, "Demonstrate the revision workflow on an already-approved page")
    book = Book.load(BOOK_ID, REPO_ROOT)
    target = next(p for p in book.manifest if p.title == content.REVISION_PAGE_TITLE)
    api.revise(BOOK_ID, target.page_id, kind=PAGE, root=REPO_ROOT,
               reason="Operator wants the arithmetic spelled out.", by=OPERATOR)
    log(f"revision opened on {target.page_id}; v1 stays canonical until v2 is approved")

    book = Book.load(BOOK_ID, REPO_ROOT)
    spec = book.read_page_spec(target.page_id)
    spec["copy"]["body"].append(
        "One film is ninety minutes. The subject is invited to draw the obvious "
        "conclusion without assistance from this manual.")
    book.write_page_spec(target.page_id, spec)
    book.save()
    api.render(BOOK_ID, page_id=target.page_id, submit=True, root=REPO_ROOT)
    api.approve(BOOK_ID, target.page_id, kind=PAGE, by=OPERATOR, root=REPO_ROOT,
                note="Revision approved.")
    log(f"{target.page_id} v2 approved; v1 archived to pages/approved/_history/")

    step(12, "Run QA")
    report = api.qa(BOOK_ID, root=REPO_ROOT)
    log(f"QA status: {report['summary']['status']} "
        f"({report['summary']['errors']} errors, {report['summary']['warnings']} warnings)")
    for layer in report["layers"]:
        for finding in layer["findings"]:
            if finding["level"] in ("error", "warning"):
                log(f"  {layer['layer']}/{finding['level']}: {finding['message']}")

    step(13, "Assemble the interior")
    record = api.assemble(BOOK_ID, root=REPO_ROOT)
    log(f"{record['output']} - {record['page_count']} pages, "
        f"sha256 {record['output_sha256'][:16]}...")

    step(14, "Generate review output")
    review = api.review(BOOK_ID, root=REPO_ROOT)
    for name, path in sorted(review["outputs"].items()):
        log(f"{name}: {path}")

    step(15, "Run KDP preflight")
    preflight = api.preflight(BOOK_ID, root=REPO_ROOT)
    log(f"preflight: {preflight['status']} "
        f"({preflight['failures']} failures, {preflight['warnings']} warnings)")
    for check in preflight["checks"]:
        if check["status"] != "pass":
            log(f"  {check['check']}: {check['message']}")

    step(16, "Produce, approve and preflight the full-wrap print cover")
    _build_cover()

    step(17, "Mark release ready (operator's step)")
    if preflight["status"] != "fail":
        api.advance(BOOK_ID, "release_ready", by=OPERATOR, root=REPO_ROOT)

    step(18, "Leave one illustration task open for the cross-agent smoke test")
    api.revise(BOOK_ID, SMOKE_TEST_ASSET, kind=ASSET, root=REPO_ROOT, by=OPERATOR,
               reason=("Cross-agent visual smoke test: the subject's posture reads as "
                       "relaxed rather than resigned."))
    task = api.next_task(BOOK_ID, root=REPO_ROOT)
    log(f"`bookfactory next {BOOK_ID}` now returns: {task['task_id']}")
    log(f"  {task['summary']}")
    log(f"  output -> {task['output']['destination']}")
    log(f"  the approved artwork stays canonical until a replacement is approved")

    book = Book.load(BOOK_ID, REPO_ROOT)
    print()
    print(f"Demo book built: stage {book.state.stage_label}, "
          f"{len(book.manifest)} pages, {len(book.registry)} assets.")
    return book


def _build_cover() -> None:
    """Walk the cover tasks `bookfactory next` hands out, in order (AGENTS.md 9a)."""
    book = Book.load(BOOK_ID, REPO_ROOT)
    data = cover.load(book)
    data.update(direction=("Deadpan field-manual cover: the subject's back, one mug, one "
                           "inherited garden. Palette and edge treatment from the locked "
                           "references. No lettering in the artwork."),
                author=AUTHOR, back_copy=BACK_COPY)
    cover.save(book, data)
    log("cover direction, author and back copy recorded in cover/cover.json")

    api.register_asset(BOOK_ID, cover.ART_ID, root=REPO_ROOT, kind="cover_artwork",
                       title="Front cover artwork",
                       description="Native, text-free front cover illustration.",
                       references=book.required_reference_ids())
    book = Book.load(BOOK_ID, REPO_ROOT)
    needed = cover.artwork_constraints(book)
    art = _make_art(cover.ART_ID, needed["min_pixels"] + 30,
                    round((needed["min_pixels"] + 30) * needed["min_height_pixels"]
                          / needed["min_pixels"]))
    api.submit_asset(BOOK_ID, cover.ART_ID, art, kind=ASSET, root=REPO_ROOT,
                     source="demo-fixture", note="Synthetic placeholder cover artwork.")
    log(f"cover artwork submitted: {cover.ART_ID}")

    book = Book.load(BOOK_ID, REPO_ROOT)
    wrap = _typeset_cover(book, art)
    draft = cover.submit(book, wrap)
    log(f"cover draft {draft['revision']} submitted: {draft['path']}")

    # The operator's step. In a real book only the operator runs `cover approve`
    # (AGENTS.md 9a); this script is standing in for them.
    book = Book.load(BOOK_ID, REPO_ROOT)
    approved = cover.approve(book, draft["revision"], by=OPERATOR)
    log(f"cover {approved['revision']} approved by {approved['by']} (operator's step)")

    book = Book.load(BOOK_ID, REPO_ROOT)
    report = cover.preflight(book)
    log(f"cover preflight: {report['status']}")
    for problem in report["errors"]:
        log(f"  {problem}")


def _typeset_cover(book: Book, art: Path) -> Path:
    """Set the full wrap as real, embedded type around the native artwork.

    Uses WeasyPrint, which the page renderer already depends on and which
    embeds (subsets of) every font it uses - the cover gate checks for that.
    """
    from html import escape

    from weasyprint import HTML

    dim = cover.dimensions(book)
    data = cover.load(book)
    back_fold = dim["bleed_in"] + dim["trim_width_in"]
    front_fold = back_fold + dim["spine_in"]
    margin = .5
    front_width = dim["trim_width_in"] + dim["bleed_in"] - 2 * margin
    html = f"""<!doctype html><html><head><style>
      @page {{ size: {dim["width_in"]}in {dim["height_in"]}in; margin: 0; }}
      body {{ margin: 0; font-family: "DejaVu Sans", sans-serif; color: #1c1a17;
              background: #fbf8f1; }}
      .box {{ position: absolute; }}
      .title {{ left: {front_fold + margin}in; top: {margin}in; width: {front_width}in;
                font-size: 24pt; text-align: center; }}
      .art {{ left: {front_fold + margin + (front_width - data["artwork_width_in"]) / 2}in;
              top: 1.7in; width: {data["artwork_width_in"]}in;
              height: {data["artwork_height_in"]}in; }}
      .author {{ left: {front_fold + margin}in; top: {dim["height_in"] - 1}in;
                 width: {front_width}in; font-size: 12pt; text-align: center; }}
      .back {{ left: {margin}in; top: {margin}in; width: {back_fold - 2 * margin}in;
               font-size: 11pt; line-height: 1.4; }}
    </style></head><body>
      <div class="box title">{escape(book.state.title)}</div>
      <img class="box art" src="{art.resolve().as_uri()}">
      <div class="box author">{escape(data["author"])}</div>
      <div class="box back">{escape(data["back_copy"])}</div>
    </body></html>"""
    path = REPO_ROOT / ".demo-art" / "cover-wrap.pdf"
    HTML(string=html, base_url=str(REPO_ROOT)).write_pdf(str(path))
    return path


def _make_art(asset_id: str, width: int, height: int) -> Path:
    staging = REPO_ROOT / ".demo-art"
    staging.mkdir(exist_ok=True)
    path = staging / f"{asset_id}.png"
    demo_art.generate(path, width=width, height=height, seed=asset_id)
    return path


def _force_remove(path: Path) -> None:
    """Approved artefacts are read-only by design, so clear the flag first."""
    import os
    import stat

    for item in path.rglob("*"):
        if item.is_file():
            os.chmod(item, stat.S_IWUSR | stat.S_IRUSR)
    shutil.rmtree(path)


if __name__ == "__main__":
    try:
        build(clean="--keep" not in sys.argv)
    finally:
        shutil.rmtree(REPO_ROOT / ".demo-art", ignore_errors=True)
