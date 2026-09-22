# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Claude Code setup, Phase 3 (Safety checks and proof): all 6 tasks built, checked and on GitHub `main`; one live trial left.
> **Finished:** `/verify-phase`, the approval guard, quick-check and session-start hooks, the settings file, guide and glossary. The checker passed everything (370 tests passing).
> **Next action:** in this fresh session, do the live trial: try `bookfactory approve no-such-book p001 --by pretend-test` and confirm the guard stops it and asks Kieran. If it does, tick the last "Done when" item, mark Phase 3 (done) and run `/handover`.

**Unfinished, carried over:**
- Phase 3 "Done when": the live pretend-approve trial (see Next action).

**Don't try again:**
- `git rev-parse --short HEAD origin/main` fails ("Needed a single revision"): run `git rev-parse --short` once per ref.
- Testing a new hook in the same session that created `.claude/settings.json`: hooks load only when a session starts, so the trial does nothing. Permission deny rules do work straight away.
- Running `scripts/build_demo_book.py` in the real checkout: it rewrites about 200 tracked demo files. Use the throwaway copy in `/verify-phase`.

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

## Phase 3: Safety checks and proof (open: built and checked, one live trial left)

Planned with `/plan-phase` on 2026-09-22; operator agreed every line.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 3.1 | `/verify-phase`: proves every "Done when" item with fresh command output. Runs `scripts/build_demo_book.py` on a throwaway copy of the repository, because it rewrites about 200 tracked demo files | main | `.claude/skills/verify-phase/SKILL.md` | [x] |
| 3.2 | Approval guard hook: before any Bash command, asks the operator if it runs `bookfactory approve / lock / policy set / reject / revise / cover approve / cover finalize / advance --force` (including disguised forms such as `python -m bookfactory ...` or chained commands); blocks Bash writes into `approved/` folders and the approved cover | helper: builder, **tricky (Opus)**: must catch disguised commands; a gap is a real risk | `.claude/hooks/guard-authority.py`, `tests/test_hook_guard_authority.py` | [x] |
| 3.3 | Quick-check hook: after a `.py` or `.json` file is saved, checks it still parses | helper: builder, routine (Sonnet) | `.claude/hooks/quick-check.py`, `tests/test_hook_quick_check.py` | [x] |
| 3.4 | Session-start hook: in web sessions installs what the tests need (`pip install -e ".[dev]"`); always warns if not on `main`; shows "Start here" | helper: builder, routine (Sonnet) | `.claude/hooks/session-start.sh` | [x] |
| 3.5 | Settings: switches on the three hooks; forbids editing approved pages, assets and the approved cover; pre-approves safe read-only commands. The only task that edits the settings file, done after 3.2-3.4 | main | `.claude/settings.json` | [x] |
| 3.6 | Add the safety checks to the guide and glossary | main | `integrations/claude/WORKFLOW.md`, `GLOSSARY.md` | [x] |

**Order:** round 1: helpers on 3.2, 3.3, 3.4 while the main session writes
3.1. Round 2: main session does 3.5 and 3.6, then the checker checks
everything.

**Note:** "Nothing is installed from outside the repository" (rules above)
means Claude plugins and add-ons. The Python packages Book Factory's own
tests need (listed in `pyproject.toml`) are fine to install.

**Test-drive:** built with `/fan-out`, checked with `/verify-phase`, closed
with `/handover`.

**Done when:**
- [x] The checker shows all tests passing.
- [ ] A pretend "approve" is stopped and handed to the operator. (The guard does this when tested directly; the live trial needs a fresh session, because hooks load at session start.)
- [x] A pretend write into an approved folder is blocked.
- [x] `/verify-phase` proves those three with fresh results.

## After Phase 3

Run the whole routine on one small, real Book Factory job from
`docs/REVIEW-2026-09.md`.

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
| 2026-09-22 | 3 | Baseline before Phase 3 | 225 passed, 2 skipped |
| 2026-09-22 | 3 | Main session's own 13 test commands against the guard | all correct (ask / deny / allow) |
| 2026-09-22 | 3 | Live: Write into an approved folder | refused by the settings file's deny rule |
| 2026-09-22 | 3 | Live: pretend approve in the session that created the hooks | not stopped (hooks load at session start); book didn't exist, nothing changed |
| 2026-09-22 | 3 | Checker, following `/verify-phase` | passed: 370 passed, 2 skipped; guard asks on approve, denies approved write; demo build OK on a throwaway copy; only the 9 planned files changed |
