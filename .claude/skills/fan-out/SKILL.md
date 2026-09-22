---
name: fan-out
description: Hand the open phase's helper tasks to helpers (at most 3 at once), each with a standard brief and a file list that doesn't overlap, after showing the operator a one-line preview and getting their OK. Then check each result with the checker and commit each checked task by name. Use only for work on Book Factory itself, never for producing a book.
disable-model-invocation: true
argument-hint: "[task numbers, e.g. 2.3 2.4, or empty for all helper tasks]"
allowed-tools: Read Grep Glob Agent Bash(git status *) Bash(git diff *) Bash(git fetch *) Bash(git log *) Bash(git branch *)
---

# Fan out

Hand out the open phase's tasks to helpers, check what comes back, and commit
each checked task. Tasks to hand out: $ARGUMENTS (empty means every
unfinished task in the open phase marked **helper**).

**Never for producing a book.** A book's tasks stay one at a time
(`AGENTS.md` section 2). This command is only for changing Book Factory's own
code, templates, schemas and docs.

## 1. Check it's safe to hand out

- On `main`, remote `main` fetched, `git status` clean (or only changes you
  know about). If not, stop and say so.
- The phase in `PLAN.md` has a task table with a **Files** column. If it
  doesn't, stop and suggest `/plan-phase` first.
- **No file appears in two tasks being handed out now.** If one does, hand out
  only one of those tasks this round.
- Tasks marked **main**, and any small job (a few lines, one file), are done
  by you directly, not handed out. A helper costs a whole worker's worth of
  reading before it starts.

## 2. Usage rules

- **At most 3 helpers at once.** More tasks means more rounds.
- **Model:** helpers run on **Sonnet** by default. Use **Opus** only when the
  plan marks the task **tricky** and gives a reason.
- **Turn limit:** every helper has one (`maxTurns` in its file under
  `.claude/agents/`). If a helper hits it, treat the task as unfinished; don't
  simply start it again, find out why.
- Which helper:
  - `implementer` (builder): changes code, templates, schemas, tests.
  - `docs-sync` (docs keeper): the only helper that edits `AGENTS.md`,
    `docs/OPERATOR.md` or `integrations/*`.
  - `verifier` (checker): checks finished work; never edits.

## 3. Show a one-line preview and wait

Before starting anything, show the operator one line per round, e.g.:

> Round 1: 3 helpers (2 builders on Sonnet, 1 docs keeper on Sonnet), about
> 6 files, then 1 checker. Tasks 2.3, 2.4, 2.5. OK?

Then **stop and wait for the operator's OK.** No answer is not an OK.

## 4. Write each brief

Every helper gets a brief in exactly this shape. It starts cold: it knows only
what the brief and the repository tell it.

```
Task <number>: <one-line title>

Why: <one or two sentences on the purpose>

Read first:
- <files it must read before changing anything>

Files you may change (nothing else):
- <exact paths>

Parts:
1. <step>
2. <step>

Done when:
- <checkable result, e.g. "pytest tests/test_x.py passes">

Rules: do not commit, push, approve, lock or edit PLAN.md. If the job needs a
file not listed above, stop and say so instead of editing it.

Report back with:
- files changed
- commands run, with their results
- decisions you made on your own, and why
- anything left undone
```

## 5. Start the helpers

Start the round's helpers together (one message, several Agent calls), with
`subagent_type` set to the helper's name and the `model` chosen above. Don't
start the next round until this one has reported and been checked.

## 6. Check every result

For each report:

1. `git status` and `git diff --stat`: only the brief's files changed. Any
   other file changed is a finding; don't commit it, raise it.
2. Start the `verifier` with the task's "Done when" and the list of changed
   files. It runs the checks and reports in plain English.
3. If the checker finds a problem: fix a small one yourself, or send the task
   back to a builder with the finding. Never commit unchecked work.

## 7. Save each checked task

- Stage the task's files **by name** (`git add path/one path/two`), never
  `git add -A` or `git add .`.
- One commit per task, e.g. `Task 2.3: implementer helper`.
- Tick the task in `PLAN.md` and add a row to the Verification log.
- Don't push after each task; push once per phase (at `/handover`).

## 8. Report

Short and plain: which tasks are done and checked, which are not and why, what
the operator needs to decide. End with **"Your next step:"**.
