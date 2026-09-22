"""Build a text-only full-wrap cover proposal (v2) for side-by-side review.

Every mark on this cover is real type or a simple vector shape: no generated
artwork. It is a proposal only. It is not submitted through `bookfactory cover
submit`, whose gate currently requires native cover artwork, and it does not
replace the operator-approved v1 draft.
"""

from pathlib import Path

import fitz
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from bookfactory.core.book import Book
from bookfactory.core import cover


ROOT = Path(__file__).resolve().parents[3]
BOOK = Book.load("runners-guide-to-normal-conversation", ROOT)
DIRECTORY = Path(__file__).resolve().parent
FONTS = DIRECTORY / "fonts"
OUT = DIRECTORY / "proposals"
OUT.mkdir(exist_ok=True)
PDF = OUT / "cover-v2-text-only.pdf"
WRAP = OUT / "cover-v2-text-only-full-wrap.png"
FRONT = OUT / "cover-v2-text-only-front-print.png"
THUMB = OUT / "cover-v2-text-only-amazon-thumbnail.png"

pdfmetrics.registerFont(TTFont("Title", str(FONTS / "Anton-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Heavy", str(FONTS / "ArchivoBlack-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Body", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))

inch = 72
d = cover.dimensions(BOOK)
width = d["width_in"] * inch
height = d["height_in"] * inch
back_fold = (d["bleed_in"] + d["trim_width_in"]) * inch
front_fold = back_fold + d["spine_in"] * inch
front_left = front_fold + 0.55 * inch
front_right = front_fold + d["trim_width_in"] * inch - 0.55 * inch
front_width = front_right - front_left
front_centre = (front_left + front_right) / 2

BLUE = HexColor("#2445a2")
PAPER = HexColor("#fbf8f1")
YELLOW = HexColor("#f6dc45")
CORAL = HexColor("#ed5a3a")

c = canvas.Canvas(str(PDF), pagesize=(width, height), pageCompression=1,
                  initialFontName="Body")
c.setTitle("The Runner’s Guide to Normal Conversation — text-only cover proposal v2")
c.setAuthor(cover.load(BOOK)["author"])

c.setFillColor(BLUE)
c.rect(0, 0, width, height, fill=1, stroke=0)


def fit(text, font, wanted, maximum):
    size = wanted
    while pdfmetrics.stringWidth(text, font, size) > maximum:
        size -= 0.25
    return size


def centred(text, y, font, wanted, colour, maximum=front_width):
    size = fit(text, font, wanted, maximum)
    c.setFillColor(colour)
    c.setFont(font, size)
    c.drawCentredString(front_centre, y, text)
    return size


def wrap_words(text, max_width, font, size):
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}" if current else word
        if current and pdfmetrics.stringWidth(trial, font, size) > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------- front
# The mock-official issuing body, set small, as a strap across the top.
c.setFillColor(CORAL)
c.rect(front_fold, 8.38 * inch, d["trim_width_in"] * inch + d["bleed_in"] * inch,
       0.34 * inch, fill=1, stroke=0)
centred("THE NORMAL CONVERSATION REHABILITATION SERVICE", 8.49 * inch, "Heavy", 9.5, PAPER)

# The title fills the front on its own: each line is set as wide as the
# front allows, and the lines are spread evenly down the space between the
# strap and the subtitle. It has to read at Amazon thumbnail size.
CAP_HEIGHT = {name: pdfmetrics.getFont(name).face.capHeight / 1000 for name in ("Title",)}
title_lines = [
    ("THE RUNNER’S", YELLOW),
    ("GUIDE TO", YELLOW),
    ("NORMAL", PAPER),
    ("CONVERSATION", CORAL),
]
sizes = [fit(text, "Title", 200, front_width) for text, _ in title_lines]
# Every line is as wide as the front allows, with equal space between lines.
gap_weights = [1.0, 1.0, 1.0]
region_top, region_bottom = 8.05 * inch, 2.05 * inch
caps = [size * CAP_HEIGHT["Title"] for size in sizes]
unit = (region_top - region_bottom - sum(caps)) / sum(gap_weights)
top = region_top
for index, ((text, colour), size, cap) in enumerate(zip(title_lines, sizes, caps)):
    centred(text, top - cap, "Title", size, colour)
    if index < len(gap_weights):
        top -= cap + unit * gap_weights[index]

# Subtitle, then the author.
c.setFillColor(PAPER)
c.setFont("Body", 14)
baseline = 1.50 * inch
for line in wrap_words("A rehabilitation manual for runners who can no longer "
                       "answer a simple question", front_width, "Body", 14):
    c.drawCentredString(front_centre, baseline, line)
    baseline -= 19
centred(cover.load(BOOK)["author"].upper(), 0.62 * inch, "Heavy", 17, YELLOW)

# ----------------------------------------------------------------- back
c.setFillColor(YELLOW)
c.setFont("Title", 38)
c.drawString(0.60 * inch, 8.25 * inch, "THEY ONLY ASKED")
c.drawString(0.60 * inch, 7.70 * inch, "ABOUT YOUR WEEKEND.")
c.setStrokeColor(CORAL)
c.setLineWidth(4)
c.line(0.60 * inch, 7.42 * inch, 2.3 * inch, 7.42 * inch)

c.setFillColor(PAPER)
c.setFont("Body", 13.2)
baseline = 6.95 * inch
for paragraph in cover.load(BOOK)["back_copy"].split("\n\n"):
    for line in wrap_words(paragraph, 4.9 * inch, "Body", 13.2):
        c.drawString(0.60 * inch, baseline, line)
        baseline -= 19.0
    baseline -= 16.0

# KDP may add the free-ISBN barcode in this empty rectangle.
c.setFillColor(PAPER)
c.rect(3.965 * inch, 0.34 * inch, 2.02 * inch, 1.22 * inch, fill=1, stroke=0)
c.showPage()
c.save()

with fitz.open(PDF) as doc:
    page = doc[0]
    page.get_pixmap(matrix=fitz.Matrix(130 / 72, 130 / 72), alpha=False).save(WRAP)
    front = fitz.Rect(front_fold, 0.125 * inch, front_fold + 6 * inch, 9.125 * inch)
    page.get_pixmap(matrix=fitz.Matrix(180 / 72, 180 / 72), clip=front, alpha=False).save(FRONT)
    page.get_pixmap(matrix=fitz.Matrix(16 / 72, 16 / 72), clip=front, alpha=False).save(THUMB)

for path in (PDF, WRAP, FRONT, THUMB):
    print(path)
