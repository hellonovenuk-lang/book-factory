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

## The `activity` page type

Most page types hold fixed copy fields. `activity` is different: it holds a
numbered panel built from an ordered list of `blocks`, so one page type
covers ticks, checklists, score boxes, write-in lines, tables, gauges,
cycles, cut-out cards and casenotes - all typeset, none of it a generated
picture. Nothing an `activity` page draws counts against the picture budget
(`AGENTS.md` section 5a); it is real type, not artwork.

Copy fields: `heading` (the panel title), optional `eyebrow`, `subheading`,
`panel_number` (e.g. `"No. 01"`), `panel_kind` (e.g. `"Assessment"`, shown as
`"No. 01 · Assessment"`), `instructions`, `body` (intro paragraphs),
`blocks` (required, rendered in order inside the panel), and `footnote`.

Block types:

| Block | Fields | Renders as |
| --- | --- | --- |
| `prose` | `text` | A paragraph. |
| `ticks` | `items`, optional `start` | Numbered statements, each with a tick box. |
| `checklist` | `items` | Plain tick boxes. |
| `score` | optional `label`, `out_of` | A "Score: ___ out of N" line. |
| `lines` | `count`, optional `label` | That many write-in lines. |
| `table` | `headers`, `rows`, optional `widths` | A table. An empty cell is a write-in cell; a cell starting `"[ ]"` gets a tick box. |
| `casenote` | `label`, `text` | A labelled note, styled like a quoted case note. |
| `gauge` | `bands: [{range, label}]` | A typeset graded bar, its bands and labels set as real type. |
| `cycle` | `steps` | Typeset boxes joined by arrows, looping back to the first. |
| `cutout` | optional `heading`, `text` | A dashed cut-out card. |
| `signature` | `fields` | Signature/date lines. |

An unknown block type is an error, not a silent skip.

Example - the Golf Addict's Guide's opening assessment
(`books/golf-addicts-guide-to-family-reintegration/manuscript/manuscript.md`,
"No. 01 · Assessment"), trimmed to a few items:

```json
{
  "type": "activity",
  "copy": {
    "panel_number": "No. 01",
    "panel_kind": "Assessment",
    "heading": "Initial assessment",
    "instructions": "Award yourself one point for each statement that is true. Sue will check your answers.",
    "blocks": [
      {
        "type": "ticks",
        "items": [
          "You have gone out for \"a quick nine\" and come back in the dark.",
          "You have practised your swing with an umbrella in the queue at the post office, and the queue moved back.",
          "You have mentioned the 7th hole at a christening."
        ]
      },
      {
        "type": "score",
        "out_of": 10
      }
    ]
  }
}
```

The severity gauge that follows the score ("Reading your score") is a
`gauge` block, not a generated illustration:

```json
{
  "type": "gauge",
  "bands": [
    {"range": "0-2", "label": "You may have been sent this book by mistake."},
    {"range": "3-6", "label": "Moderate. The Programme can help."},
    {"range": "7-9", "label": "Severe. Your family now call it \"his other house\"."},
    {"range": "10", "label": "Report to Stage One immediately."}
  ]
}
```

This is the way to put diagrams and labelled panels into a book without
generating any artwork for them (`AGENTS.md` sections 5 and 5a): every word
in every block, including a diagram's labels, is set by the renderer from
the spec, the same as any other page's copy.

## `palette_sheet`

A page type for the "palette and type rules" reference (`ref-palette` in
the default reference set, `docs/OPERATOR.md` step 5). It takes no page
copy of its own: it reads the book's palette and type scale straight from
`style/design-tokens.json` and draws swatches (each with its hex value set
as type) and a sample of the type hierarchy (heading, subheading, body,
caption at their real sizes and fonts). Because it is generated from the
design tokens rather than written by hand, it can never drift out of sync
with the values the rest of the book actually uses.

## Sample pages for the reference set: `reference render`

The reference set (`AGENTS.md` section 6, `docs/OPERATOR.md` step 5) needs
typeset examples before any real page exists - a chapter opener, a normal
internal page, a diagnostic/checklist page, the palette sheet. Writing and
approving one of these full pages is exactly the render path above, just
pointed at a reference asset instead of a page in the manifest:

```bash
bookfactory reference render <book> <asset-id> --from-file <spec.json> [--dpi 300] [--json]
```

It takes an ordinary page spec, renders it as a one-page sample through the
same templates and backend as a real page - but it is never added to the
page manifest - rasterises the result to a 300-DPI PNG, and submits that PNG
as a new draft of an already-registered reference asset, through the same
path `submit` uses, so the same measured checks (section "The copy check",
`AGENTS.md` section 6a) run on it. Register the asset first, if it is not
already registered, with the `deterministic_layout` reference role so it can
never leak into a real illustration task:

```bash
bookfactory asset add <book> ref-page-diagnostic --kind reference \
  --title "Diagnostic page example" --reference-role deterministic_layout
```

A sample spec may place an already-approved reference picture (for example
`ref-character-main`) via its normal `illustration.asset_id`, the same as
any page spec; the sample itself is still just typeset layout being proved,
not new artwork. Approving the resulting draft follows the normal rule
(`AGENTS.md` section 3): the operator, or `--autonomous` when the book's
recorded production policy authorizes it and the task's `mode` is
`continue_automatically`.

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
