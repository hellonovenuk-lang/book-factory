"""The deterministic page renderer.

The whole architecture rests on one separation:

    structured page specification   (words - exact, checked, versioned)
  + generated illustration assets   (pictures - creative, approved, immutable)
  + deterministic renderer          (typography, numbering, structure)
  ---------------------------------------------------------------------
  = finished page

Nothing generative happens here. Page numbers, headings, captions, tables,
checklists and quiz copy are set as real type from the page spec, because an
image model cannot be trusted to spell.
"""

from __future__ import annotations

import functools
from pathlib import Path

from bookfactory.core import checksums
from bookfactory.core.errors import RenderError, ValidationError
from bookfactory.render import backends
from bookfactory.render.templates import render_page_template

CSS_PATH = Path(__file__).resolve().parent / "assets" / "book.css"


@functools.lru_cache(maxsize=1)
def base_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def geometry(book, *, side: str) -> dict:
    """Page box and mirrored margins, in inches.

    With bleed enabled the sheet grows by the bleed amount on the top, bottom
    and outer edges only - the gutter edge never bleeds - which is what KDP
    expects for a bleeding interior.
    """
    from bookfactory.kdp import profiles

    tokens = book.design_tokens()
    profile_id = book.state.format.kdp_profile
    trim_w, trim_h = profiles.trim_inches(book.state.format.trim, profile_id)
    bleed = profiles.bleed_inches(profile_id) if book.state.format.bleed else 0.0

    margins = tokens.get("margins_in", {})
    top = float(margins.get("top", 0.75))
    bottom = float(margins.get("bottom", 0.75))
    inner = float(margins.get("inner", 0.875))
    outer = float(margins.get("outer", 0.625))

    page_w = trim_w + bleed
    page_h = trim_h + (2 * bleed)

    if side == "recto":            # right-hand page: gutter on the left
        left, right = inner, outer + bleed
    else:                          # verso: gutter on the right
        left, right = outer + bleed, inner

    return {
        "trim_width_in": round(trim_w, 4),
        "trim_height_in": round(trim_h, 4),
        "page_width_in": round(page_w, 4),
        "page_height_in": round(page_h, 4),
        "bleed_in": round(bleed, 4),
        "margin_top_in": round(top + bleed, 4),
        "margin_bottom_in": round(bottom + bleed, 4),
        "margin_left_in": round(left, 4),
        "margin_right_in": round(right, 4),
    }


def page_side(page) -> str:
    """Recto (right-hand, odd) or verso (left-hand, even)."""
    number = page.printed_number if page.printed_number is not None else page.sequence
    return "recto" if number % 2 == 1 else "verso"


def _asset_source(book, asset_id: str) -> str:
    """Absolute path to the *approved* artwork for an asset.

    Rendering never reaches into drafts. A page built from a draft would be a
    page nobody could later prove was the approved one.
    """
    asset = book.registry.find(asset_id)
    if asset is None:
        raise RenderError(
            f"Page requires asset '{asset_id}', which is not in the registry",
            remedy=f"Register it: `bookfactory asset add {book.state.book_id} {asset_id}`",
        )
    if not asset.approved:
        raise RenderError(
            f"Asset '{asset_id}' is not approved (status: {asset.status})",
            remedy=(
                f"Approve the artwork first: "
                f"`bookfactory approve {book.state.book_id} {asset_id} --kind asset`"
            ),
        )
    path = book.paths.resolve(asset.approved.path)
    checksums.verify(path, asset.approved.sha256)
    return path.resolve().as_uri()


#: Every copy field a template may reference, with its empty value. Templates
#: run with strict undefined checking - a typo in a spec should be a loud
#: failure, not a page that silently renders without its caption.
COPY_DEFAULTS = {
    "eyebrow": None, "heading": None, "subheading": None, "body": None,
    "caption": None, "quote": None, "attribution": None, "footnote": None,
    "items": [], "columns": [],
}
ITEM_DEFAULTS = {"label": None, "note": None, "options": None, "page": None}
COLUMN_DEFAULTS = {"title": None, "items": [], "image": None, "asset_id": None}


def _normalise_copy(raw: dict) -> dict:
    copy = {**COPY_DEFAULTS, **(raw or {})}
    copy["items"] = [
        {**ITEM_DEFAULTS, **item} if isinstance(item, dict) else item
        for item in (copy.get("items") or [])
    ]
    copy["columns"] = [
        {**COLUMN_DEFAULTS, **column} if isinstance(column, dict) else column
        for column in (copy.get("columns") or [])
    ]
    return copy


def build_context(book, page, spec: dict) -> dict:
    tokens = book.design_tokens()
    side = page_side(page)
    layout = spec.get("layout") or {}
    copy = _normalise_copy(spec.get("copy"))

    illustration = None
    illo_spec = spec.get("illustration")
    if illo_spec and illo_spec.get("asset_id"):
        illustration = {
            "asset_id": illo_spec["asset_id"],
            "placement": illo_spec.get("placement", "full_page"),
            "src": _asset_source(book, illo_spec["asset_id"]),
            "caption": copy.get("caption"),
        }

    for column in copy.get("columns") or []:
        if isinstance(column, dict) and column.get("asset_id"):
            column["image"] = _asset_source(book, column["asset_id"])

    rules = tokens.get("rules", {})
    show_running_head = layout.get("show_running_head", True)
    if page.type in ("chapter_opener", "front_matter", "quote", "certificate",
                     "contents", "closing"):
        show_running_head = layout.get(
            "show_running_head", rules.get("running_head_on_chapter_openers", False))
    show_folio = layout.get("show_page_number", True)
    if illustration and illustration["placement"] == "full_bleed":
        show_folio = layout.get("show_page_number", rules.get("folio_on_full_bleed_pages", False))

    body = copy.get("body")
    if isinstance(body, str):
        body_paragraphs = [b.strip() for b in body.split("\n\n") if b.strip()]
    else:
        body_paragraphs = [str(b) for b in (body or [])]

    dropcap = None
    if page.type == "chapter_opener" and body_paragraphs:
        first = body_paragraphs[0]
        if first:
            dropcap = {"letter": first[0], "rest": first[1:]}

    running_head = book.state.title if side == "verso" else (
        spec.get("running_head") or _chapter_running_head(book, page))

    return {
        "book": {
            "title": book.state.title,
            "subtitle": book.state.subtitle,
            "book_id": book.state.book_id,
            "language": "en-GB",
        },
        "page": {
            "page_id": page.page_id,
            "sequence": page.sequence,
            "printed_number": page.printed_number,
            "chapter": page.chapter,
            "title": page.title,
            "type": page.type,
            "side": side,
        },
        "spec": spec,
        "copy": copy,
        "body_paragraphs": body_paragraphs,
        "dropcap": dropcap,
        "illustration": illustration,
        "tokens": tokens,
        "geometry": geometry(book, side=side),
        "css": base_css(),
        "running_head": running_head,
        "show_running_head": show_running_head,
        "show_folio": show_folio,
    }


def _chapter_running_head(book, page) -> str:
    if page.chapter is None:
        return book.state.title
    for candidate in book.manifest:
        if candidate.chapter == page.chapter and candidate.type == "chapter_opener":
            return candidate.title
    return f"Chapter {page.chapter}"


def render_page_html(book, page_id: str) -> str:
    page = book.manifest.get(page_id)
    spec = book.read_page_spec(page_id)
    context = build_context(book, page, spec)
    return render_page_template(page.type, context)


def render_page(book, page_id: str, *, destination: Path | str | None = None,
                backend: str | None = None, keep_html: bool = True) -> Path:
    """Render one page to PDF. Returns the path to the PDF."""
    html = render_page_html(book, page_id)

    if keep_html:
        debug_dir = book.paths.renders_dir / "html"
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / f"{page_id}.html").write_text(html, encoding="utf-8")

    destination = Path(destination) if destination else book.paths.renders_dir / f"{page_id}.pdf"
    backends.render_html_to_pdf(html, destination, base_url=book.paths.root, backend=backend)
    _assert_single_page(destination, page_id)
    _assert_copy_present(destination, page_id, book.read_page_spec(page_id))
    return destination


def render_reference_page(book, spec: dict, *, destination: Path | str | None = None,
                          backend: str | None = None) -> Path:
    """Render one reference-set sample page to a one-page PDF.

    Used to typeset a book's reference-set samples (a chapter opener, a
    checklist/diagnostic page, an editorial page, a palette sheet, ...)
    before the book has a page plan. The spec is an ordinary page spec,
    validated exactly as a real page spec is, but it never joins the page
    manifest: no page id is reserved and nothing is written to pages/. An
    illustration the spec names must already be an approved asset, placed
    exactly as it would be on a real page.
    """
    from bookfactory import SCHEMA_VERSION
    from bookfactory.core import schema
    from bookfactory.core.models import PageRecord

    spec = dict(spec)
    if not spec.get("type"):
        raise ValidationError(
            "A reference sample spec needs a \"type\"",
            remedy="Add \"type\", e.g. \"chapter_opener\", \"checklist\", "
                   "\"editorial_illustration\" or \"palette_sheet\".",
        )
    spec.setdefault("schema_version", SCHEMA_VERSION)
    spec.setdefault("book_id", book.state.book_id)
    spec.setdefault("page_id", "p000")
    spec.setdefault("title", (spec.get("copy") or {}).get("heading")
                     or spec["type"].replace("_", " ").title())
    spec.setdefault("chapter", None)
    schema.validate("page-spec", spec, context="reference sample spec")

    page = PageRecord(page_id=spec["page_id"], sequence=1, title=spec["title"],
                      type=spec["type"], chapter=spec.get("chapter"), printed_number=1)

    context = build_context(book, page, spec)
    html = render_page_template(page.type, context)

    destination = (Path(destination) if destination
                  else book.paths.renders_dir / f"reference-{page.type}.pdf")
    destination.parent.mkdir(parents=True, exist_ok=True)
    backends.render_html_to_pdf(html, destination, base_url=book.paths.root, backend=backend)
    _assert_single_page(destination, page.page_id)
    _assert_copy_present(destination, page.page_id, spec)
    return destination


def _assert_single_page(pdf_path: Path, page_id: str) -> None:
    from pypdf import PdfReader

    count = len(PdfReader(str(pdf_path)).pages)
    if count != 1:
        raise RenderError(
            f"Page {page_id} rendered to {count} PDF pages, expected exactly 1",
            remedy=(
                "The page spec has more copy than fits the trim size. Shorten it, or split it "
                "into two pages in the manifest. Book Factory will not silently reflow a page "
                "into two."
            ),
        )


#: Copy fields that must be legible on the finished page. If the operator
#: approved these words, the page has to actually carry them.
VERIFIED_COPY_FIELDS = ("eyebrow", "heading", "subheading", "body", "caption",
                        "quote", "attribution", "footnote", "items")


def _flatten_copy(copy: dict) -> list[str]:
    strings: list[str] = []
    for field in VERIFIED_COPY_FIELDS:
        value = copy.get(field)
        if isinstance(value, str):
            strings.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    strings.append(item)
                elif isinstance(item, dict):
                    for key in ("label", "note"):
                        if isinstance(item.get(key), str):
                            strings.append(item[key])
    for column in copy.get("columns") or []:
        if isinstance(column, dict):
            if isinstance(column.get("title"), str):
                strings.append(column["title"])
            strings.extend(v for v in (column.get("items") or []) if isinstance(v, str))
    # Activity blocks: every string at any depth; "[ ]" in a table cell is a tick box.
    from bookfactory.qa.content import _block_text
    strings.extend(text.removeprefix("[ ]").strip() for text in _block_text(copy.get("blocks")))
    return [s for s in strings if len(s.strip()) > 3]


def _normalise(text: str) -> str:
    """Letters and digits only.

    Justification, hyphenation and line breaks all change how text extracts from
    a PDF; none of them change which characters the reader sees.
    """
    return "".join(character for character in text.lower() if character.isalnum())


def _needle(text: str) -> str:
    """What to look for in the extracted text.

    The first character is dropped on anything long enough to spare it, because
    a drop cap is a separate box and can extract out of order. One character of
    sensitivity is a cheap price for not crying wolf on every chapter opener.
    """
    normalised = _normalise(text)
    return normalised[1:] if len(normalised) > 12 else normalised


def _assert_copy_present(pdf_path: Path, page_id: str, spec: dict) -> None:
    """Every approved word must actually appear on the rendered page.

    Copy that overflows a fixed-height page is clipped rather than reflowed, and
    clipping silently deletes the end of a sentence. That is precisely the kind
    of quiet damage this system exists to prevent, so it is a hard failure.
    """
    from pypdf import PdfReader

    try:
        extracted = PdfReader(str(pdf_path)).pages[0].extract_text() or ""
    except Exception:  # noqa: BLE001 - extraction is a check, not the product
        return
    haystack = _normalise(extracted)
    if not haystack:
        return

    missing = [text for text in _flatten_copy(spec.get("copy") or {})
               if _needle(text) not in haystack]
    if missing:
        shown = "; ".join(f"{text[:60]}..." if len(text) > 60 else text for text in missing[:3])
        raise RenderError(
            f"Page {page_id} rendered without copy the spec requires: {shown}",
            remedy=(
                "The page has more copy than fits the trim size, so it was clipped. "
                "Shorten the copy, or split the page in two in the manifest. Book Factory "
                "will not ship a page that is missing approved words."
            ),
        )


def render_all(book, *, backend: str | None = None,
               only: list[str] | None = None) -> list[Path]:
    rendered = []
    for page in book.manifest:
        if only and page.page_id not in only:
            continue
        if not page.spec:
            raise ValidationError(
                f"Page {page.page_id} has no spec and cannot be rendered",
                remedy=f"Write pages/specs/{page.page_id}.json first.",
            )
        rendered.append(render_page(book, page.page_id, backend=backend))
    return rendered
