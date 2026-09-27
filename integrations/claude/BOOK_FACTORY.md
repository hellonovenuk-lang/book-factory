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

For a run of purely mechanical tasks - page renders, QA, assembly, interior
preflight - you may use `bookfactory produce <book>` (`AGENTS.md` section 2a)
instead of stepping through `next` by hand. It only ever runs a step whose
task `mode` is `continue_automatically`. That now includes approving a page
draft, but only when the recorded production policy authorizes autonomous
approval (`autonomous` or `visual_checkpoint`); it approves that one page the
same way `approve --autonomous --by produce` would, so the audit log shows it
was granted under the recorded policy. On a `checkpointed` book that same
task is `wait_for_operator`, so `produce` stops there instead. It stops, and
says why, at anything else: writing, a picture to draw, a picture (asset)
approval, a lock, an operator decision, remediation, or a blocked or
finished book. `produce` itself never draws, submits or approves a picture,
never touches the cover, and never locks or advances on its own. Report
where it stopped and why, the same as you would for any other task - and if
it approved pages along the way, say which ones.

When the next task is copy to write, `produce` stops with the code
`writing` instead of running it. The skill `/write-book <book>`
(`.claude/skills/write-book/SKILL.md`) repeats: run `produce`; when it stops
with `writing`, write that one task's copy yourself - brief, writing sample,
voice bible, manuscript, page plan, page specs or cover copy - on the
operator's subscription, with no Claude API call, following the "Writing
copy" rules below; save it where the task says; run `produce` again. When it
stops with `picture` (a page illustration, or a character reference or
editorial scene from the visual reference set, all in
`continue_automatically`; the cover never gives this code), and the
Higgsfield connector is available, it draws that one picture following the
"Images" routine below, checks it against the references itself, redrawing
up to 3 times if it breaks the visual bible, then submits it; only if that
picture's own approval task is next and its `mode` is
`continue_automatically` does it also approve, with `bookfactory approve
<book> <asset-id> --kind asset --draft <vN> --autonomous --by claude`,
audited as granted under the recorded policy. It reports the credits used.
The reference set's three typeset samples (`Typeset reference samples`,
below) are `produce`'s ordinary `not_mechanical` stop, not `picture` - the
skill still makes them itself, just by rendering rather than drawing. None
of this loop applies to the cover: cover artwork is drawn by the separate
"Cover artwork" routine below (Kieran allowed it 2026-09-27), and its
approval, with the full-wrap cover's, stays the operator's.
When the next task is a lock whose `mode` is `continue_automatically`, it
runs that lock itself with `--autonomous --by claude` (`AGENTS.md` quick
reference): Book Factory refuses it unless the recorded production policy
authorizes it, and refuses the locks the policy keeps as a checkpoint (the
visual lock under `visual_checkpoint`), so those stop for the operator. Once
the interior is otherwise finished, it likewise runs `bookfactory advance
<book> --to release_ready`, `bookfactory cover finalize` and `bookfactory
cover preflight` on their own, but only when the current task asks for
exactly that command and its `mode` is `continue_automatically` - otherwise
it stops and reports, same as any other command needing authority. Anything
left to the operator - the visual lock under `visual_checkpoint`, the
full-wrap cover's approval, a revise, or re-assembling and re-preflighting
after a revision - it asks for as a short statement and carries out only
once the operator's next message plainly is that decision (no question mark,
no "not"/"wait" and so on): the guard reads that message itself, from Claude
Code's own record of the conversation, and lets through exactly the command
it names, signed `--by kieran`, in whatever permission mode the session is
already in (never a mode switch), only until the operator's next message.
It stops and reports at any other stop code. It never
approves, rejects, revises, changes the picture budget, changes the
production policy, approves cover artwork or the full-wrap cover,
or uses `--force`, `--autonomous` or `--all-passing` on the operator's
behalf.

You have shell access, which means you *could* write straight into
`pages/approved/`, `chmod` a read-only file, or hand-edit `manifest.json`.
Do not. Every one of those bypasses a check that exists because of a real
failure. Use the CLI.

Write every book id, page id and asset id out in full in a command that
needs the operator's authority (`approve`, `lock`, `revise` and the rest).
The approval guard cannot read a shell variable or a loop, so it blocks
both, correctly - it is not something to work around. When only the
operator may make the decision at all, ask them for a short plain
statement, not a question, and wait: the guard reads the operator's own
next message straight from Claude Code's session record (never something an
agent writes) and, only when that message plainly is the decision itself
(short, no question mark, no "not"/"don't"/"wait" and so on), lets through
exactly the command it names, signed `--by kieran` - without anyone
switching the session's permission mode, and only for that one message; a
helper (subagent) never gets this. It is a guard against mistakes, not a
lock against a determined attacker. Never ask the operator to switch modes
instead.

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

Write the manuscript to the conventions `docs/OPERATOR.md` step 6 describes
(front matter, `## Stage N: Name` chapters starting with
`### Chapter opener`, `### No. NN · Kind: Title` activity sections, and so
on). Then build the page plan from it with the command instead of writing
every page spec by hand:

```bash
bookfactory plan <book> --from-manuscript --out <scratch>/plan.json
```

Read the fit report it writes alongside the plan - it says which pages it
split to fit, which activity pages are too long and need shortening, and
which sections it wasn't confident mapping (kept as a warning, never
dropped). Fix the manuscript or the plan file for anything flagged, then load
it with `bookfactory plan <book> --from-file <scratch>/plan.json`. This is
also what `/write-book` does at the page-plan step.

A diagnostic panel, gauge, checklist-with-ticks or cut-out card is a page
spec detail, not a picture: write it as an `activity` page's `blocks`
(`docs/RENDERING.md`), and it never touches the picture budget in
`AGENTS.md` section 5a.

The cover's own direction, author line, subtitle and back copy are copy too:
write them into `cover/cover.json` in the book's voice, the same as any
other task. You may also draw and submit the cover artwork
(`cover-front-artwork`) through Higgsfield, following "Cover artwork"
below. Only the approval stays outside what you decide (`AGENTS.md` section
9a): never approve `cover-front-artwork`, and never run `cover approve`
yourself.

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
2. Upload each reference file to Higgsfield from its approved drafts path
   (`assets/drafts/<asset-id>/...`, never the `approved/` copy itself):
   `media_upload` (returns presigned upload URLs), then `curl -X PUT -H
   "Content-Type: image/png" --data-binary @<file> '<upload_url>'` from the
   session, then `media_confirm`.
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

### Typeset reference samples

Three of the six reference-set pictures are typeset examples, not drawn
artwork, and don't need a real page to exist first: `ref-layout-chapter-opener`
(a chapter opener - illustrated with the already-approved `ref-page-editorial`
scene), `ref-page-diagnostic` (a diagnostic/checklist activity page, built
from the locked manuscript's "No. 01" page) and `ref-palette` (the palette
and type sheet, built straight from `style/design-tokens.json`, no copy to
write). `ref-page-editorial` itself - the normal page's editorial scene - is
drawn artwork, made the same way as a page illustration (`produce` gives it
the `picture` code, above), not a typeset sample.

Render a typeset sample from an ordinary page spec and submit it as a new
draft of the already-registered reference asset with:

```bash
bookfactory reference render <book> <asset-id> --from-file <spec.json> [--dpi 300] [--json]
```

This is a render, not a generation - no Higgsfield credits, no image model.
See `docs/RENDERING.md` for the full mechanics and `docs/OPERATOR.md` for
when to use it. `produce` has no distinct code for these three (they stop as
its ordinary `not_mechanical`); `/write-book` still makes them itself.

### Cover artwork

Kieran allowed Claude to draw cover artwork on 2026-09-27. Draw it with the
same Higgsfield routine as a page picture (steps 1-7 of "Images", above),
plus these cover rules:

1. Only when the book's cover is `native` (`cover/cover.json` `artwork`
   absent or `"native"`). A text-only cover is the operator's recorded
   choice (`AGENTS.md` section 9a); never switch it yourself.
2. Read `cover/cover.json`'s `direction` and the approved character
   references. Run `bookfactory cover dimensions <book>` for the front
   panel's printed size: the picture's width AND height must both reach
   300 DPI there (the task's `min_pixels` and `min_height_pixels`). Pick
   the aspect ratio and resolution to meet both; never upscale.
3. When the title is set over the picture (`design.title_over_artwork`),
   ask for a plain, empty band across the top for it. The picture itself
   carries no text, letters, numbers, logos or signatures (rule 5), and no
   title.
4. Submit it with the task's `output.submit_command`, then `bookfactory
   cover build <book>` and look at both previews against the direction.
   Redraw if it breaks the visual bible or the title does not read at
   thumbnail size.
5. Stop there. Show the operator the previews and the credits used.
   Approving the artwork and the full wrap (`cover approve`) stays the
   operator's under every policy, never `--autonomous` from Claude.

## Reporting back

Report in terms of the repository, not in terms of effort:

> Rendered p058 and submitted it as draft v1
> (`pages/drafts/p058/p058-v1.pdf`, sha256 4f2a...).
> `bookfactory next` now asks you to approve it. Nothing is approved until you
> run the command.

If you ran QA or preflight, give the status and the findings that need a human,
not a summary of the report.
