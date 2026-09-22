# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Claude Code setup, Phase 1 (Foundations).
> **Finished:** nothing yet in this phase.
> **Next action:** build Phase 1 tasks 1.1 to 1.6 below, then run `/handover`.

**Unfinished, carried over:** none.
**Don't try again:** none yet.

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

## Phase 1: Foundations (open)

Built directly by the main session, no helpers yet.

| # | Task | Files | Status |
|---|---|---|---|
| 1.1 | Load the rules for real: `@`-import `AGENTS.md` and `integrations/claude/BOOK_FACTORY.md` (and this file) from `CLAUDE.md`; update the "exists only to point" line | `CLAUDE.md` | [ ] |
| 1.2 | "Working with Kieran" section: plain English, terms explained, recommendation first, one question at a time, every reply ends with "Your next step" | `CLAUDE.md` | [ ] |
| 1.3 | Ideas parking lot | `IDEAS.md` | [ ] |
| 1.4 | Glossary, seeded with the terms used so far | `GLOSSARY.md` | [ ] |
| 1.5 | `/handover` command: updates "Start here", ticks tasks, saves, sends to GitHub, checks it arrived | `.claude/skills/handover/SKILL.md` | [ ] |
| 1.6 | Keep personal settings files out of GitHub | `.gitignore` | [ ] |

**Test-drive:** run `/handover`, open a fresh session, say only "continue".

**Done when:**
- [ ] The fresh session says where we are and what is next without being told.
- [ ] All Phase 1 files are on GitHub's `main`.

## Phase 2: Planning and handing out work (not started)

| # | Task | Files |
|---|---|---|
| 2.1 | `/plan-phase`: turns an idea into a small phase; maps which files each task touches *before* any work is handed out; plain-words "Done when" | `.claude/skills/plan-phase/` |
| 2.2 | `/fan-out` plus the standard brief (read first / files you may touch / parts / done when / decisions you made on your own); hands out only tasks whose files don't overlap | `.claude/skills/fan-out/` |
| 2.3 | Helper *builder*: edits only the files its brief names; never commits, pushes, approves or locks | `.claude/agents/implementer.md` |
| 2.4 | Helper *checker*: cannot edit; runs the checks and reports evidence | `.claude/agents/verifier.md` |
| 2.5 | Helper *docs keeper*: the only helper that edits `AGENTS.md`, `docs/OPERATOR.md`, `integrations/*` | `.claude/agents/docs-sync.md` |
| 2.6 | One-page guide, with the cheat sheet near the top of `CLAUDE.md` | `integrations/claude/WORKFLOW.md`, `CLAUDE.md` |
| 2.7 | Usage rules for helpers: at most 3 at once; small jobs done by the main session instead; helpers on Sonnet by default, Opus only when the brief says the job is tricky; a turn limit (`maxTurns`) on every helper; `/fan-out` shows a one-line preview (how many helpers, which model, rough size) and waits for the operator's OK; finished phases moved out of `PLAN.md` (it loads into every session and helper, about 7,000 tokens of rules already); checker reports in plain English | `.claude/skills/fan-out/`, `.claude/agents/*.md`, `.claude/skills/handover/SKILL.md`, `integrations/claude/WORKFLOW.md` |

**Test-drive:** use `/plan-phase` to plan Phase 3.

**Done when:** Phase 3's plan is written here and the operator understands
every line of it.

## Phase 3: Safety checks and proof (not started)

| # | Task | Files |
|---|---|---|
| 3.1 | `/verify-phase`: proves every "Done when" item with fresh command output; decides what to do about `build_demo_book.py` rewriting tracked demo files | `.claude/skills/verify-phase/` |
| 3.2 | Ask the operator before `bookfactory approve / lock / policy set / reject / revise / cover approve / advance --force`; block Bash writes into approved folders | `.claude/hooks/guard-authority.py` |
| 3.3 | Instant check that a saved `.py` or `.json` file isn't broken | `.claude/hooks/quick-check.py` |
| 3.4 | Session start: in web sessions install what the tests need; always warn if not on `main`; show "Start here" | `.claude/hooks/session-start.sh` |
| 3.5 | Permissions: never edit approved pages, assets or the approved cover; pre-approve safe read-only commands so helpers ask less | `.claude/settings.json` |

**Test-drive:** built with `/fan-out`, checked with `/verify-phase`, closed
with `/handover`.

**Done when:** the checker shows the tests passing, and a pretend "approve" is
stopped and handed to the operator.

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
