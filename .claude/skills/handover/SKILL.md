---
name: handover
description: End-of-session handover for Book Factory maintenance work. Rewrites the "Start here" note in PLAN.md, ticks finished tasks, parks new ideas and terms, commits, pushes to main and checks it arrived.
disable-model-invocation: true
allowed-tools: Read Edit Write Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git fetch *) Bash(git add *) Bash(git commit *) Bash(git push *) Bash(git rev-parse *) Bash(git branch *)
---

# Handover

Leave the repository so that a fresh session, told only "continue", can pick
up exactly where this one stopped. The repository is the only memory a new
session has.

## 1. Check where things stand

- `git branch --show-current`. If it is not `main`, stop and tell the
  operator which branch you're on and what is not on `main` (`CLAUDE.md`,
  "Branch policy"). Ask before going on.
- `git fetch origin main`, then `git status` and `git log --oneline origin/main..HEAD`.
  If remote `main` has commits you don't have, say so and bring them in
  before committing (never overwrite newer remote work).
- Read `PLAN.md` in full.

## 2. Update PLAN.md

Only the main session edits `PLAN.md`.

- **Tick** each task and "Done when" item that is actually finished. Tick only
  what you have seen finished in this session: files on disk, commands run,
  output read. If you are not sure, leave it unticked and say why in
  "Unfinished, carried over".
- **Rewrite the "Start here" block** in full, three lines:
  - **Doing:** the open phase and, in a few words, the work.
  - **Finished:** what got done this session, in plain words.
  - **Next action:** the one concrete next step (one action, not a list).
- **Unfinished, carried over:** every task or check left open, one line each,
  so nothing is silently dropped. "none" if none.
- **Don't try again:** approaches that failed this session and why, one line
  each, so the next session doesn't repeat them. Keep earlier entries that
  still apply.
- If you ran checks, add rows to the **Verification log** (date, phase, what
  was checked, result).
- If the phase's "Done when" is fully ticked, mark the phase **(done)**. Set
  "Next action" to choosing the next phase: the next one in `PLAN.md`, or one
  from `IDEAS.md`.
- **Move finished phases out.** `PLAN.md` loads into every session and every
  helper, so keep it short. Move each phase marked **(done)**, with its
  Verification log rows, to the end of `docs/PLAN-ARCHIVE.md` (create it if
  missing, headed `# PLAN archive`). Leave one line in `PLAN.md` in its place:
  `Phase N: Name (done, see docs/PLAN-ARCHIVE.md)`.

## 3. Park ideas and terms

- Any new idea raised this session that isn't part of the open phase goes into
  `IDEAS.md` as one dated line.
- Any technical term the operator met this session that isn't in
  `GLOSSARY.md` gets a one-line plain-English entry.

## 4. Save and send to GitHub

- Stage files **by name** (`git add PLAN.md IDEAS.md ...`), never `git add -A`
  or `git add .`, so nothing unexpected is swept in. If `git status` shows
  changes you did not make or don't recognise, leave them out and mention
  them.
- Commit with a message saying what the session did, e.g. `Handover: Phase 1
  foundations built, awaiting fresh-session test`.
- `git push origin main`.
- Check it arrived: `git fetch origin main` and confirm
  `git rev-parse HEAD` equals `git rev-parse origin/main`. If not, say exactly
  what is only local.

## 5. Report to the operator

Short and in plain English (see "Working with Kieran" in `CLAUDE.md`):

- what was finished,
- what is carried over, if anything,
- that it is saved on GitHub `main` (with the commit's short id),
- **"Your next step:"** usually: open a fresh session and say "continue".
