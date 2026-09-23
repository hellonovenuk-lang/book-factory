"""Build the v4 interior layout proposal and check it.

Run from the repository root:
    python books/runners-guide-to-normal-conversation/interior/build_art.py
    python books/runners-guide-to-normal-conversation/interior/build_interior.py

Writes interior/interior-v4-proposal.pdf, then reports the page count, the
lowest image resolution at printed size and any page whose content stops
well short of the bottom margin (the "random white space" check).
"""

import sys
from pathlib import Path

import pymupdf
from weasyprint import HTML

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content  # noqa: E402

OUT = HERE / "interior-v4-proposal.pdf"


def build():
    html = (f'<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
            f'<title>{content.TITLE}</title><link rel="stylesheet" href="interior.css"></head>'
            f'<body>{content.body()}</body></html>')
    doc = HTML(string=html, base_url=str(HERE) + "/").render()
    if len(doc.pages) % 2:
        html = html.replace("</body>", content.notes_page() + "</body>")
        doc = HTML(string=html, base_url=str(HERE) + "/").render()
    doc.write_pdf(OUT)
    return len(doc.pages)


def check():
    d = pymupdf.open(OUT)
    low_dpi = []
    short = []
    bottom_limit = 9 * 72 - 0.72 * 72  # bottom of the text block, in points
    for i, page in enumerate(d, start=1):
        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            dpi = info["width"] / ((x1 - x0) / 72)
            low_dpi.append((dpi, i))
        pix = page.get_pixmap(dpi=36, colorspace=pymupdf.csGRAY)
        scale = 72 / 36
        rows = [y for y in range(pix.height)
                if y * scale < bottom_limit + 2
                and min(pix.samples[y * pix.stride:y * pix.stride + pix.width]) < 200]
        lowest = rows[-1] * scale if rows else 0
        gap = (bottom_limit - lowest) / 72
        if gap > 1.2 and "--all" not in sys.argv:
            short.append((i, round(gap, 2)))
        elif "--all" in sys.argv:
            heads = [b[4].split("\n")[0][:28] for b in page.get_text("blocks")
                     if b[4].strip() and any(sp["size"] > 13 for l in page.get_text("dict", clip=pymupdf.Rect(b[:4]))["blocks"]
                                             for ln in l.get("lines", []) for sp in ln["spans"])]
            print(f"  p{i:02d} gap {gap:4.1f}in  {' | '.join(heads[:3])}")
    print(f"{OUT.name}: {len(d)} pages")
    if low_dpi:
        dpi, page = min(low_dpi)
        print(f"lowest image resolution: {dpi:.0f} dpi (page {page})")
    print("pages ending more than 1.2 in above the bottom margin:", short or "none")
    return d


if __name__ == "__main__":
    n = build()
    check()
