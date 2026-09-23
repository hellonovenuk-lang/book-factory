# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 12 (`produce`, first slice), planned and agreed by Kieran 2026-09-23; no task started yet.
> **Finished:** Phases 8-11 (one-file page plan, one-prompt start, Higgsfield picture test, picture budget). 446 tests passing, 2 skipped at the end of Phase 11.
> **Next action:** run `/fan-out` for Phase 12: task 12.1 first (12.2 needs its function), then 12.2, then the docs keeper (12.3).

**Unfinished, carried over:**
- none (the first live run of `approve --all-passing` is Kieran's, on a real book; helpers are rightly blocked from it)

**Don't try again:**
- `git rev-parse --short HEAD origin/main` fails ("Needed a single revision"): run `git rev-parse --short` once per ref.
- Testing a new hook in the same session that created `.claude/settings.json`: hooks load only when a session starts, so the trial does nothing. Permission deny rules do work straight away. (Edits to an already-registered hook script do take effect at once.)
- Running `scripts/build_demo_book.py` in the real checkout: it rewrites about 200 tracked demo files. Use the throwaway copy in `/verify-phase`.
- Relying on a hook's "ask" in auto mode: auto mode settles it without showing Kieran. Use "deny" there.
- Plain `pytest -q` took 10+ minutes and sometimes lost its summary line. `python3 -m pytest -q -p no:cacheprovider --junit-xml=<scratch>/junit.xml` ran the full suite in about 3 minutes (Phase 7); read the counts from the XML.
- Waiting for tests with `until ! kill -0 $(pgrep -f "pytest -q")`: the loop's own command contains "pytest -q", so it finds itself and never ends (one ran for 2 hours in Phase 4). Run the tests in the foreground, or wait on the exact process id.
- Test-driving `approve` through a helper: the guard blocks it, correctly. Don't work around it; prove it with tests in a temporary folder and leave the live run to Kieran.

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

## Phase 12: `produce`, first slice (not started)

Chosen 2026-09-23 by Kieran: review item #8 (`docs/REVIEW-2026-09.md`),
hands-off production. #8 is bigger than one sitting; this is its first slice.
The later slices are parked in `IDEAS.md`.

**What changes:**
- `bookfactory produce <book>` repeats "read the next task, do it" for the
  purely mechanical tasks only: `page_render` (`render --page <id>
  --submit`), `qa`, `assembly` and `preflight`. It runs one only when that
  task's `mode` is `continue_automatically`, so it follows the book's
  recorded policy (`AGENTS.md` section 3a).
- It stops at the first task of any other kind (writing, a picture, an
  approval, a lock, an operator decision, remediation, blocked, complete)
  and says in plain words why it stopped and what the next task is.
- It never approves, locks, advances or forces anything. It has a step limit
  (`--max-steps`) and stops if a step leaves the same task as next (no
  progress). `--dry-run` shows the first step it would take and changes
  nothing. `--json` for agents.
- The logic lives in `bookfactory/core/produce.py`; the CLI is only an
  adapter (`integrations/claude/BOOK_FACTORY.md`).

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 12.1 | The loop in the core, `api.produce`, and tests: runs each mechanical task, stops at every other kind with a reason, never approves/locks/advances, obeys `mode`, step limit, no-progress stop, dry run changes nothing | helper: builder, tricky (Opus: it sits on the safety rules) | `bookfactory/core/produce.py` (new), `bookfactory/core/api.py`, `tests/test_produce.py` (new) | [x] |
| 12.2 | `bookfactory produce <book> [--max-steps N] [--dry-run] [--json]`, after 12.1 | helper: builder, routine (Sonnet) | `bookfactory/cli/main.py`, `tests/test_produce_cli.py` (new) | [ ] |
| 12.3 | Rules and guides: what `produce` does and never does; quick-reference line | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/claude/BOOK_FACTORY.md` | [ ] |
| 12.4 | Park the later slices; new glossary terms; this plan | main | `IDEAS.md`, `GLOSSARY.md`, `PLAN.md` | [x] |

**Test-drive:** run `produce` on a throwaway copy of the demo book
(`/verify-phase`) and see where it stops and what it says.

**Done when:**
- [ ] `bookfactory produce <book>` runs the mechanical steps by itself and stops with a plain reason at the first thing that needs writing, a picture or the operator.
- [ ] Tests prove it never approves, locks or skips a gate.
- [ ] All tests pass (`pytest`) and the demo build passes (`python scripts/build_demo_book.py`, on a throwaway copy).

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
| 2026-09-23 | 12.1 | Checker: scope, produce.py calls only render/qa/assemble/preflight/next, full suite, demo build + produce on a throwaway copy | Pass: 466 tests, 0 failed, 2 skipped; demo build passed; produce stopped at an illustration task with a plain reason |
