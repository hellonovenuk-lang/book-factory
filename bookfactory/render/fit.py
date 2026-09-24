"""Fit-testing a page plan before it is loaded into a book.

`plan --from-manuscript` (task 17.1) puts one manuscript section on one page.
Some sections are too long for one page: the deterministic renderer clips
rather than reflows overflowing copy (`bookfactory/render/renderer.py`), so
an overflowing page must be caught and, where that is safe, split before the
plan is ever written to the book.

`fit_pages` renders every planned page's spec in every available engine
(WeasyPrint and Chromium disagree on layout, so a page must fit in both to
count as fitting) and splits an overflowing `chapter_opener` or
`text_illustration` page into an opener/lead page plus one or more
`text_illustration` continuation pages, the same shape the Golf Addict's
Guide's p005/p006 were split into by hand. Nothing is written to the book:
every render happens in a throwaway temporary directory, and a page whose
picture is not drawn yet is fit-tested with a same-sized placeholder image
rather than the book's real asset registry being touched.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from bookfactory.core import checksums, clock
from bookfactory.core.errors import RenderError
from bookfactory.core.models import ApprovalRecord, AssetRecord
from bookfactory.render import backends as render_backends
from bookfactory.render.renderer import render_reference_page

#: A `chapter_opener` or `text_illustration` page is plain eyebrow/heading/
#: body prose (`templates/pages/chapter_opener.html.j2`,
#: `templates/pages/text_illustration.html.j2`), so moving its trailing
#: whole paragraphs onto a following page never reorders or drops text and
#: never touches a table, a checklist or an activity's blocks. Every other
#: page type is left alone: splitting it would mean inventing structure the
#: plan never asked for.
SPLITTABLE_TYPES = ("chapter_opener", "text_illustration")

_PLACEHOLDER_SIZE = (1200, 1200)
_PLACEHOLDER_NAME = "_fit-test-placeholder.png"


def fit_pages(book, pages: list[dict], *, backends: list[str] | None = None) -> dict:
    """Render every planned page in every available engine, splitting where safe.

    `pages` are plan-file entries: `{"title", "type", "chapter", "spec"}`.
    Returns `{"pages": [...], "report": [...]}`: `pages` is the same list
    with overflowing pages replaced by their split parts in order; `report`
    has one entry per *input* page, `{"index", "title", "status", "detail"}`
    with `status` one of `"fits"`, `"split"`, `"too_long"`, `"not_checked"`.
    """
    engines = list(backends) if backends is not None else render_backends.available_backends()

    if not engines:
        return {
            "pages": list(pages),
            "report": [
                {"index": index, "title": page.get("title", ""), "status": "not_checked",
                 "detail": "no render backend (WeasyPrint or Chromium) is available in this "
                           "environment, so nothing could be fit-tested"}
                for index, page in enumerate(pages)
            ],
        }

    result_pages: list[dict] = []
    report: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="bf-fit-") as tmp:
        tmp_dir = Path(tmp)
        placeholder = _placeholder_image(tmp_dir)
        for index, page in enumerate(pages):
            parts, status, detail = _fit_page(book, page, engines, tmp_dir, placeholder)
            result_pages.extend(parts)
            report.append({"index": index, "title": page.get("title", ""),
                           "status": status, "detail": detail})

    return {"pages": result_pages, "report": report}


# -- one page -----------------------------------------------------------

def _fit_page(book, page: dict, engines: list[str], tmp_dir: Path, placeholder: Path):
    spec = dict(page.get("spec") or {})
    page_type = spec.get("type") or page.get("type")

    ok, detail = _check_all_engines(book, spec, engines, tmp_dir, placeholder)
    if ok:
        return [page], "fits", detail

    if page_type not in SPLITTABLE_TYPES:
        return [page], "too_long", (
            f"does not fit and '{page_type}' is not a splittable page type ({detail})")

    body = _body_paragraphs(spec)
    # A chapter opener may hand its whole body to the next page (the Golf
    # Addict's Guide's Stage Seven and Eight openers kept an empty body), so
    # even a single paragraph can move off it. Any other page must keep one.
    lead_minimum = 0 if page_type == "chapter_opener" else 1
    if len(body) <= lead_minimum:
        return [page], "too_long", (
            f"does not fit and has no whole paragraph left to split off ({detail})")

    parts: list[dict] = []
    remaining = body
    part_index = 0
    last_detail = detail
    while remaining:
        chunk_page = None
        chunk_detail = None
        n = len(remaining)
        minimum = lead_minimum if part_index == 0 else 1
        while n >= minimum:
            trial = _make_chunk_page(page, spec, remaining[:n], part_index)
            trial_ok, trial_detail = _check_all_engines(
                book, trial["spec"], engines, tmp_dir, placeholder)
            if trial_ok:
                chunk_page, chunk_detail = trial, trial_detail
                break
            n -= 1
        if chunk_page is None:
            # Not even a single whole paragraph fits alone: splitting further
            # would mean breaking a paragraph in half, which is never done.
            return [page], "too_long", (
                f"does not fit even split down to one paragraph per page ({last_detail}); "
                "left unsplit rather than break a paragraph")
        parts.append(chunk_page)
        last_detail = chunk_detail
        remaining = remaining[len(chunk_page["spec"]["copy"]["body"]):]
        part_index += 1

    _move_footnote_to_the_last_part(book, parts, engines, tmp_dir, placeholder)

    return parts, "split", f"split into {len(parts)} page(s) ({detail} on the original)"


def _move_footnote_to_the_last_part(book, parts: list[dict], engines: list[str],
                                    tmp_dir: Path, placeholder: Path) -> None:
    """A footnote belongs at the end of the page group, not on the lead part.

    The lead part is built with all of the original copy, footnote included
    (part 1), so if the page ended up split, move the footnote onto the last
    part instead - but only if it still fits there with its own copy, since
    the lead part was already proven to fit and removing text can only help.
    """
    if len(parts) < 2:
        return
    lead_copy = parts[0]["spec"]["copy"]
    footnote = lead_copy.get("footnote")
    if not footnote:
        return
    last = parts[-1]
    trial_copy = dict(last["spec"]["copy"])
    trial_copy["footnote"] = footnote
    trial_spec = dict(last["spec"])
    trial_spec["copy"] = trial_copy
    ok, _ = _check_all_engines(book, trial_spec, engines, tmp_dir, placeholder)
    if not ok:
        return  # leave the footnote on the lead part rather than lose it
    lead_copy.pop("footnote", None)
    last["spec"]["copy"] = trial_copy


def _make_chunk_page(original_page: dict, original_spec: dict, body_chunk: list[str],
                     part_index: int) -> dict:
    original_copy = original_spec.get("copy") or {}

    if part_index == 0:
        # The lead part keeps the opener's own furniture - eyebrow, heading,
        # subheading - exactly as written; only the body is trimmed.
        copy = dict(original_copy)
        page_type = original_spec.get("type") or original_page.get("type")
        title = original_spec.get("title") or original_page.get("title")
        illustration = original_spec.get("illustration")
    else:
        # A continuation is `text_illustration`, which (like the Golf
        # Addict's Guide's p006) carries no `heading`/`subheading` of its
        # own - the template does not set `subheading` at all, and repeating
        # `heading` would duplicate the opener's title. It keeps the
        # `eyebrow`, so the reader still sees which chapter they are in.
        copy = {}
        if original_copy.get("eyebrow"):
            copy["eyebrow"] = original_copy["eyebrow"]
        page_type = "text_illustration"
        base_title = original_spec.get("title") or original_page.get("title") or ""
        suffix = " (continued)" if part_index == 1 else f" (continued {part_index})"
        title = f"{base_title}{suffix}"
        illustration = None  # the opener/lead page already carries the picture

    copy["body"] = list(body_chunk)
    chapter = original_spec.get("chapter", original_page.get("chapter"))

    spec = dict(original_spec)
    spec["type"] = page_type
    spec["title"] = title
    spec["chapter"] = chapter
    spec["copy"] = copy
    spec["illustration"] = illustration

    return {"title": title, "type": page_type, "chapter": chapter, "spec": spec}


def _body_paragraphs(spec: dict) -> list[str]:
    body = (spec.get("copy") or {}).get("body")
    if isinstance(body, str):
        return [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]
    return [str(paragraph) for paragraph in (body or [])]


# -- rendering ------------------------------------------------------------

def _check_all_engines(book, spec: dict, engines: list[str], tmp_dir: Path,
                       placeholder: Path) -> tuple[bool, str]:
    """Render `spec` in every engine. A page must fit in all of them to count."""
    stub = _stand_in_for_illustration(book, spec, placeholder)
    used_placeholder = stub is not None
    try:
        for engine in engines:
            destination = tmp_dir / f"fit-{uuid.uuid4().hex}.pdf"
            try:
                render_reference_page(book, spec, destination=destination, backend=engine)
            except RenderError as exc:
                return False, f"{engine}: {exc}"
    finally:
        if stub is not None:
            book.registry.assets.remove(stub)

    detail = "fits in " + ", ".join(engines)
    if used_placeholder:
        asset_id = spec["illustration"]["asset_id"]
        detail += (f" (its picture, '{asset_id}', is not drawn yet - the space was checked with "
                   "a same-size placeholder standing in for it)")
    return True, detail


def _stand_in_for_illustration(book, spec: dict, placeholder: Path) -> AssetRecord | None:
    """Register a throwaway approved stub for an undrawn illustration.

    A plan built ahead of production almost always names artwork nobody has
    drawn yet, and `render_reference_page` refuses a missing or unapproved
    asset. The stub is added to the in-memory registry only (never saved to
    disk) and removed again by the caller once this render finishes, so the
    book's real asset registry is never touched.
    """
    illustration = spec.get("illustration")
    if not illustration or not illustration.get("asset_id"):
        return None
    asset_id = illustration["asset_id"]
    existing = book.registry.find(asset_id)
    if existing is not None and existing.approved:
        return None  # real approved artwork already exists; use it as-is

    stub = AssetRecord(
        asset_id=asset_id,
        kind="illustration",
        status="approved",
        approved=ApprovalRecord(
            revision="v1",
            path=str(placeholder),
            sha256=checksums.sha256_file(placeholder),
            approved_at=clock.timestamp(),
            approved_by="fit-test",
        ),
    )
    book.registry.assets.append(stub)
    return stub


def _placeholder_image(tmp_dir: Path) -> Path:
    """A plain image the size templates commonly reserve, so a picture's box
    is still counted against the page even though nothing was drawn yet."""
    from PIL import Image

    path = tmp_dir / _PLACEHOLDER_NAME
    Image.new("RGB", _PLACEHOLDER_SIZE, (210, 210, 210)).save(path)
    return path
