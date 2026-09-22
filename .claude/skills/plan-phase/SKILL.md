---
name: plan-phase
description: Turn an idea into one small, finishable phase of work on Book Factory itself, written into PLAN.md with a task table, the files each task touches, and a plain-words "Done when". Use when the operator wants to plan the next phase or turn an idea from IDEAS.md into work.
disable-model-invocation: true
argument-hint: "[the idea, or a phase name from PLAN.md]"
allowed-tools: Read Grep Glob Edit Bash(git status *) Bash(git fetch *) Bash(git log *) Bash(git branch *)
---

# Plan a phase

Turn one idea into one phase that fits a single sitting. The plan is written
into `PLAN.md`, and nothing is handed out until the operator has agreed to it.

Idea to plan: $ARGUMENTS
(If that is empty, use the next "not started" phase in `PLAN.md`. If there
isn't one, offer the top ideas in `IDEAS.md` and ask which one.)

## 1. Check the ground

- `git branch --show-current` must be `main`. If it isn't, stop and raise it
  (`CLAUDE.md`, "Branch policy").
- `git fetch origin main`. If remote `main` is ahead, say so before planning.
- Read `PLAN.md`. If a phase is still open (its "Done when" isn't fully
  ticked), stop. Say which items are left and offer to finish those first.
  Only one phase is open at a time.

## 2. Understand the idea

- Read the files the idea touches. Don't plan from memory.
- If something only the operator can decide is unclear, ask **one** question,
  wait for the answer, then carry on. Don't ask about what the code already
  tells you.

## 3. Cut it to size

- A phase is **at most 7 tasks** and fits one sitting. If it's bigger, split
  it into this phase and a later one (put the later one in `IDEAS.md`).
- Each task is one clear change, with one line of plain words saying what it
  does and why.
- Say for each task who does it:
  - **main**: small jobs (a few lines, one file, or anything touching
    `PLAN.md`) are quicker done by the main session than briefed out.
  - **helper**: a separate job worth handing out, say which kind (builder,
    checker or docs keeper) and whether it's **routine** (Sonnet) or
    **tricky** (Opus, only with a reason).

## 4. Map the files before anything is handed out

This is the step that stops two helpers editing the same file.

- List the exact files each task creates or changes, in the task table.
- Check that **no file appears in two tasks**. If it does, merge the tasks,
  give the file to one task, or put one of them in a later phase.
- Files with fixed owners:
  - `PLAN.md`: main session only.
  - `AGENTS.md`, `docs/OPERATOR.md`, `integrations/*`: the docs keeper only.
  - `bookfactory/cli/main.py`: one task at a time.
- Anything under a book's `approved/` folders, or an approved cover, is never
  in a plan (`AGENTS.md` section 4).

## 5. Write "Done when" and the test-drive

- **Done when:** 1 to 4 checkboxes in plain words that the operator can check
  for themselves, with no jargon. Each one is proved by something you can run
  or look at.
- **Test-drive:** how the phase's new features get used straight away.
- For code changes, "Done when" always includes `pytest` passing, and
  `python scripts/build_demo_book.py` passing if the pipeline is touched.

## 6. Show it, then write it

- Show the operator the phase in short plain words: the goal, the task list
  (who does each task, and which files), the "Done when", and a rough size
  (for example "about 5 tasks, 2 helpers, one sitting").
- Explain every technical term the first time (`CLAUDE.md`, "Working with
  Kieran"). Add new terms to `GLOSSARY.md`.
- When the operator agrees, write the phase into `PLAN.md` in the same shape
  as the existing phases (`## Phase N: Name (not started)`, task table with a
  **Files** column and a **Who** column, **Test-drive**, **Done when**), and
  update the "Start here" note.
- Don't commit here. `/handover` saves it, or the operator asks you to.

End with **"Your next step:"**, usually: "say OK to the plan, or tell me what
to change", or once agreed, "run `/fan-out`".
