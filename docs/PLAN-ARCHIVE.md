# PLAN archive

Finished phases from `PLAN.md`, with their verification logs. Newest last.

---

## Phase 1: Foundations (done)

Built directly by the main session, no helpers yet.

| # | Task | Files | Status |
|---|---|---|---|
| 1.1 | Load the rules for real: `@`-import `AGENTS.md` and `integrations/claude/BOOK_FACTORY.md` (and this file) from `CLAUDE.md`; update the "exists only to point" line | `CLAUDE.md` | [x] |
| 1.2 | "Working with Kieran" section: plain English, terms explained, recommendation first, one question at a time, every reply ends with "Your next step" | `CLAUDE.md` | [x] |
| 1.3 | Ideas parking lot | `IDEAS.md` | [x] |
| 1.4 | Glossary, seeded with the terms used so far | `GLOSSARY.md` | [x] |
| 1.5 | `/handover` command: updates "Start here", ticks tasks, saves, sends to GitHub, checks it arrived | `.claude/skills/handover/SKILL.md` | [x] |
| 1.6 | Keep personal settings files out of GitHub | `.gitignore` | [x] |

**Test-drive:** run `/handover`, open a fresh session, say only "continue".

**Done when:**
- [x] The fresh session says where we are and what is next without being told.
- [x] All Phase 1 files are on GitHub's `main`.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-22 | 1 | `@` imports in `CLAUDE.md` point at existing files | all 3 found |
| 2026-09-22 | 1 | `/handover` settings header is valid | parsed OK |
| 2026-09-22 | 1 | Only the intended files changed; personal settings are git-ignored | confirmed with `git status`, `git check-ignore` |
| 2026-09-22 | 1 | Phase 1 commits are on GitHub `main` | local and remote both at `0ebf942` |
| 2026-09-22 | 1 | `/handover` runs as a command in the session that created it | worked |
| 2026-09-22 | 1 | Fresh session told only "continue" explains where we are | passed; operator confirmed the summary |

---

## Phase 2: Planning and handing out work (done)

| # | Task | Files | Status |
|---|---|---|---|
| 2.1 | `/plan-phase`: turns an idea into a small phase; maps which files each task touches *before* any work is handed out; plain-words "Done when" | `.claude/skills/plan-phase/` | [x] |
| 2.2 | `/fan-out` plus the standard brief (read first / files you may touch / parts / done when / decisions you made on your own); hands out only tasks whose files don't overlap | `.claude/skills/fan-out/` | [x] |
| 2.3 | Helper *builder*: edits only the files its brief names; never commits, pushes, approves or locks | `.claude/agents/implementer.md` | [x] |
| 2.4 | Helper *checker*: cannot edit; runs the checks and reports evidence | `.claude/agents/verifier.md` | [x] |
| 2.5 | Helper *docs keeper*: the only helper that edits `AGENTS.md`, `docs/OPERATOR.md`, `integrations/*` | `.claude/agents/docs-sync.md` | [x] |
| 2.6 | One-page guide, with the cheat sheet near the top of `CLAUDE.md` | `integrations/claude/WORKFLOW.md`, `CLAUDE.md` | [x] |
| 2.7 | Usage rules for helpers: at most 3 at once; small jobs done by the main session instead; helpers on Sonnet by default, Opus only when the brief says the job is tricky; a turn limit (`maxTurns`) on every helper; `/fan-out` shows a one-line preview (how many helpers, which model, rough size) and waits for the operator's OK; finished phases moved out of `PLAN.md` (it loads into every session and helper, about 7,000 tokens of rules already); checker reports in plain English | `.claude/skills/fan-out/`, `.claude/agents/*.md`, `.claude/skills/handover/SKILL.md`, `integrations/claude/WORKFLOW.md` | [x] |

**Test-drive:** use `/plan-phase` to plan Phase 3.

**Done when:**
- [x] Phase 3's plan is written here and the operator understands every line of it.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-22 | 2 | Header of every new command and helper file is valid | all 6 parsed OK |
| 2026-09-22 | 2 | Every file the new guides point to exists | none missing |
| 2026-09-22 | 2 | `/plan-phase` test-drive: Phase 3 planned with the operator | operator said OK to every line |

---

## Phase 3: Safety checks and proof (done)

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
- [x] A pretend "approve" is stopped and handed to the operator. (Live trial 2026-09-23: in auto mode the guard's "ask" was settled without reaching the operator, so the guard now blocks outside the default permission mode; the retried trial was blocked.)
- [x] A pretend write into an approved folder is blocked.
- [x] `/verify-phase` proves those three with fresh results.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-22 | 3 | Baseline before Phase 3 | 225 passed, 2 skipped |
| 2026-09-22 | 3 | Main session's own 13 test commands against the guard | all correct (ask / deny / allow) |
| 2026-09-22 | 3 | Live: Write into an approved folder | refused by the settings file's deny rule |
| 2026-09-22 | 3 | Live: pretend approve in the session that created the hooks | not stopped (hooks load at session start); book didn't exist, nothing changed |
| 2026-09-22 | 3 | Checker, following `/verify-phase` | passed: 370 passed, 2 skipped; guard asks on approve, denies approved write; demo build OK on a throwaway copy; only the 9 planned files changed |
| 2026-09-23 | 3 | Live: pretend approve in a fresh session (auto mode) | not stopped: guard said "ask" but auto mode let it run; book didn't exist, nothing changed |
| 2026-09-23 | 3 | Guard changed: asks become blocks outside the default permission mode | guard tests pass; full suite 378 passed, 2 skipped |
| 2026-09-23 | 3 | Live: same pretend approve, retried | blocked, with the reason telling Claude to ask Kieran in the chat |
