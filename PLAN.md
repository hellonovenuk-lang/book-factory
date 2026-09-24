# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** no phase open. Phase 17 is done (not yet archived; `/handover` moves it to `docs/PLAN-ARCHIVE.md`).
> **Finished:** Phase 17: `bookfactory plan <book> --from-manuscript --out <plan.json>` reads the locked manuscript, builds every page (openers, text pages, numbered activity pages from blocks), fit-tests each in both engines, splits overflowing openers and text pages, and writes a plan file only; `plan --from-file` loads it. `/write-book` uses it. Test-driven on a copy of the Golf book: 71 pages, same as the real plan, all fit. Full suite 579 passed, 2 skipped. Earlier today: the branch rule (sessions switch to `main` themselves, never ask).
> **Next action:** Kieran decides whether to fix the Golf book's two empty worksheet tables (below). Then plan Phase 18 with `/plan-phase` from `IDEAS.md`.

**Unfinished, carried over:**
- Golf Addict's Guide, found by Phase 17: approved pages p055 "My triggers" and p061 "Relapse diary" have fill-in tables with no rows to write in (the old one-off plan script dropped the blank rows). Fixing them needs Kieran's `revise` on each page, new renders, his approval and a new assembly. Kieran's call.
- none else (the first live runs of `approve --all-passing`, of `produce` page approvals and of `/write-book` are Kieran's, on a real book; helpers are rightly blocked from the first two)

**Don't try again:**
- `git rev-parse --short HEAD origin/main` fails ("Needed a single revision"): run `git rev-parse --short` once per ref.
- Testing a new hook in the same session that created `.claude/settings.json`: hooks load only when a session starts, so the trial does nothing. Permission deny rules do work straight away. (Edits to an already-registered hook script do take effect at once.)
- Running `scripts/build_demo_book.py` in the real checkout: it rewrites about 200 tracked demo files. Use the throwaway copy in `/verify-phase`.
- Relying on a hook's "ask" in auto mode: auto mode settles it without showing Kieran. Use "deny" there.
- Plain `pytest -q` took 10+ minutes and sometimes lost its summary line. `python3 -m pytest -q -p no:cacheprovider --junit-xml=<scratch>/junit.xml` ran the full suite in about 3 minutes (Phase 7); read the counts from the XML.
- Waiting for tests with `until ! kill -0 $(pgrep -f "pytest -q")`: the loop's own command contains "pytest -q", so it finds itself and never ends (one ran for 2 hours in Phase 4). Run the tests in the foreground, or wait on the exact process id.
- Test-driving `approve` through a helper: the guard blocks it, correctly. Don't work around it; prove it with tests in a temporary folder and leave the live run to Kieran.
- Editing plan files with a Python or shell script whose text mentions approve/assemble: the approval guard blocks it (known false alarm, in `IDEAS.md`). Use the Edit tool, or a script that doesn't name those words.
- Asking a checker to set up a live render on the demo copy with `revise`: the guard blocks it, correctly. Prove the render path with tests instead.
- Running `bookfactory lock --help` to check its arguments: the guard blocks any command naming lock/approve, even `--help`. Read the argparse definitions in `bookfactory/cli/main.py` instead.
- An `--autonomous` step written with a shell variable (`bookfactory approve $B ...`): the guard can't read `$B`, so it blocks. Write the book id out in full.
- Test-driving a book skill against the real checkout: it writes a new book into `books/`. Clone to the scratchpad and set `PYTHONPATH` and `BOOKFACTORY_ROOT` to the clone.

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

Phase 4: Render every page in one go (done, see `docs/PLAN-ARCHIVE.md`)

Phase 5: Cover build (done, see `docs/PLAN-ARCHIVE.md`)

Phase 6: Series presets (done, see `docs/PLAN-ARCHIVE.md`)

Phase 7: Batch approval (done, see `docs/PLAN-ARCHIVE.md`)

Phase 8: Page plan and specs in one file (done, see `docs/PLAN-ARCHIVE.md`)

Phase 9: One-prompt start (done, see `docs/PLAN-ARCHIVE.md`)

Phase 10: Test one picture through Higgsfield (done, see `docs/PLAN-ARCHIVE.md`)

Phase 11: Picture budget and the Higgsfield routine (done, see `docs/PLAN-ARCHIVE.md`)

Phase 12: `produce`, first slice (done, see `docs/PLAN-ARCHIVE.md`)

Phase 13: `produce` approves pages (done, see `docs/PLAN-ARCHIVE.md`)

Phase 14: Claude writes the copy (done, see `docs/PLAN-ARCHIVE.md`)

Phase 15: The guard follows the recorded policy (done 2026-09-24; Kieran asked for it after too many stops on the Golf Addict's Guide. Changed `.claude/hooks/guard-authority.py`, `tests/test_hook_guard_authority.py`, `.claude/skills/write-book/SKILL.md`, `integrations/claude/BOOK_FACTORY.md`, `integrations/claude/WORKFLOW.md`.)

Phase 16: Activity panels, typeset diagrams and sample pages (done, see `docs/PLAN-ARCHIVE.md`)

## Phase 17: Page plan straight from the manuscript (done)

Goal: one command reads a locked manuscript and writes the whole page plan
(openers, text pages, activity pages built from blocks), fit-tests every page
in both engines and splits text pages that overflow. The Golf plan needed a
one-off scratch script. The command writes a plan file only; loading it into a
book stays `plan --from-file`. Planned and agreed with Kieran 2026-09-24.

| # | Task | Who | Files |
|---|---|---|---|
| 17.1 ✓ | Parse the manuscript into plan pages: front matter, stage openers, text pages, `No. NN · Kind: Title` activities with their blocks (ticks, checklist, table, score, case note, cut-out, gauge) | builder, tricky (Opus: many block kinds must match the renderer's schema) | `bookfactory/core/manuscript_plan.py`, `tests/test_manuscript_plan.py` |
| 17.2 ✓ | Fit test: render each planned page in both engines; split an overflowing text page at a paragraph break; name an activity page that won't fit | builder, routine (Sonnet) | `bookfactory/render/fit.py`, `tests/test_plan_fit.py` |
| 17.3 ✓ | `bookfactory plan <book> --from-manuscript --out <plan.json>`: writes the plan file and a fit report, changes nothing in the book | main (small once 17.1 and 17.2 were in) | `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `tests/test_cli_plan_from_manuscript.py` |
| 17.4 ✓ | Document the manuscript layout the command reads; `/write-book` uses it for the page plan | docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/claude/BOOK_FACTORY.md`, `.claude/skills/write-book/SKILL.md`, `GLOSSARY.md` |
| 17.5 ✓ | Check: full suite, demo build in a throwaway copy | checker, routine (Sonnet) | none |
| 17.6 ✓ | Test-drive on a copy of the Golf book: compare with its real 71-page plan | main | `PLAN.md` |

**Test-drive:** 17.6 runs the command on a scratch clone of the Golf Addict's Guide and compares its output with the real plan, page for page.

**Done when:**
- [x] One command turns the Golf manuscript into a page plan that matches the real one page for page, with any differences listed and explained. (71 pages each; same types and order; split pages match word for word. Differences: the three split-off pages are titled "(continued)" not "(introduction)", and "About this programme" is back matter with no chapter, not chapter 8.)
- [x] Every page in that plan fits on its page in both engines, or the command names the ones that don't. (Golf: 68 fit, 3 openers split, none too long. The test-drive found that a one-paragraph opener could not be split; fixed so an opener can hand its only paragraph on, as Golf's Stage Seven and Eight did; test added.)
- [x] `pytest` passes, and `scripts/build_demo_book.py` passes in a throwaway copy.
- [x] Everything is pushed to `main` and checked there.

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
| 2026-09-24 | 15 | Full suite (junit) | 510 passed, 2 skipped, 0 failed |
| 2026-09-24 | 17 | Checker: scope, full suite (junit), demo build in throwaway copy, docs vs code, placeholder can't leak | 579 passed, 2 skipped, 0 failed; demo Release Ready; no mismatches |
| 2026-09-24 | 17 | Test-drive: `plan --from-manuscript` on a scratch copy of the Golf book, compared with its real plan | 71 = 71 pages, all fit (3 openers split), split bodies identical; opener one-paragraph fix and its test added after the checker ran, `tests/test_plan_fit.py` 8 passed |
