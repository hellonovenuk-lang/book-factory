# Book Factory - operating instructions for Claude

**Since autonomous ChatGPT production mode was added, Claude Code is a
developer/maintenance tool for Book Factory - not a required part of normal
book production.** Normal production is: the user talks to ChatGPT Work,
ChatGPT reads and drives the repository directly, following
`integrations/chatgpt/AUTONOMOUS_PRODUCTION.md`. If a user asks you to produce
a book end to end, tell them ChatGPT Work is the normal way to do that now,
point them at that file, and offer to help only with the parts below -
maintaining Book Factory itself, or a specific writing/production task they
explicitly hand you. Do not tell them to bounce work between you and ChatGPT.

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

Follow `AGENTS.md` exactly. In particular: one task at a time, never approve or
lock on the operator's behalf (the only exception is `--autonomous` under a
recorded production policy, `AGENTS.md` section 3), never touch approved
artefacts, never skip a gate.

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

Every book has a recorded picture budget (`AGENTS.md` section 5a); read it
with `bookfactory pictures show <book>` before planning or generating
anything, and never raise it yourself.

When the next task is an illustration and the Higgsfield connector is
available, generate it yourself:

1. `bookfactory task <book> --json` gives the illustration task: its
   references, its `constraints` (`min_pixels` etc.) and its
   `output.destination` / `output.submit_command`. Read
   `style/visual-bible.md` first.
2. Upload each reference file to Higgsfield: `media_upload` (returns
   presigned upload URLs), then `curl -X PUT -H "Content-Type: image/png"
   --data-binary @<file> '<upload_url>'` from the session, then
   `media_confirm`.
3. `generate_image` with those media ids as `image_references`. On the basic
   plan, Nano Banana Pro works at `2k` (2 credits); `4k` needs the Plus plan.
   Pick an aspect ratio whose width at 2K meets the task's `min_pixels` (a
   3:4 portrait at 2K came out 1792x2400, enough for a 6x9 full page). Check
   cost first with `get_cost: true` if unsure. Never use a free-trial
   "unlimited" allowance unless the operator says so.
4. The prompt must describe the scene AND spell out: the visual bible's
   style words, each character's fixed features from the references, the
   visual bible's "Never" items (e.g. no brand logos), the reference's
   sparseness/background, plain paper, and "no text, letters, numbers, logos
   or signatures". A prompt that names only the scene has produced a brand
   logo on clothing and a cluttered background; naming the "Never" items and
   the sparseness fixed it (Phase 10, `docs/PLAN-ARCHIVE.md`).
5. Wait with `jobs_wait`, download the result URL with curl, submit with the
   task's `output.submit_command`. The measured checks (section 6a) run on
   submission.
6. Look at the picture yourself against the references before reporting. If
   it breaks the visual bible (a logo, a wrong face, embedded text), make a
   new draft rather than recommending it. Report the draft revision and
   path. Never approve it yourself - approval stays the operator's, unless
   `--autonomous` under a recorded policy that authorizes it (`AGENTS.md`
   section 3).
7. Each picture spends the operator's Higgsfield credits - check `balance`
   and say how many were used.

Rules 5 (image generation never sets type) and 6 (match the references
exactly, or stop and say so) apply exactly as written, unchanged.

If Higgsfield is not connected in this session, say so and hand the task
over instead:

> The next task is illustration `p058-mate-taxonomy`. Higgsfield is not
> connected in this session. Run `bookfactory task golf-addict --json`, give
> that to ChatGPT along with `integrations/chatgpt/BOOK_FACTORY.md`, and it
> will generate and submit the draft.

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
