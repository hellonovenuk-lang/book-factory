# Rendering

## How a page is made

```
pages/specs/p012.json      the exact copy and the illustration brief
style/design-tokens.json   type scale, palette, margins, trim
assets/approved/...        the approved artwork
        |
        v
templates/pages/<type>.html.j2   +   bookfactory/render/assets/book.css
        |
        v
    HTML for one page
        |
        v
  WeasyPrint or Chromium
        |
        v
 pages/renders/p012.pdf     exactly 6x9in, one page, deterministic
```

Nothing generative happens at any step. The same inputs always produce the same
bytes.

## Backends

| Backend | When it is used |
| --- | --- |
| `weasyprint` | Default. Pure Python, no browser, installs with the package. |
| `chromium` | Used if WeasyPrint is unavailable, or with `--backend chromium`. Better CSS coverage. |

`bookfactory doctor` reports what is available. Force one with `--backend`, or
set `BOOKFACTORY_RENDER_BACKEND`.

**The backends do not render identically.** WeasyPrint's flexbox in particular
disagrees with Chromium's. The page CSS therefore avoids column flexbox for page
body layout and states illustration heights in inches. If you add CSS, check it
in both.

## Debugging a layout

Every render writes its HTML next to the PDF:

```
books/<book>/pages/renders/html/p012.html
```

Open it in a browser. It is the exact input the PDF was made from, with the CSS
inlined. Edit it, reload, work out what you want, then move the change into the
template or the design tokens - never into the rendered file, which is
regenerated.

## Determinism

* `SOURCE_DATE_EPOCH` is pinned during rendering.
* PDF metadata and the document ID are normalised afterwards.
* Result: re-rendering an unchanged page produces an identical SHA-256.

This is what makes checksums meaningful. If a render changes, something actually
changed.

## The copy check

After rendering, the text is extracted back out of the PDF and every word the
page spec requires is checked for. A page is a fixed-height box: copy that does
not fit is clipped, not reflowed, and clipping silently deletes the end of a
sentence.

If you see:

```
Page p012 rendered without copy the spec requires: ...
```

the page has more copy than fits. Shorten it, or split it into two pages in the
manifest. Do not work around the check.

## Page geometry

* Page box is the trim size from the KDP profile, exactly.
* With bleed enabled, the sheet grows by the bleed amount on the top, bottom and
  outer edges only. The gutter edge never bleeds.
* Margins are mirrored: the gutter is on the left of a recto (odd printed page)
  and on the right of a verso.
* Recto and verso are decided by the printed page number in the manifest.

Margins, type scale and palette all come from `style/design-tokens.json`, which
is per book. Changing a book's look is a data edit, not a code change.

## Adding a page type

1. Add `templates/pages/<type>.html.j2`, extending `_base.html.j2`.
2. Add the type to the enum in `schemas/page-manifest.schema.json`.
3. Add its required copy fields to `REQUIRED_COPY` in `bookfactory/qa/content.py`.
4. Add any new copy field names to `COPY_DEFAULTS` in
   `bookfactory/render/renderer.py` - templates run with strict undefined
   checking so that a typo in a spec fails loudly instead of rendering a page
   with a missing caption.

`tests/test_render.py` asserts that every page type in `REQUIRED_COPY` has a
template, so a half-added type fails the suite.

## Fonts

The default stack is Charter/DejaVu Serif with DejaVu Sans for accents - widely
available, and good for setting a book. To use licensed fonts, drop the files in
`books/<book>/style/fonts/`, reference them with `@font-face` and name them in
`design-tokens.json`.

KDP requires embedded fonts. Technical QA and preflight both check for this.
