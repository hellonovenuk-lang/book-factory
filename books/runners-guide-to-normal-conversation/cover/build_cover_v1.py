"""Rebuild the provisional full-wrap cover v1 from native art and real type."""

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
ART = DIRECTORY / "native/cover-front-artwork-v1.png"
WORK = DIRECTORY / "work"
WORK.mkdir(exist_ok=True)
PDF = WORK / "cover-v1-review.pdf"
WRAP = DIRECTORY / "previews/cover-v1-full-wrap.png"
FRONT = DIRECTORY / "previews/cover-v1-front-print.png"
THUMB = DIRECTORY / "previews/cover-v1-amazon-thumbnail.png"
WRAP.parent.mkdir(exist_ok=True)

pdfmetrics.registerFont(TTFont("Display", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("BodyBold", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))

inch = 72
d = cover.dimensions(BOOK)
width = d["width_in"] * inch
height = d["height_in"] * inch
back_fold = (d["bleed_in"] + d["trim_width_in"]) * inch
front_fold = back_fold + d["spine_in"] * inch
front_centre = front_fold + 3 * inch
c = canvas.Canvas(str(PDF), pagesize=(width, height), pageCompression=1)
c.setTitle("The Runner’s Guide to Normal Conversation — provisional cover v1")
c.setAuthor("Kieran Smith")

BLUE = HexColor("#2445a2")
PAPER = HexColor("#fbf8f1")
YELLOW = HexColor("#f6dc45")
CORAL = HexColor("#ed5a3a")

# A continuous blue field crosses both folds and the narrow, unlettered spine.
c.setFillColor(BLUE)
c.rect(0, 0, width, height, fill=1, stroke=0)


def fitted_centred(text, y, wanted, maximum, colour):
    size = wanted
    while pdfmetrics.stringWidth(text, "Display", size) > maximum:
        size -= 0.25
    c.setFillColor(colour)
    c.setFont("Display", size)
    c.drawCentredString(front_centre, y, text)


# The exact title is drawn as real, embedded font type in reading order.
fitted_centred("THE RUNNER’S", 8.33 * inch, 45, 5.40 * inch, YELLOW)
fitted_centred("GUIDE TO", 7.56 * inch, 46, 5.40 * inch, PAPER)
fitted_centred("NORMAL", 6.74 * inch, 59, 5.40 * inch, PAPER)
fitted_centred("CONVERSATION", 6.16 * inch, 38, 5.40 * inch, CORAL)

# Native 1024 x 1536 art occupies precisely 3.4 x 5.1 inches: 301 DPI.
c.drawImage(str(ART), front_centre - 1.7 * inch, 0.87 * inch,
            width=3.4 * inch, height=5.1 * inch, mask="auto")
c.setFillColor(YELLOW)
c.setFont("Display", 19)
c.drawCentredString(front_centre, 0.43 * inch, "KIERAN SMITH")

# Back cover: a brisk recognition line, followed by the saved cover copy.
c.setFillColor(YELLOW)
c.setFont("Display", 27)
c.drawString(0.60 * inch, 8.37 * inch, "THEY ONLY ASKED")
c.drawString(0.60 * inch, 7.90 * inch, "ABOUT YOUR WEEKEND.")
c.setStrokeColor(CORAL)
c.setLineWidth(4)
c.line(0.60 * inch, 7.60 * inch, 2.3 * inch, 7.60 * inch)


def wrap_words(text, max_width, font="Body", size=13.2):
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


c.setFillColor(PAPER)
c.setFont("Body", 13.2)
baseline = 7.10 * inch
for paragraph in cover.load(BOOK)["back_copy"].split("\n\n"):
    for line in wrap_words(paragraph, 4.9 * inch):
        c.drawString(0.60 * inch, baseline, line)
        baseline -= 19.0
    baseline -= 16.0

# KDP may add the free-ISBN barcode in this empty, art-free rectangle.
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

print(PDF)
print(WRAP)
print(FRONT)
print(THUMB)
