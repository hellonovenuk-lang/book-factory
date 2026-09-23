"""Build cover proposal v3: "How was your weekend?"

A full-wrap KDP paperback cover for the 58-page interior v4
(interior/interior-v4-proposal.pdf). Everything is typeset or drawn as
vector shapes by this script: there is no generated artwork and no generated
lettering. The spine is left blank (58 pages is far below KDP's 79-page
minimum for spine text).

Run from the repository root:
    python books/runners-guide-to-normal-conversation/cover/build_cover_v3.py

Writes cover/proposals/cover-v3-weekend.pdf and three previews, then runs
Book Factory's own cover checks (bookfactory.core.cover.check_pdf) against
the 58-page dimensions.
"""

import json
from pathlib import Path

import pymupdf
from weasyprint import HTML

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
INTERIOR = BOOK / "interior" / "interior-v4-proposal.pdf"
OUT = HERE / "proposals" / "cover-v3-weekend.pdf"

BLEED = 0.125
TRIM_W, TRIM_H = 6.0, 9.0
PAGES = len(pymupdf.open(INTERIOR))
SPINE = round(PAGES * 0.002252, 6)            # white paper, as bookfactory/core/cover.py
WIDTH = round(2 * TRIM_W + SPINE + 2 * BLEED, 6)
HEIGHT = TRIM_H + 2 * BLEED
FRONT = BLEED + TRIM_W + SPINE                 # x of the front fold, inches

DATA = json.loads((HERE / "cover.json").read_text())
TITLE = "The Runner’s Guide to Normal Conversation"
SUBTITLE = "A Rehabilitation Manual for Runners Who Can No Longer Answer a Simple Question"
AUTHOR = DATA["author"]
BACK_COPY = DATA["back_copy"]

ORANGE = "#ff5a1f"
INK = "#17120f"
LIME = "#c8f53a"
CREAM = "#fff6ec"


def route_svg():
    """A looping GPS trace with start/finish flag, drawn as plain vector lines."""
    return f"""
<svg viewBox="0 0 200 130" width="1.95in" height="1.27in" xmlns="http://www.w3.org/2000/svg">
  <path d="M20 108 C 18 80, 40 78, 44 60 S 30 26, 58 18 S 96 30, 104 22 S 150 6, 164 26
           S 150 58, 172 70 S 196 104, 168 112 S 128 96, 112 108 S 70 124, 52 112 S 26 118, 20 108 Z"
        fill="none" stroke="{LIME}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
  <path d="M20 108 C 18 80, 40 78, 44 60 S 30 26, 58 18 S 96 30, 104 22 S 150 6, 164 26
           S 150 58, 172 70 S 196 104, 168 112 S 128 96, 112 108 S 70 124, 52 112 S 26 118, 20 108 Z"
        fill="none" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 5" opacity=".55"/>
  <circle cx="20" cy="108" r="7" fill="{INK}" stroke="{LIME}" stroke-width="3"/>
  <circle cx="20" cy="108" r="2.5" fill="{LIME}"/>
  {''.join(f'<circle cx="{x}" cy="{y}" r="3.2" fill="white"/>' for x, y in
           [(44, 60), (58, 18), (104, 22), (164, 26), (172, 70), (168, 112), (112, 108), (52, 112)])}
</svg>"""


def elevation_svg():
    pts = [0, 6, 4, 12, 30, 44, 38, 20, 16, 26, 58, 64, 40, 22, 18, 10, 14, 8, 4, 2]
    step = 200 / (len(pts) - 1)
    line = " ".join(f"{i * step:.1f},{60 - p * 0.8:.1f}" for i, p in enumerate(pts))
    return f"""
<svg viewBox="0 0 200 64" width="2.2in" height="0.62in" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
  <polygon points="0,64 {line} 200,64" fill="{LIME}" opacity=".22"/>
  <polyline points="{line}" fill="none" stroke="{LIME}" stroke-width="2.4" stroke-linejoin="round"/>
</svg>"""


def splits_svg():
    paces = [5.12, 5.03, 4.58, 5.20, 4.49, 4.55, 5.31, 4.44]
    bars = ""
    for i, p in enumerate(paces):
        h = (p - 4.3) * 52
        bars += (f'<rect x="{6 + i * 24}" y="{56 - h:.1f}" width="15" height="{h:.1f}" rx="2" '
                 f'fill="{LIME if p < 4.6 else "white"}"/>')
    return f'<svg viewBox="0 0 200 60" width="2.2in" height="0.6in" xmlns="http://www.w3.org/2000/svg">{bars}</svg>'


M = 0.45                          # margin from every trim edge, inches
CW = TRIM_W - 2 * M               # content width on each panel
TOP = BLEED + 0.42                # top of the first line of type

FONTS = """
@font-face { font-family: Brico; src: url(fonts/BricolageGrotesque-ExtraBold.ttf); font-weight: 800; }
@font-face { font-family: Brico; src: url(fonts/BricolageGrotesque-Bold.ttf); font-weight: 700; }
@font-face { font-family: Brico; src: url(fonts/BricolageGrotesque-Medium.ttf); font-weight: 500; }
@font-face { font-family: Mono; src: url(fonts/JetBrainsMono-Bold.ttf); font-weight: 700; }
@font-face { font-family: Mono; src: url(fonts/JetBrainsMono-Medium.ttf); font-weight: 500; }
@font-face { font-family: Hand; src: url(fonts/Caveat-Bold.ttf); }
"""

TITLE_LINES = [("THE RUNNER’S GUIDE TO", "-0.01em"), ("NORMAL", "-0.045em"), ("CONVERSATION", "-0.035em")]


def fit_title():
    """Font sizes that make every title line exactly the content width."""
    probe = "".join(f'<div style="font: 800 100pt/1.3 Brico; letter-spacing: {ls}; white-space: nowrap">{t}</div>'
                    for t, ls in TITLE_LINES)
    pdf = HTML(string=f"<style>{FONTS}@page {{ size: 30in 10in; margin: 0 }}</style>{probe}",
               base_url=str(HERE) + "/").write_pdf()
    page = pymupdf.open("pdf", pdf)[0]
    widths = {}
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(sp["text"] for sp in line["spans"]).strip()
            x0 = min(sp["bbox"][0] for sp in line["spans"])
            x1 = max(sp["bbox"][2] for sp in line["spans"])
            widths[text] = (x1 - x0) / 72
    # letter-spacing adds space after the last glyph too; the ink width is what we fit
    return [round(100 * CW / widths[t], 2) for t, _ in TITLE_LINES]


def tail(direction, fill, w=0.42, h=0.34):
    pts = "0,0 60,0 8,100" if direction == "left" else "40,0 100,0 92,100"
    return (f'<svg viewBox="0 0 100 100" preserveAspectRatio="none" width="{w}in" height="{h}in" '
            f'xmlns="http://www.w3.org/2000/svg"><polygon points="{pts}" fill="{fill}"/></svg>')


def html():
    back_paras = "".join(f"<p>{p}</p>" for p in BACK_COPY.split("\n\n"))
    f = FRONT
    k, n, c = fit_title()
    fx = f + M                     # front content left
    bx = BLEED + M                 # back content left
    barcode_x = BLEED + TRIM_W - 0.25 - 2.0
    barcode_y = HEIGHT - BLEED - 0.25 - 1.2
    bottom = HEIGHT - BLEED - M    # baseline area of the last line
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{TITLE}</title><style>
{FONTS}
@page {{ size: {WIDTH}in {HEIGHT}in; margin: 0; }}
html, body {{ margin: 0; }}
body {{ width: {WIDTH}in; height: {HEIGHT}in; position: relative; background: {ORANGE};
        font-family: Brico; color: {INK}; overflow: hidden; }}
.a {{ position: absolute; }}
.col {{ width: {CW}in; }}

/* ---------- front ---------- */
.front {{ left: {fx}in; top: {TOP}in; }}
.t {{ font-weight: 800; white-space: nowrap; }}
.t1 {{ font-size: {k}pt; line-height: 1; letter-spacing: -0.01em; }}
.t2 {{ font-size: {n}pt; line-height: 0.80; letter-spacing: -0.045em; color: white; margin: 0.07in 0 0 -0.02in; }}
.t3 {{ font-size: {c}pt; line-height: 0.92; letter-spacing: -0.035em; margin-top: 0.07in; }}

.q {{ margin-top: 0.50in; position: relative; }}
.qb {{ display: inline-block; background: white; border-radius: 16pt; padding: 11pt 18pt 12pt;
       font: 700 17pt/1 Brico; }}
.q .tl {{ position: absolute; left: 0.28in; bottom: -0.30in; }}

.big {{ margin-top: 0.46in; position: relative; background: {INK}; border-radius: 18pt;
        padding: 0.24in 0.26in 0.22in; color: white; }}
.big .tl {{ position: absolute; right: 0.55in; bottom: -0.32in; }}
.lead {{ font: 700 13pt/1.2 Brico; margin: 0; }}
.lead span, .lime {{ color: {LIME}; }}
div.stats {{ display: flex; justify-content: space-between; margin: 0.18in 0 0.18in; }}
div.stats b {{ display: block; font: 700 17pt/1 Mono; color: {LIME}; letter-spacing: -0.02em; }}
div.stats i {{ display: block; font: 500 7.6pt/1.4 Mono; font-style: normal; color: #bdb3ab; letter-spacing: .08em; }}
table.charts {{ width: 100%; border-collapse: collapse; }}
table.charts td {{ padding: 0; vertical-align: top; }}
.rlabel {{ font: 500 7.6pt/1 Mono; color: #bdb3ab; letter-spacing: .08em; margin-bottom: 5pt; }}
.gap {{ height: 0.12in; }}
.tailtext {{ font: 700 10.6pt/1.25 Brico; white-space: nowrap; margin: 0.14in 0 0; }}

.sticker {{ left: {f + TRIM_W - M - 1.42}in; top: 2.98in; width: 1.5in; height: 1.5in; border-radius: 50%;
            background: {LIME}; transform: rotate(11deg);
            display: flex; align-items: center; justify-content: center; text-align: center; }}
.sticker div {{ font: 800 9pt/1.14 Brico; text-transform: uppercase; }}
.sticker div span {{ display: block; font: 800 17pt/1 Brico; margin: 3pt 0 2pt; }}

.foot {{ left: {fx}in; top: {bottom - 0.42}in; height: 0.42in; display: flex; align-items: flex-end;
         justify-content: space-between; }}
.sub {{ width: 3.55in; font: 700 11.5pt/1.2 Brico; }}
.author {{ font: 800 11.5pt/1.2 Brico; letter-spacing: .08em; text-transform: uppercase; white-space: nowrap; }}

/* ---------- back ---------- */
.back {{ left: {bx}in; top: {TOP}in; }}
.b-hand {{ font: 26pt/1 Hand; transform: rotate(-3deg); transform-origin: left; margin-left: 2pt; }}
.b-head {{ font: 800 33pt/0.98 Brico; letter-spacing: -0.03em; color: white; margin-top: 0.06in; }}
.card {{ margin-top: 0.38in; background: {CREAM}; border-radius: 14pt; padding: 0.26in 0.28in 0.18in; }}
.card .lab {{ font: 700 7.6pt/1 Mono; letter-spacing: .14em; color: {ORANGE}; margin-bottom: 10pt; }}
.card p {{ font: 500 10.6pt/1.42 Brico; margin: 0 0 7pt; }}
.card p:first-of-type {{ font: 800 13pt/1.25 Brico; }}
.row {{ margin-top: 0.40in; display: flex; justify-content: space-between; align-items: flex-start; }}
.inside {{ width: 2.85in; }}
.lab2 {{ font: 700 7.6pt/1.25 Mono; letter-spacing: .1em; margin-bottom: 8pt; }}
.inside div.i {{ font: 700 9.6pt/1.25 Brico; margin: 0 0 6pt; padding-left: 17pt; position: relative; }}
.inside div.i::before {{ content: ""; position: absolute; left: 0; top: 1pt; width: 9pt; height: 9pt;
                         border: 1.6pt solid {INK}; border-radius: 2pt; background: {LIME}; }}
.side {{ width: 2.0in; border: 1.6pt solid {INK}; border-radius: 8pt; padding: 9pt 10pt 10pt; box-sizing: border-box; }}
.side p {{ font: 500 8.8pt/1.3 Brico; margin: 0; }}
.imprint {{ left: {bx}in; top: {bottom - 0.11}in; font: 700 7.6pt/1 Mono; letter-spacing: .12em; }}
.barcode {{ left: {barcode_x}in; top: {barcode_y}in; width: 2.0in; height: 1.2in; background: white; }}
</style></head><body>

<!-- FRONT -->
<div class="a front col">
  <div class="t t1">{TITLE_LINES[0][0]}</div>
  <div class="t t2">{TITLE_LINES[1][0]}</div>
  <div class="t t3">{TITLE_LINES[2][0]}</div>
  <div class="q"><div class="qb">How was your weekend?</div><div class="tl">{tail("left", "white")}</div></div>
  <div class="big">
    <p class="lead">Well, I was up at <span>06:15</span>, porridge, then —</p>
    <div class="stats">
      <div><b>21.1</b><i>KM</i></div><div><b>4:58</b><i>AVG /KM</i></div>
      <div><b>1:44:52</b><i>MOVING TIME</i></div><div><b>162</b><i>AVG BPM</i></div>
    </div>
    <table class="charts"><tr>
      <td><div class="rlabel">ROUTE (THE LONG WAY)</div>{route_svg()}</td>
      <td style="width:2.2in"><div class="rlabel">SPLITS</div>{splits_svg()}<div class="gap"></div>
          <div class="rlabel">ELEVATION</div>{elevation_svg()}</td>
    </tr></table>
    <p class="tailtext">…and that’s when the headwind started, near the retail park…</p>
    <div class="tl">{tail("right", INK)}</div>
  </div>
</div>
<div class="a sticker"><div>For anyone who<br>has heard about<span>the 10K PB</span>more than once</div></div>
<div class="a foot col"><div class="sub">{SUBTITLE}</div><div class="author">{AUTHOR}</div></div>

<!-- BACK -->
<div class="a back col">
  <div class="b-hand">You asked one question.</div>
  <div class="b-head">This is what<br>happened next.</div>
  <div class="card"><div class="lab">PATIENT INFORMATION LEAFLET</div>{back_paras}</div>
  <div class="row">
    <div class="inside">
      <div class="lab2">INSIDE THIS MANUAL</div>
      <div class="i">A severity test for Runner’s Conversational Capture</div>
      <div class="i">36 exercises, quizzes and worksheets</div>
      <div class="i">A cut-out emergency conversation card</div>
      <div class="i">A certificate of conditional discharge</div>
    </div>
    <div class="side"><div class="lab2" style="letter-spacing:.03em">SIDE EFFECTS MAY INCLUDE</div>
      <p>Listening. Eye contact. Knowing the name of a colleague’s partner. Answering “How was your weekend?” in under twenty minutes.</p></div>
  </div>
</div>
<div class="a imprint">HUMOUR · GIFT</div>
</body></html>"""


def previews():
    d = pymupdf.open(OUT)
    page = d[0]
    stem = OUT.stem
    # Preview only: show where KDP prints its barcode (2 x 1.2 in, 0.25 in from the trim).
    shape = page.new_shape()
    x1 = (BLEED + TRIM_W - 0.25) * 72
    y1 = (HEIGHT - BLEED - 0.25) * 72
    shape.draw_rect(pymupdf.Rect(x1 - 2.0 * 72, y1 - 1.2 * 72, x1, y1))
    shape.finish(color=(1, 1, 1), width=1.2, dashes="[4 3] 0")
    shape.commit()
    page.insert_textbox(pymupdf.Rect(x1 - 2.0 * 72, y1 - 0.68 * 72, x1, y1 - 0.4 * 72),
                        "KDP barcode (added by KDP)", fontsize=8, color=(1, 1, 1), align=1)
    page.get_pixmap(dpi=130).save(HERE / "proposals" / f"{stem}-full-wrap.png")
    front = pymupdf.Rect(FRONT * 72, 0, WIDTH * 72, HEIGHT * 72)
    page.get_pixmap(dpi=150, clip=front).save(HERE / "proposals" / f"{stem}-front-print.png")
    page.get_pixmap(dpi=24, clip=front).save(HERE / "proposals" / f"{stem}-amazon-thumbnail.png")


def check():
    """Run Book Factory's own cover checks with the 58-page dimensions."""
    import sys
    sys.path.insert(0, str(BOOK.parent.parent))
    from bookfactory.core import cover
    from bookfactory.core.book import Book

    book = Book.load(BOOK.name)
    dims = {"page_count": PAGES, "paper": "white", "spine_in": SPINE, "width_in": WIDTH,
            "height_in": HEIGHT, "trim_width_in": TRIM_W, "trim_height_in": TRIM_H, "bleed_in": BLEED}
    cover.dimensions = lambda _book: dims
    cover.artwork_mode = lambda _data: cover.TEXT_ONLY   # vector design, no raster artwork
    return cover.check_pdf(book, OUT)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    HTML(string=html(), base_url=str(HERE) + "/").write_pdf(OUT)
    previews()
    print(f"{OUT.name}: {WIDTH:.4f} x {HEIGHT:.3f} in, spine {SPINE:.4f} in for {PAGES} pages")
    problems = check()
    print("cover check:", "pass" if not problems else problems)
