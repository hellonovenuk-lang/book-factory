---
name: verify-phase
description: Prove that the open phase in PLAN.md is finished, one "Done when" item at a time, using fresh command output rather than earlier claims. Runs the test suite, and the demo-book build on a throwaway copy so tracked demo files are never rewritten. Use before closing a phase with /handover.
disable-model-invocation: true
argument-hint: "[phase number, or empty for the open phase]"
allowed-tools: Read Grep Glob Agent Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git branch *) Bash(git rev-parse *) Bash(git clone *) Bash(python3 -m pytest *) Bash(python -m pytest *) Bash(pytest *) Bash(mktemp *)
---

# Verify a phase

Prove, with output produced **now**, that each "Done when" item of the phase
is true. Earlier messages, helper reports and ticked boxes are claims, not
proof. Phase to verify: $ARGUMENTS (empty means the open phase in `PLAN.md`).

## 1. Read the finish line

- Read the phase in `PLAN.md`: its task table (with **Files**) and its
  "Done when" list.
- `git status --short`. Note any change that isn't in the phase's file list.
  That goes in the report as a finding.

## 2. Standard checks (every phase that touched code, hooks or templates)

1. **Tests:** `python3 -m pytest -q` from the repository root. Record the
   summary line (e.g. "225 passed, 2 skipped"). If `pytest` or `bookfactory`
   isn't installed, say so; don't mark this item as passed.
2. **Demo build, on a throwaway copy.** `scripts/build_demo_book.py` rewrites
   about 200 tracked files under `books/demo-book/`, so never run it in the
   real checkout. Instead:
   ```bash
   tmp=$(mktemp -d)
   git clone -q . "$tmp/bf"
   # copy uncommitted changes in too, so what is checked is what will be committed
   git diff HEAD | git -C "$tmp/bf" apply --allow-empty
   git ls-files --others --exclude-standard -z | xargs -0 -I{} cp --parents {} "$tmp/bf"/
   (cd "$tmp/bf" && python3 scripts/build_demo_book.py)
   ```
   Record whether it finished and its last lines. Then `rm -rf "$tmp"`. Run
   this only when the phase touched `bookfactory/`, templates, schemas or
   `scripts/`. Otherwise say it was skipped and why.
3. **Real checkout untouched:** `git status --short` again. It must match
   step 1.

## 3. Prove each "Done when" item

For each item, in order:

- Decide the one command (or small set) whose output proves it. Prefer a
  command a fresh session could rerun.
- Run it and read the output. Don't guess from the code.
- For behaviour that needs a live session (for example "a pretend approve is
  stopped"), prove it with the smallest real trial: feed the hook the exact
  input Claude Code would send and show its decision, **and** say that the
  live-session trial is for the operator to watch.
- Never run a real authority command (`approve`, `lock`, `policy set`,
  `cover approve`...) against a real book to prove a guard works. Use the
  hook directly with pretend input.

You may hand the checks to the `verifier` helper (Sonnet) instead of running
them yourself. Give it the "Done when" list and the phase's file list. Its
report still has to contain the command output.

## 4. Report in plain English

Short table, one row per "Done when" item:

| Done when | Proved by | Result |
|---|---|---|
| All tests pass | `python3 -m pytest -q` | 262 passed, 2 skipped |

Then:

- **Verdict:** "Phase N verified" only if every row passed. Otherwise
  "Not yet" and what's missing.
- **Findings:** files changed outside the plan, skipped checks, anything
  surprising.
- Don't tick anything in `PLAN.md` here. Offer to tick the proven items and
  add rows to the Verification log (main session only), then `/handover`.

End with **"Your next step:"**.
