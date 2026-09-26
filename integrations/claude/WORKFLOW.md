# The Claude Code routine for improving Book Factory

This is for work on **Book Factory itself** (its code, templates and rules).
Producing a book is a different job: ChatGPT Work drives it, one task at a
time (`integrations/chatgpt/AUTONOMOUS_PRODUCTION.md`).

## Cheat sheet

| When | Type | What happens |
|---|---|---|
| Starting a session | `continue` | Claude reads "Start here" in `PLAN.md` and proposes the next action |
| You have an idea to work on | `/plan-phase <idea>` | A small phase: tasks, files, "Done when". Nothing starts until you OK it |
| The plan is agreed | `/fan-out` | A one-line preview (helpers, model, size), then waits for your OK |
| Before closing a phase | `/verify-phase` | Proves every "Done when" item with fresh results |
| Ending a session | `/handover` | Updates `PLAN.md`, saves to GitHub `main`, checks it arrived |
| An idea comes up mid-phase | just say it | Claude parks it in `IDEAS.md` and steers back |

## The routine

1. **Plan** (`/plan-phase`). One idea becomes one phase: at most 7 tasks, one
   sitting, a plain-words "Done when". Every task lists the exact files it
   touches, and no file is in two tasks.
2. **Hand out** (`/fan-out`). Small jobs are done by the main session. Bigger
   ones go to helpers, all at once when their files do not overlap, after you've seen the preview and
   said OK.
3. **Check** (the checker helper, then `/verify-phase` for the whole phase). Every finished task is checked with fresh
   command output before it's saved. The checker can't edit anything, so it
   can't "fix" its way to a pass.
4. **Save.** The main session commits each checked task by name. Helpers never
   commit or push.
5. **Hand over** (`/handover`). `PLAN.md`'s "Start here" note is rewritten so a
   fresh session, told only "continue", knows exactly where we are. Finished
   phases move to `docs/PLAN-ARCHIVE.md` to keep `PLAN.md` short.

## The helpers

| Helper | File | Can edit | Model | Turn limit |
|---|---|---|---|---|
| Builder | `.claude/agents/implementer.md` | only the files in its brief | Sonnet | 40 |
| Checker | `.claude/agents/verifier.md` | nothing | Sonnet | 25 |
| Docs keeper | `.claude/agents/docs-sync.md` | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/*` (as briefed) | Sonnet | 30 |

None of them commits, pushes, approves, locks, or touches approved book files.

## Safety checks that run by themselves

Hooks (small scripts Claude Code runs automatically at set moments), switched
on in `.claude/settings.json`:

| Hook | When | What it does |
|---|---|---|
| `.claude/hooks/guard-authority.py` | before every shell command | Stops `approve`, `lock`, `policy set`, `reject`, `revise`, `cover approve/finalize`, `advance --force` and similar. In the default permission mode it asks the operator; in auto mode (where a question would be settled without reaching the operator) it blocks the command and Claude asks in the chat instead. It lets through `approve`, `lock` and `cover approve` run with `--autonomous` (not signed with the operator's name), because Book Factory itself refuses those unless the book's recorded production policy authorizes them Blocks any write into approved pages, assets or the approved cover |
| `.claude/hooks/quick-check.py` | after a file is saved | Checks a `.py` or `.json` file still reads correctly, so a slip is caught at once |
| `.claude/hooks/session-start.sh` | when a session starts | In web sessions installs what the tests need; if not on `main`, tells Claude to switch to `main` itself (no question to Kieran); shows "Start here" |

The settings file also forbids editing approved pages, assets and the approved
cover, and pre-approves safe read-only commands so helpers ask less.

## Keeping usage down

Each helper is a separate Claude worker that reads the rules (several thousand
tokens) before it starts. So:

- At most **3 helpers at once**.
- **Small jobs are done by the main session**, not handed out.
- Helpers use **Sonnet**. Opus only when the plan marks a task as tricky and
  says why.
- Every helper has a **turn limit**; one that hits it stops and reports.
- `/fan-out` shows its **preview and waits for your OK** before starting.
- **Finished phases leave `PLAN.md`**, because it loads into every session and
  every helper.

## Where things live

- `PLAN.md`: the open block of work and the "Start here" note. Main session
  only.
- `docs/PLAN-ARCHIVE.md`: finished phases and their verification logs.
- `IDEAS.md`: the parking lot for new ideas.
- `GLOSSARY.md`: plain-English meanings of the terms we use.
- `.claude/skills/`: the commands. `.claude/agents/`: the helpers.
