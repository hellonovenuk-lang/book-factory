"""Review output.

The previous project became hard to manage because there was no way to look at
the whole book at once. These commands build that view - and they build it from
*existing renders only*. Nothing here draws, rewrites or regenerates a page.
"""

from __future__ import annotations

import html
from pathlib import Path

from bookfactory.core import checksums, clock
from bookfactory.core.errors import AssemblyError
from bookfactory.core.jsonio import write_json

A4_WIDTH_PT = 595.276
A4_HEIGHT_PT = 841.890
SHEET_MARGIN_PT = 28.0
LABEL_HEIGHT_PT = 16.0
COLUMNS = 3
ROWS = 4


def generate_review(book, *, contact_sheet: bool = True, chapters: bool = True,
                    full: bool = True) -> dict:
    """Build the review material. Returns the paths produced."""
    approved = [p for p in book.manifest if p.approved]
    if not approved:
        raise AssemblyError(
            "Nothing to review: no page has been approved yet",
            remedy="Approve at least one page first.",
        )

    review_dir = book.paths.review_dir
    review_dir.mkdir(parents=True, exist_ok=True)
    produced: dict[str, str] = {}

    if full:
        from bookfactory.assembly.assemble import assemble

        target = review_dir / "full-book-review.pdf"
        record = assemble(book, destination=target, label="review", skip_checks=True)
        produced["full_book_review"] = record["output"]

    if chapters:
        for chapter in book.manifest.chapters():
            pages = [p for p in approved if p.chapter == chapter]
            if not pages:
                continue
            target = review_dir / f"chapter-{chapter:02d}.pdf"
            _concatenate(book, pages, target)
            produced[f"chapter_{chapter:02d}"] = book.paths.relative(target)

    if contact_sheet:
        target = review_dir / "full-book-contact-sheet.pdf"
        _contact_sheet(book, list(book.manifest), target)
        produced["contact_sheet"] = book.paths.relative(target)

    status = production_status(book)
    write_json(review_dir / "production-status.json", status)
    (review_dir / "production-status.md").write_text(_status_markdown(book, status),
                                                     encoding="utf-8")
    produced["production_status"] = book.paths.relative(review_dir / "production-status.md")

    book.log("review_generated", outputs=sorted(produced))
    return produced


def _concatenate(book, pages, destination: Path) -> Path:
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for page in pages:
        source = book.paths.resolve(page.approved.path)
        checksums.verify(source, page.approved.sha256)
        if source.suffix.lower() != ".pdf":
            from bookfactory.assembly.assemble import _image_to_pdf_page

            source = _image_to_pdf_page(book, source, page.page_id)
        writer.add_page(PdfReader(str(source)).pages[0])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        writer.write(handle)
    return destination


def _contact_sheet(book, pages, destination: Path) -> Path:
    """N-up thumbnails of every planned page, labelled with id and status.

    Pages that exist only as drafts, or not at all, are left as an empty cell
    with a label - so a gap in production is obvious at a glance, which is
    exactly what was missing last time.
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf import Transformation

    writer = PdfWriter()
    per_sheet = COLUMNS * ROWS
    usable_w = A4_WIDTH_PT - (2 * SHEET_MARGIN_PT)
    usable_h = A4_HEIGHT_PT - (2 * SHEET_MARGIN_PT)
    cell_w = usable_w / COLUMNS
    cell_h = usable_h / ROWS
    art_h = cell_h - LABEL_HEIGHT_PT

    chunks = [pages[i:i + per_sheet] for i in range(0, len(pages), per_sheet)] or [[]]

    for chunk in chunks:
        sheet = writer.add_blank_page(width=A4_WIDTH_PT, height=A4_HEIGHT_PT)
        cells = []
        for index, page in enumerate(chunk):
            column = index % COLUMNS
            row = index // COLUMNS
            cell_x = SHEET_MARGIN_PT + (column * cell_w)
            cell_top = A4_HEIGHT_PT - SHEET_MARGIN_PT - (row * cell_h)

            source = _thumbnail_source(book, page)
            if source is not None:
                reader = PdfReader(str(source))
                src = reader.pages[0]
                src_w = float(src.mediabox.width)
                src_h = float(src.mediabox.height)
                scale = min((cell_w * 0.86) / src_w, (art_h * 0.92) / src_h)
                draw_w = src_w * scale
                draw_h = src_h * scale
                offset_x = cell_x + ((cell_w - draw_w) / 2)
                offset_y = cell_top - LABEL_HEIGHT_PT - draw_h
                sheet.merge_transformed_page(
                    src, Transformation().scale(scale).translate(offset_x, offset_y))

            cells.append({
                "x_pt": cell_x,
                "top_pt": A4_HEIGHT_PT - cell_top,
                "width_pt": cell_w,
                "label": _cell_label(page),
                "status": page.status,
            })
        overlay = _label_overlay(book, cells)
        if overlay is not None:
            sheet.merge_page(overlay)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        writer.write(handle)
    return destination


def _thumbnail_source(book, page) -> Path | None:
    """Existing renders only, approved preferred. Never renders anything new."""
    candidates = []
    if page.approved:
        candidates.append(book.paths.resolve(page.approved.path))
    latest = page.latest_draft()
    if latest:
        candidates.append(book.paths.resolve(latest.path))
    candidates.append(book.paths.renders_dir / f"{page.page_id}.pdf")
    for candidate in candidates:
        if candidate.exists() and candidate.suffix.lower() == ".pdf":
            return candidate
    return None


def _cell_label(page) -> str:
    number = f"p.{page.printed_number}" if page.printed_number else "-"
    mark = {"approved": "APPROVED", "draft_submitted": "DRAFT", "rejected": "REJECTED"}.get(
        page.status, page.status.replace("_", " ").upper())
    if page.revision_open:
        mark += " / REVISING"
    return f"{page.page_id} - {number} - {mark}"


def _label_overlay(book, cells: list[dict]):
    """Labels are set as real type, on their own layer, over the thumbnails."""
    if not cells:
        return None
    rows = []
    for cell in cells:
        colour = {"APPROVED": "#1f6b3a", "DRAFT": "#8a6b12", "REJECTED": "#8c2f22"}.get(
            cell["label"].split(" - ")[-1].split(" /")[0], "#4a453e")
        rows.append(
            f'<div class="cell" style="left:{cell["x_pt"]:.2f}pt;'
            f'top:{cell["top_pt"]:.2f}pt;width:{cell["width_pt"]:.2f}pt;color:{colour}">'
            f'{html.escape(cell["label"])}</div>'
        )
    document = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page {{ size: {A4_WIDTH_PT}pt {A4_HEIGHT_PT}pt; margin: 0; }}
body {{ margin:0; font-family: "DejaVu Sans", sans-serif; }}
.cell {{ position:absolute; font-size:6.2pt; letter-spacing:0.04em;
         text-align:center; padding-top:2pt; }}
</style></head><body>{''.join(rows)}</body></html>"""

    from pypdf import PdfReader

    from bookfactory.render import backends

    overlay_path = book.paths.tmp_dir / "contact-sheet-labels.pdf"
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        backends.render_html_to_pdf(document, overlay_path, base_url=book.paths.root)
    except Exception:  # noqa: BLE001 - a missing label layer must not lose the sheet
        return None
    return PdfReader(str(overlay_path)).pages[0]


# ----------------------------------------------------------------------
# Production status report
# ----------------------------------------------------------------------


def production_status(book) -> dict:
    counts = book.manifest.counts()
    by_chapter = {}
    for page in book.manifest:
        key = str(page.chapter) if page.chapter is not None else "front/back matter"
        bucket = by_chapter.setdefault(key, {"total": 0, "approved": 0, "pages": []})
        bucket["total"] += 1
        bucket["approved"] += 1 if page.is_approved else 0
        bucket["pages"].append({
            "page_id": page.page_id,
            "printed_number": page.printed_number,
            "title": page.title,
            "type": page.type,
            "status": page.status,
            "revision_open": page.revision_open,
            "qa": page.qa,
        })
    return {
        "book_id": book.state.book_id,
        "title": book.state.title,
        "generated_at": clock.timestamp(),
        "stage": book.state.stage,
        "counts": counts,
        "assets": book.registry.counts(),
        "by_chapter": by_chapter,
        "next_action": book.state.next_action,
    }


def _status_markdown(book, status: dict) -> str:
    lines = [
        f"# Production status - {status['title']}",
        "",
        f"Generated {status['generated_at']} - stage **{book.state.stage_label}**",
        "",
        f"- Pages planned: {status['counts']['total']}",
        f"- Approved: {status['counts']['approved']}",
        f"- Draft: {status['counts']['draft_submitted']}",
        f"- Not started: {status['counts']['not_started']}",
        f"- In revision: {status['counts']['in_revision']}",
        "",
    ]
    for chapter, bucket in sorted(status["by_chapter"].items()):
        lines.append(f"## Chapter {chapter} - {bucket['approved']}/{bucket['total']} approved")
        lines.append("")
        lines.append("| Page | Printed | Title | Type | Status |")
        lines.append("| ---- | ------- | ----- | ---- | ------ |")
        for page in bucket["pages"]:
            lines.append(
                f"| {page['page_id']} | {page['printed_number'] or '-'} | {page['title']} "
                f"| {page['type']} | {page['status']}"
                f"{' (revising)' if page['revision_open'] else ''} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"
