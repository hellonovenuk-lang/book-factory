---
name: write-book
description: Drive one book forward by alternating `bookfactory produce` with Claude writing the copy itself (brief, writing sample, voice bible, visual bible, manuscript, page plan, page specs), drawing its page pictures through Higgsfield, and running its final release steps - each only as far as the recorded production policy allows. Runs produce; when it stops with `writing`, writes that one task's copy to the voice rules, saves it where the task says, and runs produce again. When it stops with `picture`, generates and submits that page picture following the Images routine, and may approve it itself under `--autonomous` if the policy allows and the skill has checked it. Runs a lock, `cover finalize`, `cover preflight` or the release-ready step itself with `--autonomous` only when the task's mode is continue_automatically (the recorded policy authorizes it). Stops and reports at anything else - the cover's own artwork and approval, operator decisions, any lock or step the policy keeps for the operator. Never approves or forces the cover. No Claude API call.
disable-model-invocation: true
argument-hint: "<book-id>"
---

# Write a book

Book: $ARGUMENTS. If that is empty, run `bookfactory list` and ask which book.

This is **operating a book** (`integrations/claude/BOOK_FACTORY.md`, "Two
different jobs"), so every rule in `AGENTS.md` applies exactly. The copy is
written by you, in this session, on the operator's subscription: there is no
Claude API call. Pictures use the operator's Higgsfield credits (say how many
were spent, per `integrations/claude/BOOK_FACTORY.md` "Images").

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
3. If `stopped_because` is **`picture`**: do section 3b, then go back to 1.
4. If the `next_task` is a lock whose `mode` is **`continue_automatically`**:
   do section 3a, then go back to 1.
5. If the `next_task` is that same picture's own approval, its `mode` is
   **`continue_automatically`**, and the skill itself drew and checked that
   picture: do section 3c, then go back to 1.
6. If the `next_task`'s `submit_command` is `bookfactory cover finalize`,
   `bookfactory cover preflight` or `bookfactory advance ... --to
   release_ready`, and its `mode` is **`continue_automatically`**: do
   section 3d, then go back to 1.
7. Anything else: stop the loop and go to section 5.

## 3. Write one task's copy

1. `bookfactory task <book> --json`. Check its `task_id` matches the
   `next_task` produce stopped on. If not, stop and report.
2. Read every file in its `required_inputs`, plus `style/voice-bible.md` and
   `manuscript/writing-sample.md` when they exist and are filled in. Before
   writing the brief, the main character, or any visual copy (visual bible,
   visual references, cover direction, cover artwork), also read
   `brief/intake.json` if it exists. Treat its `title`,
   `main_character_details`, `print_colour` and `cover_style` answers as
   fixed - the task's own `instructions` repeat them as "fixed at intake -
   do not change without the operator" when they apply. Write to them
   exactly; never invent a different title, character detail, print colour
   or cover style, and never change one yourself even if it seems wrong -
   stop and ask the operator instead. Follow the "Writing copy" rules in
   `integrations/claude/BOOK_FACTORY.md` (voice bible binding, banned
   phrases, the constructions content QA flags). Write it properly the
   first time.
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

## 3b. Draw a picture

`produce` stops with `picture` only for a page picture (an illustration,
character reference or layout reference) whose task's `mode` is
`continue_automatically`; it never gives this code for cover artwork, which
always stays the operator's (section 4).

1. `bookfactory pictures show <book>`. If drawing this picture would break
   the recorded budget, stop and report - `produce` should not have offered
   it, so say so plainly.
2. Check the Higgsfield connector's `balance` first. If Higgsfield is not
   connected in this session, or credits are too low for the picture,
   stop and report exactly as `integrations/claude/BOOK_FACTORY.md`,
   "Images" says to when handing a task to ChatGPT instead - do not
   substitute a placeholder.
3. Follow the Images routine in `integrations/claude/BOOK_FACTORY.md` step
   by step: read the task and the visual bible, upload the references,
   `generate_image` with the style words, each character's fixed features,
   the "Never" items, the reference's sparseness and "no text, letters,
   numbers, logos or signatures" spelled out in the prompt, `jobs_wait`,
   download the result.
4. Look at the picture yourself against the references before doing
   anything else with it. If it breaks the visual bible - a wrong face, a
   logo, embedded text or pseudo-lettering, colour in a black-and-white
   book, a cluttered background - generate a new draft instead of
   submitting it. Try at most 3 times; if none pass, stop and report which
   drafts failed and why, rather than submitting a bad one.
5. Submit the one that matches with the task's `output.submit_command`.
   Note the draft path and how many Higgsfield credits it cost, for the
   final report.
6. Go back to the loop (step 1 of section 2).

## 3c. Approve a picture the skill itself checked

`produce` never approves a picture (it stops instead, saying approving a
picture stays with the operator). But when the very next task is the
approval of a page picture the skill drew and checked in section 3b two
steps ago, and that task's `mode` is `continue_automatically`, the skill may
approve it itself - never for `cover-front-artwork` or any other cover task,
which stay the operator's under every policy (section 4).

1. `bookfactory task <book> --json`. Check its `task_id` is that picture's
   own approval task, its `mode` is `continue_automatically`, and its
   `asset_id` is the one just drawn - not a cover asset.
2. Run `bookfactory approve <book-id-written-in-full> <asset-id> --kind
   asset --draft <vN> --autonomous --by claude`, using the draft revision
   just submitted. Never sign it with the operator's name.
3. If Book Factory refuses it, stop and report the refusal.
4. Go back to the loop (step 1 of section 2).

## 3d. Run a release step the recorded policy authorizes

Exactly like a lock (section 3a): an agent may run `cover finalize`, `cover
preflight` or `advance <book> --to release_ready` itself when it is the
current task from `bookfactory next`, that task's `mode` is
`continue_automatically`, and its `submit_command` is exactly one of those
commands. The full-wrap cover's own approval is never one of these - it stays
an explicit operator decision under every policy (`AGENTS.md` section 9a),
so this never covers `cover approve`.

1. `bookfactory task <book> --json`. Check its `task_id` matches the
   `next_task`, its `mode` is `continue_automatically`, and its
   `submit_command` is the release step in question.
2. Run exactly that command, with the book id written out in full and, for a
   lock or an approval-adjacent step, `--autonomous --by claude` added where
   the command supports it. Never invent flags such as `--force`.
3. If the guard or Book Factory refuses it, stop and report the refusal
   exactly - that step is the operator's. Never retry another way.
4. Go back to the loop (step 1 of section 2).

## 4. Never

- Never run `approve`, `reject`, `revise`, `assemble`, `preflight`,
  `policy set`, `pictures set` or any `cover` command yourself, except
  exactly `bookfactory approve ... --kind asset` for one page picture the
  skill itself drew and checked (section 3c), and exactly `cover finalize`
  or `cover preflight` when section 3d's conditions hold. Never `--force`.
  Never run `lock` or `advance` except as section 3a or 3d says. `produce`
  makes the only page approvals; the skill makes the only picture
  approvals, both under the recorded policy.
- Never generate, submit or approve cover artwork
  (`cover-front-artwork`), and never approve or finalize the full-wrap
  cover other than the `cover finalize` step in 3d - `cover approve` stays
  the operator's under every policy.
- Never write into `approved/` folders or an approved cover.
- Never generate or submit a picture other than through section 3b, and
  never approve one other than through section 3c.
- Never use a free-trial "unlimited" Higgsfield allowance unless the
  operator says so.
- Never change the picture budget or the production policy.
- Never write cover copy (cover tasks do not stop with `writing`).

## 5. Report

In repository terms (`AGENTS.md` section 10), short and plain:

- each file you wrote or command you ran to save copy (e.g. "wrote
  `brief/brief.md`", "`spec` p012 from file");
- what `produce` did along the way (renders, pages it approved);
- each picture you drew (asset id, draft path, which attempt passed), how
  many Higgsfield credits were used, and which pictures were approved under
  the recorded policy (section 3c);
- each lock or release step you ran under section 3a or 3d, as recorded
  under the policy;
- where it stopped, its `stopped_because` and `message`, and what the
  operator now needs to decide (e.g. "read the brief and lock the concept:
  `bookfactory lock concept <book>`", or "review and approve the full-wrap
  cover: `bookfactory cover approve <book> --draft v2`").

End with **"Your next step:"** and the one action for the operator.
