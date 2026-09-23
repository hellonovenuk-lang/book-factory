# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** no phase open. Phase 14 is done and archived.
> **Finished:** Phase 14, `produce` slice 3: `produce` stops with `writing` when the next job is copy, and `/write-book <book>` has Claude write it (no API call) and run `produce` again, stopping at locks, pictures, the cover and anything else needing Kieran. 488 tests passing, 2 skipped.
> **Next action:** plan Phase 15 with `/plan-phase`: `produce` slice 4, pictures through Higgsfield inside the loop (see `IDEAS.md`).

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
