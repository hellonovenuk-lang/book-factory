"""Prepare the interior illustrations for the v4 layout proposal.

Reads the 25 illustrations embedded in releases/interior-v3-publication-draft.pdf
(the only surviving copies) and writes print-ready greyscale PNGs to
interior/art/. Nothing is redrawn or generated. Each image is only:

* flattened onto white (page 68's image carries a transparency mask),
* converted to true greyscale (the interior prints black and white),
* levelled so the paper tone becomes pure white and the linework deepens,
* cropped to the drawing, so it can be printed larger,
* feathered at the edges, so scenes sit on the page without a hard box.

Run from the repository root:
    python books/runners-guide-to-normal-conversation/interior/build_art.py
"""

from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
SOURCE = BOOK / "releases" / "interior-v3-publication-draft.pdf"
OUT = HERE / "art"
# v3 printed the same drawing on pages 9 and 41; v4 uses it once (page 41).
SKIP_PAGES = {9}


def _rgb(doc, xref):
    pix = pymupdf.Pixmap(doc, xref)
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)
    if pix.colorspace is None or pix.colorspace.n != 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def clean(im):
    g = np.asarray(im.convert("L")).astype(float)
    paper = max(np.percentile(g, 80 if g.mean() > 190 else 92), 200)
    ink = np.percentile(g, 0.8)
    v = np.clip((g - ink) / (paper - ink), 0, 1) ** 1.35
    v = np.where(v > 0.93, 1.0, v)

    drawn = v < 0.85
    rows = np.where(drawn.mean(1) > 0.004)[0]
    cols = np.where(drawn.mean(0) > 0.004)[0]
    pad = 24
    v = v[max(rows[0] - pad, 0):min(rows[-1] + pad, v.shape[0]),
          max(cols[0] - pad, 0):min(cols[-1] + pad, v.shape[1])]

    h, w = v.shape
    f = int(min(h, w) * 0.06)
    yy = np.minimum(np.arange(h), np.arange(h)[::-1]) / f
    xx = np.minimum(np.arange(w), np.arange(w)[::-1]) / f
    e = np.clip(np.minimum(yy[:, None], xx[None, :]), 0, 1)
    e = e * e * (3 - 2 * e)
    v = 1 - (1 - v) * e
    return Image.fromarray((v * 255).round().astype("uint8"), "L")


def main():
    OUT.mkdir(exist_ok=True)
    doc = pymupdf.open(SOURCE)
    for number, page in enumerate(doc, start=1):
        if number in SKIP_PAGES:
            continue
        for info in page.get_images(full=True):
            xref, smask = info[0], info[1]
            pix = pymupdf.Pixmap(doc, xref)
            if pix.colorspace is None or pix.colorspace.n != 3:
                continue  # a bare mask, handled with its colour image
            im = _rgb(doc, xref)
            if smask:
                m = pymupdf.Pixmap(doc, smask)
                alpha = Image.frombytes("L", (m.width, m.height), m.samples)
                im = Image.composite(im, Image.new("RGB", im.size, "white"), alpha)
            out = clean(im)
            name = OUT / f"art-p{number:03d}.png"
            out.save(name, dpi=(300, 300))
            print(f"{name.name}  {out.width}x{out.height}px  "
                  f"max {out.width / 300:.2f}in wide at 300 dpi")


if __name__ == "__main__":
    main()
