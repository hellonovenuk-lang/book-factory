# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 6 (Series presets) is done. The next phase isn't chosen yet.
> **Finished:** `bookfactory create "<title>" --policy <p> --series-from <book>` starts a book from a locked book's voice, visual rules, design tokens, reference set and cover design; references arrive as drafts with their source recorded; nothing approved or locked. 396 tests passing, 2 skipped.
> **Next action:** choose the next phase. Candidates from `docs/REVIEW-2026-09.md`: #7 one-prompt start, the rest of #2 (approve every draft that passes its checks in one command), #4 image API. `PLAN.md` is getting long: archive Phases 4-6 to `docs/PLAN-ARCHIVE.md` at the next `/handover`. Also in `IDEAS.md`: helper turn limits.

**Unfinished, carried over:**
- none

**Don't try again:**
- `git rev-parse --short HEAD origin/main` fails ("Needed a single revision"): run `git rev-parse --short` once per ref.
- Testing a new hook in the same session that created `.claude/settings.json`: hooks load only when a session starts, so the trial does nothing. Permission deny rules do work straight away. (Edits to an already-registered hook script do take effect at once.)
- Running `scripts/build_demo_book.py` in the real checkout: it rewrites about 200 tracked demo files. Use the throwaway copy in `/verify-phase`.
- Relying on a hook's "ask" in auto mode: auto mode settles it without showing Kieran. Use "deny" there.

---

## Goal of this block

Make Claude Code reliable for the operator's routine: **plan a phase, hand
work out to helpers, check it with proof, hand over to a fresh session**. Each
phase builds some features; the next phase uses them, so every feature is
test-driven straight after it is built.

Background research and the reasons for each choice: the audit of 2026-09-22
(summarised under "Decisions" below). Longer-term roadmap for Book Factory
itself: `docs/REVIEW-2026-09.md`.

## Rules for this block

- Work on `main` (operator confirmed 2026-09-22). Fetch remote `main` before
  changing files; push at the end of each phase and check it arrived.
- One phase open at a time. Each phase fits one sitting. The next starts only
  when this one's "Done when" is ticked.
- New ideas go in `IDEAS.md`, not into the open phase.
- Nothing is installed from outside the repository. Every file is written here.

---

Phase 1: Foundations (done, see `docs/PLAN-ARCHIVE.md`)

Phase 2: Planning and handing out work (done, see `docs/PLAN-ARCHIVE.md`)

Phase 3: Safety checks and proof (done, see `docs/PLAN-ARCHIVE.md`)

## Phase 4: Render every page in one go (done)

Planned 2026-09-23 with Kieran; the first real job for the routine, from
`docs/REVIEW-2026-09.md` item #2. `bookfactory render <book> --submit`
without `--page` already renders and submits every page, but it stops at the
first approved page, at the first page with no spec, and at the first page
that fails to render. This phase makes it safe to run on a real book.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 4.1 | Whole-book render: with `--submit`, skips approved pages (unless a revision is open); always skips pages with no spec; carries on past a page that fails; reports rendered / skipped / failed with reasons; the command exits non-zero if any page failed. Tests for each case | helper: builder, routine (Sonnet) | `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `tests/test_render.py` | [x] |
| 4.2 | Operator guide explains rendering the whole book and what is skipped | helper: docs keeper, routine (Sonnet) | `docs/OPERATOR.md` | [x] |
| 4.3 | Mark review item #2 as partly done | main | `docs/REVIEW-2026-09.md` | [x] |
| 4.4 | Check everything with proof (`/verify-phase`) | helper: checker | none (read-only) | [x] |

**Order:** round 1: 4.1 and 4.2 together while the main session does 4.3.
Then the checker checks everything.

**Test-drive:** on a throwaway copy of the demo book, approve one page, break
another, run `render --submit` on the whole book and read what it reports.

**Done when:**
- [x] One command renders and submits every page that is ready, and approved pages are never touched.
- [x] A broken page is listed as failed, and the other pages still get done.
- [x] `pytest` passes and the demo build passes.
- [x] Everything is saved to GitHub `main` and checked there.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 4 | Checker: only the 3 files of task 4.1 uncommitted | confirmed |
| 2026-09-23 | 4 | Checker: full `pytest` | 383 passed, 2 skipped (baseline 378 + 5 new) |
| 2026-09-23 | 4 | Checker: demo build on a throwaway copy | finished, Release Ready, 24 pages |
| 2026-09-23 | 4 | Test-drive: whole-book `render --submit` on the built demo book, one spec broken | all 24 pages skipped as approved, exit 0; approved PDFs' sha256 unchanged |
| 2026-09-23 | 4 | Broken page fails, rest carry on (demo book had no unapproved page, so by tests) | 5 new tests in `tests/test_render.py` pass |

---

## Phase 5: Cover build (done)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #5. Today
each cover is typeset by a one-off script (the running book has three:
`build_cover_v1.py`, `_text_v2.py`, `_v3.py`; the demo script has its own).
`bookfactory cover build <book>` does it from `cover/cover.json` in seconds,
the same way every time.

**The command:** `bookfactory cover build <book> [--submit]`. Reads title
(the book's), optional `subtitle`, `author`, `back_copy`, optional
`spine_text` (set only when KDP allows it, else left off and reported) and an
optional `design` block (`background`, `ink`, `accent` colours;
`title_font`, `body_font` font files inside the book). Places the approved
(or latest reviewable) `cover-front-artwork` on the front, or none for a
text-only cover. Keeps the barcode area clear. Writes
`output/cover-build/cover-wrap.pdf` plus a full-wrap preview PNG and a
front thumbnail PNG (regenerable, not tracked), runs the cover checks, and
with `--submit` registers a new cover draft only if they pass. It never
approves.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 5.1 | `cover build` with template, previews, checks, `--submit`, schema fields, the cover-layout task pointing to it, and tests | helper: builder, routine (Sonnet) | `bookfactory/render/cover.py` (new), `templates/cover/wrap.html.j2` (new), `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `bookfactory/core/tasks.py`, `schemas/cover.schema.json`, `tests/test_cover_build.py` (new) | [x] |
| 5.2 | Demo script uses `cover build` instead of its own typesetting | main, after 5.1 | `scripts/build_demo_book.py` | [x] |
| 5.3 | Rules and guides say covers are built with `cover build` | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/*` | [x] |
| 5.4 | Mark review item #5 done | main | `docs/REVIEW-2026-09.md` | [x] |
| 5.5 | Check everything with proof, and test-drive on a throwaway copy of the running book | helper: checker | none (read-only) | [x] |

**Notes:** the 5.1 builder hit its 40-turn limit, most likely waiting on the
slow full test run; its work was complete and its 8 tests passed. Main then
found that WeasyPrint ignores CSS `writing-mode`, so spine text came out
horizontal across both covers. Fixed by rotating it, sized from the spine
width, with a test that renders real spine text. Main also tightened the
AGENTS.md 9a wording so both previews must be looked at.

**Order:** round 1: 5.1 and 5.3 together; main does 5.4. Round 2: main
does 5.2, then the checker.

**Test-drive:** on a throwaway copy, build the running book's cover from its
`cover.json` and look at the preview and thumbnail.

**Done when:**
- [x] One command builds a full-wrap cover PDF and previews from `cover.json`, and it passes Book Factory's own cover checks.
- [x] With `--submit` it becomes a new cover draft; it never approves.
- [x] `pytest` passes and the demo build (now using `cover build`) passes.
- [x] Everything is saved to GitHub `main` and checked there.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 5 | Main: WeasyPrint spine test | `writing-mode` ignored (text horizontal, 1.7in wide); rotation keeps it vertical inside the spine |
| 2026-09-23 | 5 | Checker: only the phase's 12 files changed | confirmed |
| 2026-09-23 | 5 | Checker: full `pytest` | 392 passed, 2 skipped (383 + 9 new) |
| 2026-09-23 | 5 | Checker: demo build on a throwaway copy, now via `cover build --submit` | Release Ready; cover draft v1 built and submitted, cover preflight pass |
| 2026-09-23 | 5 | Test-drive: `cover build` on a throwaway copy of the running book | no problems; previews legible, artwork clear, nothing crosses the spine |

---

## Phase 6: Series presets (done)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #6. Book 2
of a series should start from book 1's locked look and voice instead of
redoing visual development, the slowest creative stage.

**The command:** `bookfactory create "<title>" --policy <policy> --series-from
<source-book>` (other `create` options as usual). The source must have its
voice and visual style locked. It copies into the new book: the voice bible
and writing sample, the visual bible, design tokens and reference set, and
the cover `design` block with any font files it names. Each required
reference's **approved** file from the source is registered and submitted in
the new book as a **draft** recording where it came from (source book,
revision, sha256). Nothing is approved or locked: the new book's own policy
and `next` decide who approves the references and locks voice and visual
(under `visual_checkpoint`, the operator's one visual lock). `series` is set
to the source's series name, or its title if it has none. An audit entry
lists every file copied and its sha256.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 6.1 | `create --series-from`: copy the locked style, submit the references as drafts with provenance, record series and audit; refuse if the source isn't locked; tests | helper: builder, routine (Sonnet) | `bookfactory/core/series.py` (new), `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `tests/test_series.py` (new) | [x] |
| 6.2 | Rules and guides explain starting a series book | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/BOOK_FACTORY.md` | [x] |
| 6.3 | Mark review item #6 done; glossary entry for "series preset" | main | `docs/REVIEW-2026-09.md`, `GLOSSARY.md` | [x] |
| 6.4 | Check everything with proof; test-drive by starting a series book from the demo book on a throwaway copy | helper: checker | none (read-only) | [x] |

**Notes:** the 6.1 builder hit its 40-turn limit with one wrong test (it
expected the new book's next task to be the visual lock; a new book
rightly starts at its own brief). Main rewrote that test to check what is
true, and made an explicit `create --series` name win over the source's.
The checker also needed a second turn budget to report.

**Order:** round 1: 6.1 and 6.2 together; main does 6.3. Then the checker.

**Test-drive:** on a throwaway copy, build the demo book, start "book 2" from
it, and read `status` and `next`: the style files match, the references wait
as drafts, and nothing is approved or locked.

**Done when:**
- [x] One command starts a new book with the earlier book's voice, visual rules, design settings and references already in place.
- [x] Nothing is approved or locked on anyone's behalf; the references arrive as drafts that say where they came from.
- [x] `pytest` passes and the demo build passes.
- [x] Everything is saved to GitHub `main` and checked there.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 6 | Checker: only the phase's files changed | confirmed |
| 2026-09-23 | 6 | Checker: full `pytest` | exit 0; 396 passed, 2 skipped (392 + 4 new; counted from the progress marks, the summary line wasn't written to the log) |
| 2026-09-23 | 6 | Checker: demo build on a throwaway copy | Release Ready, 24 pages |
| 2026-09-23 | 6 | Test-drive: `create --series-from demo-book` | exit 0; 5 style files byte-identical; 6 references as drafts, 0 approved, source `series:demo-book`; voice and visual unlocked; `next` = its own brief |
| 2026-09-23 | 6 | Test-drive: `--series-from` an unlocked book | refused (exit 5), no folder created |

---

## Decisions (from the 2026-09-22 audit)

- **Rules stay in `AGENTS.md`** (shared with ChatGPT). `CLAUDE.md` imports it
  and adds only Claude-specific material.
- **Parallel helpers are for improving Book Factory itself, never for
  producing a book.** A book's tasks stay one at a time (`AGENTS.md` §2).
- **Helpers never commit or push.** The main session commits each checked task
  naming its exact files (no `git add -A`), and pushes once per phase.
- **No file is edited by two helpers in the same phase.** `/plan-phase` assigns
  every file to one task; shared docs belong to the docs keeper; the CLI file
  `bookfactory/cli/main.py` is changed by one task at a time.
- **Not used, on purpose:** git worktrees and `isolation: worktree` (clash with
  working on `main`); agent teams (experimental, and they turn helpers into
  teammates); outside plugins such as Superpowers, everything-claude-code and
  pro-workflow (their mandatory branches, TDD and always-on hooks clash with
  `AGENTS.md`; their best ideas are written into our own commands instead).
- **Command names avoid Claude's built-ins** (`/verify`, `/batch`,
  `/code-review`, `/simplify`). Don't use `/batch` here: it works in worktrees.
- **Everything lives in the repository**, not in `~/.claude/`, because web
  sessions start in a fresh container each time.
- **Helpers cost usage.** Each one is a separate Claude worker that reads the
  rules before starting. Fan out only when it saves real time, keep it to 3 at
  once, and use the cheaper model for routine jobs (task 2.7, added
  2026-09-22 at the operator's request).

## Verification log

| Date | Phase | Check | Result |
|---|---|---|---|
