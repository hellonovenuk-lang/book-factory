"""Deterministic full-wrap print cover builder.

Typesets `cover/cover.json` into a full-wrap PDF the same way every time - no
one-off script per book (the running book alone had three) - and reuses Book
Factory's own cover checks (`bookfactory.core.cover.check_pdf`) so a cover
that builds clean is a cover that already passes the gate.

Nothing here approves anything. `build(..., submit=True)` only registers a new
reviewable draft, and only when the build has no problems.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import cover as cover_module
from bookfactory.core.errors import ValidationError
from bookfactory.render import backends
from bookfactory.render.templates import templates_root

#: Where a built cover and its previews live. Regenerable, like output/ generally.
BUILD_DIR = "output/cover-build"

DEFAULT_DESIGN = {
    "background": "#fbf8f1",
    "ink": "#1c1a17",
    "accent": "#8a3b2e",
}

MARGIN_IN = 0.5
FONT_SUFFIXES = (".ttf", ".otf")

#: Mirrors the KDP barcode rectangle in bookfactory.core.cover.check_pdf - the
#: back panel's content is kept entirely to its left, so it can never overlap
#: the barcode regardless of how tall the back copy grows.
BARCODE_X_OFFSET_IN = 2.16


def _cover_template_env():
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

    return Environment(
        loader=FileSystemLoader(str(templates_root() / "cover")),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=select_autoescape(["html", "xml", "j2"], default_for_string=True),
    )


def _book_font(book, rel_path: str, *, field: str) -> Path:
    if Path(rel_path).suffix.lower() not in FONT_SUFFIXES:
        raise ValidationError(
            f"cover.json design.{field} must be a .ttf or .otf file, got {rel_path!r}",
            remedy="Point it at a font file inside this book, e.g. style/fonts/Title.ttf",
        )
    resolved = (book.paths.root / rel_path).resolve()
    if not resolved.is_relative_to(book.paths.root.resolve()):
        raise ValidationError(
            f"cover.json design.{field} is outside the book project: {rel_path}",
            remedy="Point it at a font file inside this book, e.g. style/fonts/Title.ttf",
        )
    if not resolved.is_file():
        raise ValidationError(
            f"cover.json design.{field} file not found: {rel_path}",
            remedy="Add the font file to the book, or remove the design override.",
        )
    return resolved


def _paragraphs(text: str) -> list[str]:
    return [block.strip() for block in (text or "").split("\n\n") if block.strip()]


def _spine_allowed(dim: dict) -> bool:
    """Mirrors the spine-text rule in bookfactory.core.cover.check_pdf."""
    return dim["page_count"] >= 79 and (dim["spine_in"] - .125) >= 7 / 72


def build(book, *, submit: bool = False) -> dict:
    if not cover_module.required(book):
        raise ValidationError("Enable cover production with cover init")
    dim = cover_module.dimensions(book)
    data = cover_module.load(book)

    title = book.state.title
    if not (title or "").strip():
        raise ValidationError("The book has no title",
                              remedy="Set book.json's title before building the cover.")
    author = (data.get("author") or "").strip()
    if not author:
        raise ValidationError("cover.json has no author",
                              remedy="Set cover/cover.json's 'author' field.")
    back_copy = data.get("back_copy") or ""
    if not back_copy.strip():
        raise ValidationError("cover.json has no back_copy",
                              remedy="Set cover/cover.json's 'back_copy' field.")
    subtitle = data.get("subtitle")

    notes: list[str] = []
    spine_text = None
    spine_setting = data.get("spine_text")
    if spine_setting:
        if _spine_allowed(dim):
            spine_text = title if spine_setting is True else str(spine_setting)
        else:
            notes.append(
                "spine_text was set but left off this build: the cover cannot carry spine "
                "text yet (needs at least 79 pages and a wide enough spine for KDP's 7pt "
                "minimum and fold clearances). Remove spine_text from cover/cover.json, "
                "or add pages, so the cover checks pass."
            )

    design = data.get("design") or {}
    background = design.get("background") or DEFAULT_DESIGN["background"]
    ink = design.get("ink") or DEFAULT_DESIGN["ink"]
    accent = design.get("accent") or DEFAULT_DESIGN["accent"]

    title_font_family = "DejaVu Sans"
    body_font_family = "DejaVu Sans"
    font_faces = []
    if design.get("title_font"):
        path = _book_font(book, design["title_font"], field="title_font")
        title_font_family = "CoverTitleFont"
        font_faces.append({"family": title_font_family, "uri": path.as_uri()})
    if design.get("body_font"):
        path = _book_font(book, design["body_font"], field="body_font")
        body_font_family = "CoverBodyFont"
        font_faces.append({"family": body_font_family, "uri": path.as_uri()})

    mode = cover_module.artwork_mode(data)
    artwork_uri = None
    if mode == cover_module.NATIVE:
        _asset, art = cover_module._artwork(book)
        if not art:
            raise ValidationError(
                "No reviewable native cover artwork",
                remedy=(f"Submit cover-front-artwork first: `bookfactory submit "
                        f"{book.state.book_id} {cover_module.ART_ID} --kind asset "
                        f"--file <path>`, or record a text-only cover with "
                        f"`bookfactory cover artwork {book.state.book_id} --mode none "
                        f"--by <operator>`."),
            )
        artwork_uri = book.paths.resolve(art.path).resolve().as_uri()

    back_fold_in = dim["bleed_in"] + dim["trim_width_in"]
    front_fold_in = back_fold_in + dim["spine_in"]
    front_width_in = dim["trim_width_in"] + dim["bleed_in"] - 2 * MARGIN_IN
    back_width_in = (back_fold_in - BARCODE_X_OFFSET_IN) - MARGIN_IN - 0.1

    context = {
        "width_in": dim["width_in"], "height_in": dim["height_in"], "bleed_in": dim["bleed_in"],
        "back_fold_in": back_fold_in, "front_fold_in": front_fold_in, "spine_in": dim["spine_in"],
        "margin_in": MARGIN_IN, "front_width_in": front_width_in, "back_width_in": back_width_in,
        "title": title, "subtitle": subtitle, "author": author,
        "back_paragraphs": _paragraphs(back_copy), "spine_text": spine_text,
        # Fill the spine less its fold clearances, capped at 9pt; _spine_allowed
        # already guarantees at least KDP's 7pt minimum.
        "spine_font_pt": round(min(9.0, (dim["spine_in"] - .125) * 72), 2),
        "background": background, "ink": ink, "accent": accent,
        "title_font_family": title_font_family, "body_font_family": body_font_family,
        "font_faces": font_faces, "artwork_uri": artwork_uri,
        "artwork_width_in": data["artwork_width_in"], "artwork_height_in": data["artwork_height_in"],
    }
    html = _cover_template_env().get_template("wrap.html.j2").render(**context)

    destination = book.paths.root / BUILD_DIR / "cover-wrap.pdf"
    backends.render_html_to_pdf(html, destination, base_url=book.paths.root)

    problems = cover_module.check_pdf(book, destination)
    previews = _write_previews(destination, dim)

    result = {
        "pdf": book.paths.relative(destination),
        "previews": [book.paths.relative(p) for p in previews],
        "dimensions": dim,
        "problems": problems,
        "notes": notes,
        "submitted": None,
    }
    if submit and not problems:
        result["submitted"] = cover_module.submit(book, destination)
    return result


def _write_previews(pdf_path: Path, dim: dict) -> list[Path]:
    """A full-wrap preview and a trim-size front thumbnail, ~400px tall."""
    import fitz

    directory = pdf_path.parent
    with fitz.open(str(pdf_path)) as doc:
        page = doc[0]
        wrap_png = directory / "cover-wrap.png"
        page.get_pixmap(dpi=100).save(str(wrap_png))

        front_left = (dim["bleed_in"] + dim["trim_width_in"] + dim["spine_in"]) * 72
        right = (dim["width_in"] - dim["bleed_in"]) * 72
        top = dim["bleed_in"] * 72
        bottom = (dim["bleed_in"] + dim["trim_height_in"]) * 72
        clip = fitz.Rect(front_left, top, right, bottom)
        thumb_png = directory / "cover-thumb.png"
        thumb_dpi = max(1, round(400 / dim["trim_height_in"]))
        page.get_pixmap(dpi=thumb_dpi, clip=clip).save(str(thumb_png))
    return [wrap_png, thumb_png]
