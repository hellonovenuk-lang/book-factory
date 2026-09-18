# Book Factory - operating instructions for Claude

You are working inside a Book Factory repository. Read `AGENTS.md` first - those
rules apply to you. This file adds what is specific to Claude, which usually
means having filesystem and shell access, and therefore more ways to do damage.

---

## Starting a session

Whatever the user says, begin by reading the repository:

```bash
bookfactory status <book-id>
bookfactory next <book-id>
```

If the user says only "continue Book Factory project golf-addict", those two
commands are the entire briefing. You do not need the previous conversations and
should not ask for them.

If no book id is given: `bookfactory list`.

## Two different jobs

Be clear which one you are doing, because the rules differ.

### Operating a book

You are using Book Factory to produce a book: writing briefs, manuscripts, page
specs, planning pages, rendering, running QA.

Follow `AGENTS.md` exactly. In particular: one task at a time, never approve,
never touch approved artefacts, never skip a gate.

You have shell access, which means you *could* write straight into
`pages/approved/`, `chmod` a read-only file, or hand-edit `manifest.json`.
Do not. Every one of those bypasses a check that exists because of a real
failure. Use the CLI.

The one legitimate exception is repairing state the system itself cannot
repair - a hand-corrupted manifest, for instance. Say clearly that you are doing
it, say why, and run `bookfactory validate` afterwards.

### Maintaining Book Factory itself

You are changing the code in `bookfactory/`, the templates, or the schemas.

* Run `pytest` before you finish. The suite exists to stop production mistakes.
* Run `python scripts/build_demo_book.py`. It walks the whole pipeline and fails
  if anything is broken end to end.
* If you touch page CSS or templates, check both render backends - WeasyPrint
  and Chromium disagree, and the disagreement shows up as missing body copy.
  `docs/RENDERING.md` has the detail.
* Keep business logic in `bookfactory/core/`. The CLI is an adapter. If you find
  yourself writing a rule inside a CLI command handler, it belongs in `api.py`
  or `book.py`.

## Writing copy

If you are drafting a brief, manuscript or page copy:

1. Read `style/voice-bible.md` and treat it as binding, banned phrases included.
2. Read `manuscript/writing-sample.md` and match it - that is what the operator
   approved.
3. Avoid the constructions content QA flags: the "it's not X, it's Y" shape,
   corporate vocabulary, three-part aphorisms used as rhythm, stacked one-line
   paragraphs for false emphasis.
4. Copy goes into the page spec, never into an image prompt.

Write it properly the first time rather than generating something and letting QA
catch it.

## Images

Claude does not generate images. When the next task is an illustration, say so
and hand it over:

> The next task is illustration `p058-mate-taxonomy`. I cannot generate images.
> Run `bookfactory task golf-addict --json`, give that to ChatGPT along with
> `integrations/chatgpt/BOOK_FACTORY.md`, and it will generate and submit the
> draft.

Then stop. Do not substitute a placeholder, do not describe the picture in the
page spec as if it existed, and do not advance past it.

## Reporting back

Report in terms of the repository, not in terms of effort:

> Rendered p058 and submitted it as draft v1
> (`pages/drafts/p058/p058-v1.pdf`, sha256 4f2a...).
> `bookfactory next` now asks you to approve it. Nothing is approved until you
> run the command.

If you ran QA or preflight, give the status and the findings that need a human,
not a summary of the report.
