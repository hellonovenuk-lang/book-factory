# Book Factory - architecture

This document is for whoever maintains the code. For operating a book, read
`docs/OPERATOR.md`. For the rules an AI agent must follow, read `AGENTS.md`.

## The shape of the thing

```
        page specification            approved illustration assets
       (exact words, versioned)          (pictures, immutable)
                    \                          /
                     \                        /
                      +---> deterministic renderer <---+ design tokens
                                    |                     (type, palette,
                                    v                      margins, trim)
                            one finished page
                                    |
                                    v
                       explicit operator approval
                                    |
                                    v
                    pages/approved/<id>-<slug>.pdf   (read-only, checksummed)
                                    |
                                    v
                        deterministic assembly
                                    |
                                    v
                            output/interior.pdf
```

Everything else is bookkeeping around that pipeline.

## Design decisions, and why

### The repository is the source of truth

No database. State is JSON and Markdown in a git repository, because:

* any agent, any vendor, any language can read it;
* `git log` is the audit trail of last resort;
* a human can open a file and see what is happening;
* it survives the tool that made it.

`books/<book-id>/book.json` is the entry point. It is deliberately small - a
dashboard, not a data store - and it carries a cached copy of the next action so
that reading one file answers "where is this book and what happens next?".
Every command that changes the book refreshes that cache and `tasks/open/`.

Looking never writes. `status`, `next`, `task` and `validate` change nothing in
the repository; they recompute the stage and next task in memory. `qa` writes
its report (`qa/reports/` and `qa/latest.json`, which later stages read) and
nothing else. `next --persist` is the explicit way to refresh the cached next
action and `tasks/open/` without changing anything else - useful after
hand-editing a file, for an agent that reads the repository without a shell.

### Generative and deterministic work are separated by construction

An image model cannot spell, cannot count pages, and cannot be relied on to
letter a diagram twice the same way. So it never does any of those things.

* **Generative:** illustrations, characters, scenes, decorative artwork.
* **Deterministic:** all typography, page numbers, headings, captions, tables,
  checklists, quizzes, contents, footers, page geometry.

Pages are HTML and CSS rendered to PDF. HTML was chosen over a drawing API
because it gives exact trim boxes, real typography, reusable templates, and a
file you can open in a browser when a layout looks wrong. Every render also
writes its HTML to `pages/renders/html/` for exactly that reason.

Two backends are supported: WeasyPrint (default, pure Python) and Chromium.
Renders are byte-reproducible: `SOURCE_DATE_EPOCH` is pinned and PDF metadata is
normalised, so an unchanged page re-renders to an identical checksum.

After every render the system extracts the text back out of the PDF and checks
that every word the spec requires is actually present. A fixed-height page clips
copy that does not fit rather than reflowing it, and silently losing the end of
a sentence is precisely the kind of quiet damage this system exists to prevent.
This check has already caught one backend laying a page out differently from
another.

### Approved artefacts are immutable, in two layers

1. **Permissions.** Promotion sets the file to `0444`. An accidental overwrite
   fails at the OS level. This is best-effort: root ignores permission bits.
2. **Checksums.** The manifest records a SHA-256 for every approved artefact.
   QA, `validate` and assembly all recompute it. This is the layer that actually
   guarantees the artefact, and it is never weakened.

Replacing approved work requires `bookfactory revise`, which:

* leaves the current approved file canonical, so the book stays assemblable;
* marks the record as having an open revision;
* requires a fresh explicit approval, which archives the previous version into
  `_history/` with the reason it was superseded.

Nothing is ever deleted. Rejected drafts stay on disk, because regenerating
something that was already rejected is itself a failure mode.

### Identity is the id, never the title

Canonical filenames lead with the id: `p058-the-golf-mate-taxonomy.pdf`. Two
pages cannot collide however similar their titles, and the manifest detects it
if a record somehow claims a path another record already has.

### Stages are derived, not declared

A book has exactly one stage, and it is recomputed from evidence on disk after
every state change (`Book.autoadvance`); read-only commands report the same
derived stage without recording it (`Book.derived_stage`). A stage is never a
flag somebody remembered to set. Two kinds of stage are exempt: the four lock stages, which
require an explicit `bookfactory lock`, and release ready, which is the
operator's call.

Gates (`bookfactory/core/gates.py`) decide whether the book may move on, and a
blocked gate always returns the exact list of unmet conditions.

## Package map

```
bookfactory/
  core/
    api.py        the library API - everything callable, no CLI in it
    book.py       the Book aggregate; the only thing that writes to a project
    gates.py      production gates; pure, no mutation
    manifest.py   the page manifest
    registry.py   the asset registry
    tasks.py      the `next` engine - derives the next action from state alone
    models.py     typed views over the state files
    stages.py     the twenty-one production stages
    checksums.py  SHA-256 and approved-artefact protection
    paths.py      the canonical on-disk layout, in one place
    schema.py     JSON Schema validation on read and write
    audit.py      append-only JSONL event log
  render/
    renderer.py   spec + approved artwork + tokens -> one PDF page
    backends.py   WeasyPrint and Chromium, both made deterministic
    templates.py  Jinja loading for project and page templates
    assets/book.css  the editorial design system
  qa/             content, visual, technical and assembly checks
  assembly/       deterministic PDF assembly and review output
  kdp/            KDP profiles (data) and preflight (code)
  cli/            argparse front end, thin over core.api

schemas/          the published JSON Schema contract
templates/pages/  one HTML template per page type
templates/project/ the Markdown documents scaffolded into a new book
books/            the projects themselves
```

The CLI holds no business logic. Anything it can do, `bookfactory.core.api` can
do from Python, which is what makes an MCP server a small adapter rather than a
rewrite - see "Future MCP" below.

## A book on disk

```
books/<book-id>/
  book.json                 dashboard: stage, locks, versions, next action
  audit.jsonl               append-only log of meaningful events
  brief/                    what the book is and who buys it
  manuscript/
    manuscript.md           the working manuscript
    versions/               immutable locked snapshots, checksummed
    writing-sample.md       the voice calibration piece
  style/
    voice-bible.md          locked humour and voice rules
    visual-bible.md         locked art direction
    design-tokens.json      type scale, palette, margins, trim - the renderer reads this
    reference-set.json      which references must be approved before visual lock
  pages/
    manifest.json           THE PAGE MANIFEST - the authoritative page list
    specs/<page>.json       exact copy and illustration brief, per page
    drafts/<page>/          candidate renders, never deleted
    approved/               approved pages, read-only, checksummed
    approved/_history/      superseded approvals
    renders/                working renders and debug HTML (regenerable)
  assets/
    registry.json           illustration assets and visual references
    drafts/<asset>/         candidate artwork
    approved/               approved artwork, read-only, checksummed
  cover/
    cover.json              print cover settings, drafts, approval, cover preflight
    drafts/                 versioned full-wrap cover PDFs, never deleted
  tasks/open|done/          the current task, and the ones it replaced
  qa/                       QA reports
  output/                   interior.pdf, cover.pdf, review material (regenerable)
```

`output/` and `pages/renders/` are gitignored. Everything else is canonical and
belongs in version control.

## Schemas

`schemas/` holds the published contract: book state, page manifest, page spec,
asset registry, task, QA report, print cover. They are validated on write and on read, and
they exist as plain JSON Schema so a non-Python tool - ChatGPT, a future MCP
server - can check its own output before submitting it.

Schemas are versioned by `schema_version` on every document.

## QA

Four layers, reported separately because different people fix them:

* **content** - placeholders, missing copy for the page type, duplicate
  concepts, doubled words, drift from the locked manuscript, the AI
  constructions and banned phrases the voice bible forbids.
* **visual** - artwork exists, is approved, is intact, is above 300 DPI at its
  printed size, is not accidentally reused, and does not permit embedded text.
* **technical** - manifest integrity, trim size, page numbering, embedded fonts,
  gutter and outside margins against the KDP profile, checksums.
* **assembly** - the fail-closed gate: every page approved, every checksum good,
  no draft substituted, no sequence gaps.

Anything a machine cannot decide - is the joke landing, has the character
drifted - is reported as `needs_human` rather than quietly passed.

## KDP

Amazon changes its requirements, so they live in
`bookfactory/kdp/profiles/*.json` with a `captured_on` date, and nothing in the
code hard-codes a number. Preflight reads the profile and the assembled PDF.
Updating for a rule change is a data edit.

## Future MCP

The API surface was designed to map directly onto tool calls:

| MCP tool | Function |
| --- | --- |
| `book_factory.create_book` | `api.create_book` |
| `book_factory.status` | `api.status` |
| `book_factory.next_task` | `api.next_task` |
| `book_factory.get_task` | `api.get_task` |
| `book_factory.submit_asset` | `api.submit_asset` |
| `book_factory.approve` | `api.approve` |
| `book_factory.reject` | `api.reject` |
| `book_factory.qa` | `api.qa` |
| `book_factory.assemble` | `api.assemble` |

Each takes plain JSON-compatible arguments and returns a dict. The server is a
thin wrapper; it is deliberately not built yet, because the core had to be right
first.

## Testing

`pytest`. The fixtures build real projects on disk - real files, real checksums,
real rendered PDFs - because every failure this system prevents is a filesystem
failure and a mocked filesystem would prove nothing.

`books/demo-book/` is a complete worked example, rebuilt from scratch by
`scripts/build_demo_book.py`. If a change breaks the production pipeline, that
script fails.
