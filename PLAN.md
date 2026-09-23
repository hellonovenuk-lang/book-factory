# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 14, Claude writes the copy (`produce` slice 3). Planned and agreed 2026-09-23; no task started.
> **Finished:** Phase 13, `produce` slice 2: on an `autonomous` or `visual_checkpoint` book, `produce` approves each page it renders (signed `produce`, audited under the recorded policy) and carries on to QA, assembly and preflight; on a `checkpointed` book it stops at the first page approval. Never pictures, locks, the cover or force. 481 tests passing, 2 skipped.
> **Next action:** run `/fan-out` for Phase 14 (task 14.1 first; 14.2 and 14.3 build on its stop code).

**Unfinished, carried over:**
- none (the first live runs of `approve --all-passing` and of `produce` page approvals are Kieran's, on a real book; helpers are rightly blocked from them)

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

## Phase 14: Claude writes the copy (not started)

Chosen 2026-09-23 by Kieran: `produce` slice 3 from `IDEAS.md`. Kieran
decided there is no Claude API call: Claude Code writes the copy itself, on
his subscription, and `produce` does the rest.

**What changes:**
- `produce` stops with its own code, `writing`, when the next task is a
  writing (`authoring`) task whose `mode` is `continue_automatically`. It
  still writes nothing itself. Cover writing tasks (`cover-*`) and lock
  steps (`operator_decision`) are not `writing`: they keep their current
  stop codes.
- A new Claude Code skill, `/write-book <book>`, repeats: run
  `bookfactory produce <book> --json`; if it stopped with `writing`, read the
  full task (`bookfactory task <book> --json`), write that copy following
  `style/voice-bible.md` and `manuscript/writing-sample.md` (and the
  "Writing copy" rules in `integrations/claude/BOOK_FACTORY.md`), save it
  where the task's `output.destination` says (through `spec --from-file` or
  `plan --from-file` where the task names them), then run `produce` again.
  It stops, reporting where and why, at any other stop code.
- The skill never locks (the brief task's `submit_command` is the concept
  lock: the skill only writes the files, and the lock waits for Kieran),
  never approves pictures, never touches the cover, never raises the picture
  budget, never chooses or changes a policy, and never uses `--force`.
  Doing locks under an `autonomous` policy is a later idea, in `IDEAS.md`.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 14.1 | The `writing` stop code in `produce`, with tests: an `authoring` task in `continue_automatically` gives `writing`; cover writing tasks, lock steps and `wait_for_operator` writing tasks do not; the stop changes nothing on disk; dry run reports it too | helper: builder, routine (Sonnet) | `bookfactory/core/produce.py`, `tests/test_produce.py` | [x] |
| 14.2 | The `/write-book` skill: produce → write → save → produce, with the stop rules above; after 14.1 | main | `.claude/skills/write-book/SKILL.md` (new) | [ ] |
| 14.3 | Rules and guides: the `writing` stop code; how `/write-book` works and what it never does; after 14.1 | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/claude/BOOK_FACTORY.md` | [ ] |
| 14.4 | Tick slice 3 off in `IDEAS.md`; glossary terms; this plan | main | `IDEAS.md`, `GLOSSARY.md`, `PLAN.md` | [ ] |

**Test-drive:** make a throwaway `visual_checkpoint` book in a temporary
folder and run `/write-book` on it: it writes the brief, then stops at the
concept lock with a plain reason.

**Done when:**
- [ ] `produce` says "writing" when the next job is copy, and tests prove it still never writes, locks or approves anything by itself.
- [ ] `/write-book` on a throwaway book writes the brief and stops at the concept lock with a plain reason.
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
| 2026-09-23 | 14.1 | Checker: scope, `_stop_for` read, no new API call, full suite (junit XML), demo build + `produce` on a fresh `visual_checkpoint` book, both on a throwaway copy | Pass: 488 tests, 0 failed, 2 skipped; demo build Release Ready; fresh book stopped with `writing` at the brief, no steps taken |
