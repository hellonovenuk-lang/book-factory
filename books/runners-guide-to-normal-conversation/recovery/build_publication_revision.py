"""Prepare a publication-details draft from the preserved interior.

This is an explicit PDF-level recovery operation, not a Book Factory approval.
It changes PDF page 2 (author) and replaces PDF page 4 with the supplied
publication-page preview plus the confirmed copyright line. Other pages are
carried over unchanged in appearance. Keep the v2 source PDF separately.
"""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

import fitz
from pypdf import PdfReader, PdfWriter

TRIM = (432, 648)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def add_text(page, value, x, baseline_from_bottom, size, color):
    page.insert_font(fontname="RecoveredSerif", fontfile=FONT_PATH)
    page.insert_text(
        (x, TRIM[1] - baseline_from_bottom), value,
        fontsize=size, fontname="RecoveredSerif", color=color,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interior", type=Path)
    parser.add_argument("preview", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--publication-only", type=Path)
    args = parser.parse_args()

    with fitz.open(args.interior) as source_doc:
        with fitz.open(args.preview) as preview_doc:
            if len(source_doc) != 80 or len(preview_doc) != 1:
                raise ValueError("Expected an 80-page interior and a one-page preview")
            for page in (source_doc[1], source_doc[3], preview_doc[0]):
                if (page.rect.width, page.rect.height) != TRIM:
                    raise ValueError("Input page is not 6 × 9 inches")

            author_text = "Kieran Smith"
            font = fitz.Font(fontfile=FONT_PATH)
            author_x = (TRIM[0] - font.text_length(author_text, fontsize=11.5)) / 2
            add_text(source_doc[1], author_text, author_x, 144, 11.5, (.13, .13, .13))
            edited_source = source_doc.tobytes(garbage=4, deflate=True)

            # Remove placeholder glyphs from actual PDF content. A visual
            # overlay would leave them in extractable text.
            page = preview_doc[0]
            page.add_redact_annot(
                fitz.Rect(35, 510, 400, 610),
                fill=(251 / 255, 250 / 255, 245 / 255),
            )
            page.apply_redactions(images=0, graphics=0, text=0)
            add_text(page, "© 2026 Kieran Smith", 45.5, 106, 9.1,
                     (.18, .18, .18))
            clean_preview = preview_doc.tobytes(garbage=4, deflate=True)

    edited_publication = PdfReader(BytesIO(clean_preview)).pages[0]
    if args.publication_only:
        single = PdfWriter()
        single.add_page(edited_publication)
        args.publication_only.parent.mkdir(parents=True, exist_ok=True)
        with args.publication_only.open("wb") as f:
            single.write(f)

    source = PdfReader(args.interior)
    edited_title_page = PdfReader(BytesIO(edited_source)).pages[1]
    writer = PdfWriter()
    for index, page in enumerate(source.pages):
        if index == 1:
            page = edited_title_page
        elif index == 3:
            page = edited_publication
        writer.add_page(page)
    writer.add_metadata({"/Title": "The Runner’s Guide to Normal Conversation", "/Author": "Kieran Smith"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as f:
        writer.write(f)


if __name__ == "__main__":
    main()
