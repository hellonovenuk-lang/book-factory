# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 16 (activity panels, typeset diagrams, sample pages), in progress: round 1 is 16.1 and 16.2.
> **Finished:** Phase 15, the guard follows the recorded policy: `guard-authority.py` lets `approve`, `lock` and `cover approve` through when run with `--autonomous` (not signed "kieran"), since Book Factory refuses those unless the policy authorizes them; `/write-book` now runs a lock itself when its task's mode is `continue_automatically`. 510 tests passing, 2 skipped. Earlier: Phase 14, `/write-book`.
> **Next action:** plan Phase 16 with `/plan-phase`: bring the Runner's Guide v4 typeset elements (numbered activity panels with tick boxes, score boxes, write-in lines and fill-in tables; typeset diagrams such as gauges, cycles and trackers; dashed cut-out cards) into the standard renderer, so the Golf Addict's Guide gets them before its pages are made (Kieran, 2026-09-23). Reference: `books/runners-guide-to-normal-conversation/interior/build_interior.py` and its `README.md`. Also include a way to render the typeset sample pages the reference set needs before the page plan (`ref-layout-chapter-opener`, `ref-page-diagnostic`, `ref-page-editorial`, `ref-palette`): the Golf Addict's Guide is waiting on exactly these, with Dave and the family references already approved. `produce` slice 4 (pictures in the loop) moves to Phase 17.

**Unfinished, carried over:**
- none (the first live runs of `approve --all-passing`, of `produce` page approvals and of `/write-book` are Kieran's, on a real book; helpers are rightly blocked from the first two)

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

## Phase 16: Activity panels, typeset diagrams and sample pages (in progress)

Goal: pages can carry the Runner's Guide v4 panels and diagrams as real type,
built from blocks inside Book Factory's one-page-at-a-time renderer, and Book
Factory can render the typeset sample pages a book's reference set needs
before its page plan. Planned 2026-09-24, agreed by Kieran.

| # | Task | Who | Files |
|---|---|---|---|
| 16.1 | `activity` page type built from blocks (panel header, ticks, checklist, score, lines, table, casenote, gauge, cycle, cutout, signature), right in both backends | builder, tricky (Opus: WeasyPrint and Chromium disagree on layout) | `templates/pages/_blocks.html.j2`, `templates/pages/activity.html.j2`, `bookfactory/render/assets/book.css`, `bookfactory/qa/content.py`, `tests/test_activity_page.py` |
| 16.2 | `bookfactory reference render <book> <asset-id> --from-file <spec.json>`: renders a sample page spec to a 300-DPI PNG and submits it as that reference's draft; plus a `palette_sheet` page type | builder, routine (Sonnet) | `bookfactory/core/api.py`, `bookfactory/render/renderer.py`, `bookfactory/cli/main.py`, `templates/pages/palette_sheet.html.j2`, `tests/test_reference_render.py` |
| 16.3 | Document the activity page and `reference render` | docs keeper, routine | `AGENTS.md`, `docs/OPERATOR.md`, `docs/RENDERING.md`, `integrations/claude/BOOK_FACTORY.md`, `integrations/chatgpt/BOOK_FACTORY.md`, `GLOSSARY.md` |
| 16.4 | Check: full suite, demo build in a throwaway copy, both backends | checker, routine | none |
| 16.5 | Test-drive on the Golf Addict's Guide: render its four sample-page references, stop at Kieran's visual lock | main | the book's reference drafts, `PLAN.md` |

**Test-drive:** 16.5 renders the Golf Addict's Guide's `ref-layout-chapter-opener`, `ref-page-diagnostic` (an activity page), `ref-page-editorial` and `ref-palette` with the new command.

**Done when:**
- [ ] Kieran can look at a sample Golf page with a numbered panel, tick boxes, a score box, write-in lines, a fill-in table, a case note, the gauge and the cycle, all as real type.
- [ ] The Golf book's four sample pages exist and are ready for Kieran's visual lock.
- [ ] `pytest` passes, and `scripts/build_demo_book.py` passes in a throwaway copy.
- [ ] Everything is pushed to `main` and checked there.

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
