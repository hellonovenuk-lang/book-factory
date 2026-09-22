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
