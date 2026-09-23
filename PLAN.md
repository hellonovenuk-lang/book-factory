# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 4 (Render every page in one go) is done. The next phase isn't chosen yet.
> **Finished:** `bookfactory render <book> --submit` without `--page` now renders the whole book, skipping pages with no spec and approved pages, and carrying on past a page that fails. 383 tests passing, 2 skipped; demo build passes. Ran with Kieran's standing OK to work without asking (2026-09-23).
> **Next action:** choose the next phase from `docs/REVIEW-2026-09.md` (the rest of item #2, or #3 / #5 / #7), planned with `/plan-phase`. Kieran wants effort on what makes books faster, not more process.

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
