---
name: write-book
description: Drive one book forward by alternating `bookfactory produce` with Claude writing the copy itself (brief, writing sample, voice bible, visual bible, manuscript, page plan, page specs). Runs produce; when it stops with `writing`, writes that one task's copy to the voice rules, saves it where the task says, and runs produce again. Runs a lock itself with `--autonomous` only when the task's mode is continue_automatically (the recorded policy authorizes it). Stops and reports at anything else - pictures, the cover, operator decisions, any lock the policy keeps for the operator. Never approves or forces. No Claude API call.
disable-model-invocation: true
argument-hint: "<book-id>"
---

# Write a book

Book: $ARGUMENTS. If that is empty, run `bookfactory list` and ask which book.

This is **operating a book** (`integrations/claude/BOOK_FACTORY.md`, "Two
different jobs"), so every rule in `AGENTS.md` applies exactly. The copy is
written by you, in this session, on the operator's subscription: there is no
Claude API call.

## 1. Read the repository

```bash
bookfactory status <book> --json
bookfactory policy show <book> --json
bookfactory pictures show <book>
```

Note the production policy and picture budget. Never change either.

## 2. The loop

Repeat:

1. Run `bookfactory produce <book> --json`. It does the routine steps by
   itself (renders, page approvals under the recorded policy, QA, assembly,
   preflight) and stops with a `stopped_because` code.
2. If `stopped_because` is **`writing`**: do section 3, then go back to 1.
3. If the `next_task` is a lock whose `mode` is **`continue_automatically`**:
   do section 3a, then go back to 1.
4. Anything else: stop the loop and go to section 5.

## 3. Write one task's copy

1. `bookfactory task <book> --json`. Check its `task_id` matches the
   `next_task` produce stopped on. If not, stop and report.
2. Read every file in its `required_inputs`, plus `style/voice-bible.md` and
   `manuscript/writing-sample.md` when they exist and are filled in. Follow
   the "Writing copy" rules in `integrations/claude/BOOK_FACTORY.md` (voice
   bible binding, banned phrases, the constructions content QA flags). Write
   it properly the first time.
3. Write exactly what the task's `instructions` ask for, no more. Replace
   every TODO. The placeholder check is literal: the words "TODO" or "TBD"
   anywhere in the file block the gate, including the template's own
   guidance notes (the `>` lines), so remove those notes once the section is
   written. Do not work ahead into the next task.
4. Save it where `output.destination` says:
   - a Markdown file: write that file.
   - a page plan: run
     `bookfactory plan <book> --from-manuscript --out <scratch>/plan.json`
     to build it from the locked manuscript rather than writing every page
     by hand. Read the fit report it writes alongside the plan: fix the
     manuscript or the plan file for any warning (a section it wasn't
     confident mapping) or `too_long` page (needs splitting or
     shortening), then run
     `bookfactory plan <book> --from-file <scratch>/plan.json`. Stay within
     the picture budget; if the book needs more pictures, stop and ask.
     If the manuscript doesn't fit the command's conventions
     (`docs/OPERATOR.md` step 6) for a page, write that one page's entry by
     hand in the plan JSON instead.
   - a page spec: write the spec JSON in the scratchpad, then run
     `bookfactory spec <book> <page-id> --from-file <spec.json>`. Copy comes
     from the locked manuscript, never invented; never set
     `illustration.embedded_text`.
   - If the task's `submit_command` is a `lock`, `approve` or any other
     command needing authority (for example the brief's concept lock), do
     **not** run it here. Only write the files; a lock is its own next task
     (section 3a).
5. `bookfactory validate <book>`. If it reports a problem in what you wrote,
   fix it before going on.

If a refusal or error comes back that you cannot fix inside the task, stop
and report it. Never work around a gate.

## 3a. Run a lock the recorded policy authorizes

`AGENTS.md` quick reference: an agent may run a lock when it is the current
task from `bookfactory next` **and** that task's `mode` is
`continue_automatically`, using `--autonomous`. Book Factory then refuses it
unless the recorded production policy authorizes it, refuses the locks the
policy keeps as a checkpoint (the visual lock under `visual_checkpoint`), and
audits it as granted under the policy.

1. `bookfactory task <book> --json`. Check its `task_id` matches the
   `next_task` produce stopped on, its `mode` is `continue_automatically`,
   and its `submit_command` is `bookfactory lock <what> <book>`.
2. Run exactly that command with `--autonomous --by claude` added. Never
   sign it with the operator's name.
3. If Book Factory refuses it, stop and report the refusal: that lock is the
   operator's. Never retry without `--autonomous`, and never work round it.

## 4. Never

- Never run `approve`, `reject`, `revise`, `advance`, `assemble`,
  `preflight`, `policy set`, `pictures set` or any `cover` command yourself,
  and never `--force`. Never run `lock` except as section 3a says.
  `produce` makes the only approvals, under the recorded policy.
- Never write into `approved/` folders or an approved cover.
- Never generate or submit a picture here (that is its own routine,
  `integrations/claude/BOOK_FACTORY.md`, "Images").
- Never write cover copy (cover tasks do not stop with `writing`).

## 5. Report

In repository terms (`AGENTS.md` section 10), short and plain:

- each file you wrote or command you ran to save copy (e.g. "wrote
  `brief/brief.md`", "`spec` p012 from file");
- what `produce` did along the way (renders, pages it approved);
- each lock you ran under section 3a, as recorded under the policy;
- where it stopped, its `stopped_because` and `message`, and what the
  operator now needs to decide (e.g. "read the brief and lock the concept:
  `bookfactory lock concept <book>`").

End with **"Your next step:"** and the one action for the operator.
