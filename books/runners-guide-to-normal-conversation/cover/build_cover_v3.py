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


def bubble_svg(w, h, fill, tail, stroke=None, sw=0):
    """A rounded speech bubble w x h inches, tail 'bl' (bottom left) or 'br'."""
    W, H = w * 72, h * 72
    r = 22
    st = f'stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    if tail == "bl":
        t = f"M{W * 0.14} {H - 1} L{W * 0.06} {H + 30} L{W * 0.30} {H - 1} Z"
    else:
        t = f"M{W * 0.70} {H - 1} L{W * 0.93} {H + 34} L{W * 0.86} {H - 1} Z"
    return (f'<svg viewBox="-4 -4 {W + 8} {H + 42}" width="{w + 8 / 72:.3f}in" height="{h + 46 / 72:.3f}in" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<path d="{t}" fill="{fill}" {st}/>'
            f'<rect x="0" y="0" width="{W}" height="{H}" rx="{r}" fill="{fill}" {st}/>'
            f'<path d="{t}" fill="{fill}"/></svg>')


def html():
    back_paras = "".join(f"<p>{p}</p>" for p in BACK_COPY.split("\n\n"))
    f = FRONT  # front fold
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{TITLE}</title><style>
@font-face {{ font-family: Brico; src: url(fonts/BricolageGrotesque-ExtraBold.ttf); font-weight: 800; }}
@font-face {{ font-family: Brico; src: url(fonts/BricolageGrotesque-Bold.ttf); font-weight: 700; }}
@font-face {{ font-family: Brico; src: url(fonts/BricolageGrotesque-Medium.ttf); font-weight: 500; }}
@font-face {{ font-family: Mono; src: url(fonts/JetBrainsMono-Bold.ttf); font-weight: 700; }}
@font-face {{ font-family: Mono; src: url(fonts/JetBrainsMono-Medium.ttf); font-weight: 500; }}
@font-face {{ font-family: Hand; src: url(fonts/Caveat-Bold.ttf); }}
@page {{ size: {WIDTH}in {HEIGHT}in; margin: 0; }}
html, body {{ margin: 0; }}
body {{ width: {WIDTH}in; height: {HEIGHT}in; position: relative; background: {ORANGE};
        font-family: Brico; color: {INK}; overflow: hidden; }}
.a {{ position: absolute; }}

/* ---------- front ---------- */
.kicker {{ left: {f + 0.42}in; top: 0.62in; font: 800 21pt/1 Brico; letter-spacing: -0.01em; white-space: nowrap; }}
.normal {{ left: {f + 0.34}in; top: 0.90in; font: 800 90pt/0.86 Brico; letter-spacing: -0.045em; color: white; }}
.convo {{ left: {f + 0.40}in; top: 2.06in; font: 800 49pt/0.9 Brico; letter-spacing: -0.035em; }}

.q {{ left: {f + 0.30}in; top: 3.36in; }}
.qtext {{ left: {f + 0.52}in; top: 3.51in; font: 700 17pt/1 Brico; }}
.big {{ left: {f + 0.30}in; top: 4.30in; }}
.ans {{ left: {f + 0.56}in; top: 4.50in; width: 4.9in; color: white; }}
.ans .lead {{ font: 700 13pt/1.2 Brico; margin: 0 0 6pt; }}
.ans .lead span {{ color: {LIME}; }}
.stats {{ left: {f + 0.56}in; top: 5.02in; width: 4.95in; }}
.stat {{ display: inline-block; margin-right: 11pt; vertical-align: top; }}
.stat b {{ display: block; font: 700 17pt/1 Mono; color: {LIME}; letter-spacing: -0.02em; }}
.stat i {{ display: block; font: 500 7.6pt/1.3 Mono; font-style: normal; color: #bdb3ab; letter-spacing: .08em; }}
.route {{ left: {f + 0.50}in; top: 5.62in; }}
.rlabel {{ font: 500 7.6pt/1 Mono; color: #bdb3ab; letter-spacing: .08em; }}
.splits {{ left: {f + 2.95}in; top: 5.62in; }}
.elev {{ left: {f + 2.95}in; top: 6.42in; }}
.tail {{ left: {f + 0.56}in; top: 7.22in; width: 5.0in; font: 700 11.2pt/1.25 Brico; color: white; }}
.tail span {{ color: #8f857d; }}
.note {{ left: {f + 3.72}in; top: 3.28in; font: 22pt/0.9 Hand; transform: rotate(-6deg); width: 2.1in; }}
.arrow {{ left: {f + 3.25}in; top: 3.62in; }}

.sticker {{ left: {f + 4.12}in; top: 3.05in; width: 1.62in; height: 1.62in; border-radius: 50%;
            background: {LIME}; transform: rotate(11deg); text-align: center; }}
.sticker div {{ padding-top: 0.30in; font: 800 9.6pt/1.12 Brico; letter-spacing: .01em; text-transform: uppercase; }}
.sticker div span {{ display: block; font: 800 18pt/1 Brico; margin: 2pt 0; }}

.sub {{ left: {f + 0.42}in; top: 8.10in; width: 3.9in; font: 700 11.5pt/1.2 Brico; }}
.author {{ left: {f + 4.26}in; top: 8.30in; width: 1.55in; text-align: right; font: 800 12pt/1 Brico;
           letter-spacing: .08em; text-transform: uppercase; }}

/* ---------- back ---------- */
.b-top {{ left: 0.55in; top: 0.62in; width: 5.0in; }}
.b-hand {{ font: 25pt/1 Hand; transform: rotate(-3deg); margin: 0 0 4pt 4pt; }}
.b-head {{ font: 800 30pt/0.98 Brico; letter-spacing: -0.03em; color: white; }}
.card {{ left: 0.50in; top: 2.12in; width: 5.10in; background: {CREAM}; border-radius: 14pt;
         padding: 20pt 22pt 16pt; box-sizing: border-box; }}
.card .lab {{ font: 700 7.4pt/1 Mono; letter-spacing: .14em; color: {ORANGE}; margin-bottom: 9pt; }}
.card p {{ font: 500 10.6pt/1.42 Brico; margin: 0 0 7pt; }}
.card p:first-of-type {{ font: 800 13pt/1.25 Brico; }}
.inside {{ left: 0.55in; top: 5.95in; width: 2.95in; }}
.inside .lab {{ font: 700 7.4pt/1 Mono; letter-spacing: .14em; margin-bottom: 7pt; }}
.inside div.i {{ font: 700 9.6pt/1.25 Brico; margin: 0 0 5pt; padding-left: 17pt; position: relative; }}
.inside div.i::before {{ content: ""; position: absolute; left: 0; top: 1pt; width: 9pt; height: 9pt;
                         border: 1.6pt solid {INK}; border-radius: 2pt; background: {LIME}; }}
.side {{ left: 3.62in; top: 5.95in; width: 2.0in; border: 1.6pt solid {INK}; border-radius: 8pt;
         padding: 8pt 9pt; box-sizing: border-box; }}
.side .lab {{ font: 700 7.2pt/1.25 Mono; letter-spacing: .04em; margin-bottom: 5pt; }}
.side p {{ font: 500 8.6pt/1.3 Brico; margin: 0; }}
.imprint {{ left: 0.55in; top: 8.55in; font: 700 7.4pt/1 Mono; letter-spacing: .12em; }}
.barcode {{ left: {BLEED + TRIM_W - 2.25}in; top: {HEIGHT - 1.62}in; width: 2.1in; height: 1.3in;
            background: white; }}
</style></head><body>

<!-- FRONT -->
<div class="a kicker">THE RUNNER’S GUIDE TO</div>
<div class="a normal">NORMAL</div>
<div class="a convo">CONVERSATION</div>

<div class="a q">{bubble_svg(3.18, 0.62, "white", "bl")}</div>
<div class="a qtext">How was your weekend?</div>

<div class="a big">{bubble_svg(5.42, 3.42, INK, "br")}</div>
<div class="a ans"><p class="lead">Well, I was up at <span>06:15</span>, porridge, then —</p></div>
<div class="a stats">
  <div class="stat"><b>21.1</b><i>KM</i></div>
  <div class="stat"><b>4:58</b><i>AVG /KM</i></div>
  <div class="stat"><b>1:44:52</b><i>MOVING TIME</i></div>
  <div class="stat"><b>162</b><i>AVG BPM</i></div>
</div>
<div class="a route"><div class="rlabel">ROUTE (THE LONG WAY)</div>{route_svg()}</div>
<div class="a splits"><div class="rlabel">SPLITS</div>{splits_svg()}</div>
<div class="a elev"><div class="rlabel">ELEVATION</div>{elevation_svg()}</div>
<div class="a tail">…and that’s when the headwind started, near the retail park…</div>

<div class="a sticker"><div>For anyone who<br>has heard about<span>the 10K PB</span>more than once</div></div>
<div class="a sub">{SUBTITLE}</div>
<div class="a author">{AUTHOR}</div>

<!-- BACK -->
<div class="a b-top">
  <div class="b-hand">You asked one question.</div>
  <div class="b-head">This is what happened next.</div>
</div>
<div class="a card"><div class="lab">PATIENT INFORMATION LEAFLET</div>{back_paras}</div>
<div class="a inside">
  <div class="lab">INSIDE THIS MANUAL</div>
  <div class="i">A severity test for Runner’s Conversational Capture</div>
  <div class="i">36 exercises, quizzes and worksheets</div>
  <div class="i">A cut-out emergency conversation card</div>
  <div class="i">A certificate of conditional discharge</div>
</div>
<div class="a side"><div class="lab">SIDE EFFECTS MAY INCLUDE</div>
  <p>Listening. Eye contact. Knowing the name of a colleague’s partner. Answering “How was your weekend?” in under twenty minutes.</p></div>
<div class="a imprint">HUMOUR · GIFT</div>
<div class="a barcode"></div>
</body></html>"""


def previews():
    d = pymupdf.open(OUT)
    page = d[0]
    stem = OUT.stem
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
