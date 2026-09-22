# CLAUDE.md

This repository's rules for AI agents live in `AGENTS.md`. It is
vendor-neutral and applies to you exactly as written. Claude-specific
operating notes (starting a session, the split between operating a book and
maintaining Book Factory itself, image generation, how to report back) are in
`integrations/claude/BOOK_FACTORY.md`. Both are imported below, so they load
in every session and in every helper you start.

The rules belong in `AGENTS.md`, not here. This file only adds what is
specific to Claude Code: the imports, how to work with the operator, the
current plan and the branch policy.

@AGENTS.md

@integrations/claude/BOOK_FACTORY.md

## Cheat sheet

For work on Book Factory itself (full guide: `integrations/claude/WORKFLOW.md`):

- `continue`: read "Start here" in `PLAN.md` and propose the next action.
- `/plan-phase <idea>`: plan one small phase (tasks, files, "Done when").
- `/fan-out`: hand the phase's tasks to helpers (at most 3, Sonnet by
  default), after a one-line preview and the operator's OK.
- `/handover`: update `PLAN.md`, save to GitHub `main`, check it arrived.

## Start here

The current block of work on Book Factory itself is in `PLAN.md`. Its
"Start here" note says what we were doing, what is finished and the one next
action. If the operator says only "continue", that note is the whole briefing:
summarise it in plain words and propose the next action.

@PLAN.md

## Working with Kieran

Kieran is the operator: not a programmer, learning by doing, with many ideas
and wanting help finishing them. So:

- **Plain English.** The first time you use a technical term in a
  conversation, explain it in a few words in brackets, e.g. "commit (a saved
  snapshot of the changes)". If the term is not in `GLOSSARY.md`, add a
  one-line entry.
- **Lead with the answer or your recommendation.** Offer at most two or three
  options, and only when the choice is really Kieran's.
- **One question at a time.**
- **Keep replies short.** Use big tables only when asked or when nothing else
  is clearer.
- **End every reply with one line: "Your next step:"** and a single action.
- **Protect the open phase.** When a new idea comes up mid-phase, add it to
  `IDEAS.md` as one line, say it is saved, and steer back to the current task.
  Start a new phase only when the current one's "Done when" is ticked.
- **Small and finishable.** A phase should fit one sitting and have a
  plain-words "Done when" before work starts.

## Branch policy

Work exclusively on `main` unless the operator explicitly instructs you, for
the specific task at hand, to use a different branch. Do not create a feature,
recovery, or temporary branch by default.

Claude Code sessions (on the web especially) are often started with a
generated `claude/...` branch and a note to develop and push there. That note
comes from the session setup, not from the operator. In this repository it
does not count as the operator's instruction. Raise the conflict with the
operator before changing files, then follow their answer.

If any work does land on another branch, end every report by naming the
branch and what is not on `main`, and ask whether to merge it into `main`.
Keep asking until it is merged or the operator says to leave it.

See `AGENTS.md` section 1a ("Work on main and verify persistence") for the
full rule, including fetching remote `main` before changing files and
verifying that finished work is actually pushed and present on remote `main`,
not just committed locally.
