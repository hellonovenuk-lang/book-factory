# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 13 is done and checked, not yet archived.
> **Finished:** Phase 13, `produce` slice 2: on an `autonomous` or `visual_checkpoint` book, `produce` approves each page it renders (signed `produce`, audited under the recorded policy) and carries on to QA, assembly and preflight; on a `checkpointed` book it stops at the first page approval. Never pictures, locks, the cover or force. 481 tests passing, 2 skipped.
> **Next action:** run `/handover` to archive Phase 13; then pick the next `produce` slice from `IDEAS.md` (3: copy through the Claude API, 4: pictures through Higgsfield, 5: morning routine).

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

## Phase 13: `produce` approves pages (done)

Chosen 2026-09-23 by Kieran: `produce` slice 2 from `IDEAS.md`. Kieran
decided that page approvals run under **both** `autonomous` and
`visual_checkpoint` (the two policies `gates.autonomous_approval_authorized`
already accepts, and under which `next` already gives page approvals
`continue_automatically`).

**What changes:**
- `produce` takes one more kind of task: a **page** approval (`type:
  approval`, a `page_id`, task id `<page>-approve`), only when its `mode` is
  `continue_automatically` and `gates.autonomous_approval_authorized` passes.
  It approves exactly the reviewable draft the task is about, through
  `api.approve(..., kind="page", autonomous=True, by="produce")`, so every
  existing check applies and the audit log records it as granted under the
  recorded policy.
- It still stops at asset (picture) approvals, locks, the cover, remediation,
  writing and operator decisions. It never passes `force`, never calls
  `approve_passing`, `lock`, `advance`, `reject`, `revise` or a policy or
  picture-budget change. A `checkpointed` book stops at the first page approval.
- `--dry-run` reports the approval it would make and changes nothing.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 13.1 | Page approvals in the loop, as above, with tests: approves pages under `autonomous` and `visual_checkpoint`; stops on `checkpointed`; never approves assets, locks or the cover; never forces; dry run changes nothing; a whole planned book runs render → approve → … → QA → assembly | helper: builder, tricky (Opus: it hands the loop approval power) | `bookfactory/core/produce.py`, `tests/test_produce.py` | [x] |
| 13.2 | `produce` help text no longer says "never approves"; CLI test that the JSON shows an approval step | main | `bookfactory/cli/main.py`, `tests/test_produce_cli.py`, `bookfactory/core/api.py` (docstring, found by 13.1) | [x] |
| 13.3 | Rules and guides: what `produce` now approves (pages only, under the recorded policy) and what it still never does | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/claude/BOOK_FACTORY.md` | [x] |
| 13.4 | Tick slice 2 off in `IDEAS.md`; glossary terms (none new); this plan | main | `IDEAS.md`, `GLOSSARY.md`, `PLAN.md` | [x] |

**Test-drive:** tests on a `visual_checkpoint` book show `produce` running
render → approve → render → … → QA → assembly; on a `checkpointed` book it
stops at the first page's approval. Checker runs the full suite and the demo
build on a throwaway copy (`/verify-phase`).

**Done when:**
- [x] On a `visual_checkpoint` or `autonomous` book, `produce` approves each page it renders and keeps going; on a `checkpointed` book it stops and waits for Kieran.
- [x] Tests prove it never approves a picture, a lock or the cover, and never forces anything.
- [x] All tests pass (`pytest`) and the demo build passes (`python scripts/build_demo_book.py`, on a throwaway copy).

**Notes:** real task ids carry the book prefix (`<book>-<page>-approve`); the
builder matched that. `produce` approves a page only when its reviewable draft
is also its latest draft. Approvals are signed `produce` and audited as
`autonomous_production_policy:<mode>`. The first live run on a real book is
Kieran's.

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
| 2026-09-23 | 13 | Checker: full suite (junit XML), demo build on a throwaway copy, code read of `produce.py`, file list | 481 passed, 2 skipped; demo build Release Ready (24 pages, 17 assets); only the 8 briefed files changed; no leftover "never approves" wording |
