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
pdfmetrics.registerFont(TTFont("BodyItalic", "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"))

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
INK = HexColor("#1b1f2e")
YELLOW = HexColor("#f6dc45")
CORAL = HexColor("#ed5a3a")

c = canvas.Canvas(str(PDF), pagesize=(width, height), pageCompression=1)
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

# The title dominates: it has to read at Amazon thumbnail size on its own.
centred("THE RUNNER’S GUIDE TO", 7.62 * inch, "Title", 44, YELLOW)
centred("NORMAL", 6.02 * inch, "Title", 160, PAPER)
centred("CONVERSATION", 5.20 * inch, "Title", 90, CORAL)

# The joke, typeset as a speech bubble: the question, then the answer.
bubble_top, bubble_bottom = 4.72 * inch, 2.42 * inch
c.setFillColor(PAPER)
c.roundRect(front_left, bubble_bottom, front_width, bubble_top - bubble_bottom,
            0.16 * inch, fill=1, stroke=0)
tail = c.beginPath()
tail.moveTo(front_left + 0.55 * inch, bubble_bottom + 1)
tail.lineTo(front_left + 0.40 * inch, bubble_bottom - 0.32 * inch)
tail.lineTo(front_left + 1.05 * inch, bubble_bottom + 1)
tail.close()
c.drawPath(tail, fill=1, stroke=0)

text_left = front_left + 0.28 * inch
c.setFillColor(CORAL)
c.setFont("Heavy", 11)
c.drawString(text_left, 4.32 * inch, "QUESTION ASKED")
c.setFillColor(INK)
c.setFont("BodyItalic", 16)
c.drawString(text_left, 4.02 * inch, "“How was your weekend?”")

c.setStrokeColor(BLUE)
c.setLineWidth(1.2)
c.line(text_left, 3.74 * inch, front_right - 0.28 * inch, 3.74 * inch)

c.setFillColor(CORAL)
c.setFont("Heavy", 11)
c.drawString(text_left, 3.44 * inch, "ANSWER GIVEN")
c.setFillColor(INK)
c.setFont("Body", 13)
answer = ("“So I was out the door at 6:15, and the first 3k felt heavy, "
          "which I put down to the porridge…”")
baseline = 3.16 * inch
for line in wrap_words(answer, front_width - 0.56 * inch, "Body", 13):
    c.drawString(text_left, baseline, line)
    baseline -= 17
c.setFillColor(BLUE)
c.setFont("Heavy", 11)
c.drawString(text_left, baseline - 6, "DURATION: 47 MINUTES AND COUNTING")

# Subtitle, then the author.
c.setFillColor(PAPER)
c.setFont("Body", 13.5)
baseline = 1.50 * inch
for line in wrap_words("A rehabilitation manual for runners who can no longer "
                       "answer a simple question", front_width, "Body", 13.5):
    c.drawCentredString(front_centre, baseline, line)
    baseline -= 18
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
