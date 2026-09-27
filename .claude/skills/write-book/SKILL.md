---
name: write-book
description: Drive one book forward by alternating `bookfactory produce` with Claude writing the copy itself (brief, writing sample, voice bible, visual bible, manuscript, page plan, page specs, cover copy), drawing its page pictures and reference set through Higgsfield and `reference render`, and running its final release steps - each only as far as the recorded production policy allows. Asks once at the start how often to pause for review. Runs produce; when it stops with `writing`, writes that one task's copy to the voice rules, saves it where the task says, and runs produce again. When it stops with `picture`, generates or typesets that picture following the Images routine, and may approve it itself under `--autonomous` if the policy allows and the skill has checked it. Runs a lock, `cover finalize`, `cover preflight` or the release-ready step itself with `--autonomous` only when the task's mode is continue_automatically. Anything the operator alone may decide (the visual lock under visual_checkpoint, the cover's own approval, a revise, re-assembly after a revision) is asked for in plain words and run only once Kieran types the matching decision, signed `--by kieran`, on his own go-ahead. Never approves or forces the cover, never switches Claude Code's permission mode. No Claude API call.
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

Never ask the operator to switch Claude Code's permission mode. The go-ahead
slip (section 3g) is how his own typed decisions reach commands that need his
authority, in whatever mode the session is already in.

## 0. Ask once

Before anything else, ask the operator one question: "Shall I check each
draft with you (brief, writing sample, manuscript, each reference picture),
or run straight through to the look-check?" Remember the answer for this
session only - it never changes the book's recorded production policy
(`bookfactory policy show`), only how often *this skill* pauses to show you
work that the policy would otherwise let it carry straight past.

- **"Check each draft"**: after writing the brief, the writing sample or the
  manuscript, and before submitting each reference-set picture for approval,
  show the operator what you wrote or drew and wait for them to say
  "continue" (or to correct it) before going on.
- **"Run straight"**: carry on through everything the recorded policy allows
  without pausing for these drafts. Stop only where Book Factory itself
  stops: `wait_for_operator`, a refusal, the visual lock under
  `visual_checkpoint` (section 3g), and the cover's own approval (`cover
  approve`, always the operator's, section 3g).

Either way, this choice never widens what the policy authorizes - it only
changes when the skill shows you a draft along the way.

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
3. If `stopped_because` is **`picture`**: do section 3b (a page illustration)
   or section 3c (a character reference or `ref-page-editorial`), then go
   back to 1.
4. If `stopped_because` is **`not_mechanical`** and the `next_task` is one of
   the three typeset reference samples (`ref-layout-chapter-opener`,
   `ref-page-diagnostic`, `ref-palette`) or registers one of the six
   reference-set asset ids (a task id ending `-register`): do section 3c,
   then go back to 1.
5. If the `next_task` is a lock whose `mode` is **`continue_automatically`**:
   do section 3a, then go back to 1.
6. If the `next_task` is a reference-set picture's own approval and all six
   reference-set assets now have a reviewable draft the skill drew or
   rendered itself in this session: do section 3d (show and approve them
   together), then go back to 1.
7. If the `next_task` is that same page picture's own approval, its `mode`
   is **`continue_automatically`**, and the skill itself drew and checked
   that picture: do section 3d, then go back to 1.
8. If the `next_task`'s task id is `<book>-cover-direction`: do section 3e,
   then go back to 1.
9. If the `next_task`'s `submit_command` is `bookfactory cover finalize`,
   `bookfactory cover preflight` or `bookfactory advance ... --to
   release_ready`, and its `mode` is **`continue_automatically`**: do
   section 3f, then go back to 1.
10. Anything else that only the operator may decide (the visual lock under
    `visual_checkpoint`, the full-wrap cover's approval, a revise, a
    re-assembly or preflight after a revision, or any other operator
    decision): do section 3g, then go back to 1.
11. Anything else: stop the loop and go to section 5.

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
     confident mapping), any `too_long` page, or any page it flags for
     running into the bottom margin, then run
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
     (section 3a), and anything the operator alone decides is section 3g.
5. `bookfactory validate <book>`. If it reports a problem in what you wrote,
   fix it before going on. If "check each draft" was chosen in section 0,
   show the operator what you wrote and wait for "continue" before the next
   `produce` step.

If a refusal or error comes back that you cannot fix inside the task, stop
and report it. Never work around a gate.

## 3a. Run a lock the recorded policy authorizes

`AGENTS.md` quick reference: an agent may run a lock when it is the current
task from `bookfactory next` **and** that task's `mode` is
`continue_automatically`, using `--autonomous`. Book Factory then refuses it
unless the recorded production policy authorizes it, refuses the locks the
policy keeps as a checkpoint (the visual lock under `visual_checkpoint`), and
audits it as granted under the policy. A refused visual lock is the
operator's, via section 3g - never retry it with `--autonomous`.

1. `bookfactory task <book> --json`. Check its `task_id` matches the
   `next_task` produce stopped on, its `mode` is `continue_automatically`,
   and its `submit_command` is `bookfactory lock <what> <book>`.
2. Write the book id out in full - never a shell variable - and run exactly
   that command with `--autonomous --by claude` added. Never sign it with
   the operator's name.
3. If Book Factory refuses it, stop and report the refusal: that lock is the
   operator's (section 3g). Never retry without `--autonomous`, and never
   work round it.

## 3b. Draw a page picture

`produce` stops with `picture` for a page's own illustration whose task's
`mode` is `continue_automatically`; it never gives this code for cover
artwork, which always stays the operator's (section 3e/3g).

1. `bookfactory pictures show <book>`. If drawing this picture would break
   the recorded budget, stop and report - `produce` should not have offered
   it, so say so plainly.
2. Check the Higgsfield connector's `balance` first. If Higgsfield is not
   connected in this session, or credits are too low for the picture,
   stop and report exactly as `integrations/claude/BOOK_FACTORY.md`,
   "Images" says to when handing a task to ChatGPT instead - do not
   substitute a placeholder.
3. Follow the Images routine in `integrations/claude/BOOK_FACTORY.md` step
   by step: read the task and the visual bible, upload each reference from
   its approved drafts path, `generate_image` with the style words, each
   character's fixed features, the "Never" items, the reference's
   sparseness and "no text, letters, numbers, logos or signatures" spelled
   out in the prompt, `jobs_wait`, download the result.
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

## 3c. The reference set

The visual lock's reference set is six pictures. Three are drawn artwork
(the two character references, plus `ref-page-editorial`, an editorial
scene); three are typeset samples made from the book's own renderer, never
drawn:

| Asset id | What it is | How it is made |
|---|---|---|
| `ref-character-main` | Main character | Drawn (section 3b's routine) |
| `ref-character-support` | Supporting character or pet | Drawn (section 3b's routine) |
| `ref-page-editorial` | A normal page's editorial scene | Drawn (section 3b's routine) |
| `ref-layout-chapter-opener` | A chapter opener example | Typeset (below), illustrated with the approved `ref-page-editorial` |
| `ref-page-diagnostic` | A diagnostic/checklist activity page example | Typeset (below), from a page spec built from the manuscript |
| `ref-palette` | Palette and type sheet | Typeset (below), from the book's design tokens |

`produce` stops with `picture` for `ref-character-main`,
`ref-character-support` and `ref-page-editorial`: draw each one following
section 3b's routine, using any already-approved reference (a character
already approved) as an image reference for the next.

`produce` stops with `not_mechanical` for the three typeset samples and for
registering any of the six that is not yet in the asset registry (a task id
ending `-register`) - it has no code of its own for these, so read the
`next_task` yourself:

1. **A `-register` task**: run the exact `bookfactory asset add ...` command
   the task's `instructions` give. Then go back to the loop.
2. **`ref-layout-chapter-opener`**: write a chapter-opener page spec whose
   `illustration.asset_id` is `ref-page-editorial` (already approved), then
   run `bookfactory reference render <book> ref-layout-chapter-opener
   --from-file <spec.json> [--dpi 300] --json`.
3. **`ref-page-diagnostic`**: build the page plan from the locked manuscript
   (`bookfactory plan <book> --from-manuscript --out <scratch>/plan.json`),
   take its "No. 01" activity page spec, and run `bookfactory reference
   render <book> ref-page-diagnostic --from-file <spec.json> --json`.
4. **`ref-palette`**: run `bookfactory reference render <book> ref-palette
   --from-file <spec.json> --json` with `{"type": "palette_sheet", "title":
   "Palette and type sheet", "copy": {}}` as the spec - it draws the book's
   colours and type sizes from `style/design-tokens.json` itself, so there
   is no copy to write.

These are renders, not generations: no Higgsfield credits, no image model
(`docs/RENDERING.md`).

Draw or typeset all six before asking for any approval - keep looping
through section 2 without approving individually. Once every one has a
reviewable draft, show all six to the operator together, then go to
section 3d.

## 3d. Approve a picture the skill itself checked

`produce` never approves a picture (it stops instead, saying approving a
picture stays with the operator). But when the very next task is the
approval of a picture the skill drew or typeset itself (section 3b or 3c) in
this session, and that task's `mode` is `continue_automatically`, the skill
may approve it itself - never for `cover-front-artwork` or any other cover
task, which stay the operator's under every policy (section 3g).

1. `bookfactory task <book> --json`. Check its `task_id` is that picture's
   own approval task, its `mode` is `continue_automatically`, and its
   `asset_id` is one just drawn or typeset - not a cover asset.
2. Run `bookfactory approve <book-id-written-in-full> <asset-id> --kind
   asset --draft <vN> --autonomous --by claude`, using the draft revision
   just submitted. Never sign it with the operator's name.
3. If Book Factory refuses it (for example the visual lock's checkpoint
   keeps a `checkpointed` book's reference approvals with the operator too),
   stop, show the operator all six drafts together, and ask them to approve
   or reject each one - or wait for their typed go-ahead (section 3g) if
   the recorded policy allows it that way.
4. Go back to the loop (step 1 of section 2).

## 3e. Write the cover

When the next task is the cover direction task (`<book>-cover-direction`),
write the cover's own copy - this is no longer forbidden, only the artwork
and its approval are:

1. Read `cover/cover.json`, the locked manuscript and, if it exists,
   `brief/intake.json`'s `cover_style` answer (fixed at intake).
2. Write `cover/cover.json`'s `direction`, `author`, `subtitle` and back
   copy in the book's own voice, following `style/voice-bible.md` exactly
   as any other copy would. A big-lettering book (`brief/intake.json`'s
   `cover_style`) already has a starting `design` block Book Factory wrote
   for it - adjust it, changing only the words and colours the direction
   calls for, rather than inventing a new one.
3. Run `bookfactory cover build <book> --json`. Look at both previews it
   writes (the full-wrap print-size preview and the thumbnail). Fix
   whatever `problems` names in `cover/cover.json` - never the PDF - and
   rebuild until both previews are right.
4. Run `bookfactory cover build <book> --submit` to register the versioned
   draft.
5. Go back to the loop (step 1 of section 2). Approving the cover artwork
   and the full-wrap cover itself stays the operator's decision (section
   3g); this step only ever writes the copy and typesets the draft.

## 3f. Run a release step the recorded policy authorizes

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
   exactly - that step is the operator's (section 3g). Never retry another
   way.
4. Go back to the loop (step 1 of section 2).

## 3g. Operator decisions taken from the operator's own message

Some steps stay the operator's whatever the recorded policy is: the visual
lock under `visual_checkpoint`, the full-wrap cover's own approval, a
`revise`, re-assembling and re-preflighting the interior after a revision
(the interior goes stale the moment a page is revised and re-approved -
`bookfactory status` and `bookfactory next` say so), and any preflight the
`next_task` did not itself ask for. Never switch Claude Code's permission
mode to get one of these through: Book Factory's own safety check reads the
operator's own next message from the conversation itself, never from
anything Claude writes, and, only when that message plainly is the decision
itself, lets the exact command it names through in whatever mode the session
is already in. A short statement, not a question, counts; one containing
"not", "don't", "no", "wait", "hold", "later", "after" or "until" does not.
This applies only to that one message from the operator, never to a helper
(subagent), and naming the cover always needs the word "cover" in it.

1. Report clearly what is ready and the exact plain-English decision the
   operator can type, e.g. "the reference set is ready - type 'lock the
   look' to lock it", "cover draft v1 is built - type 'approve cover v1'",
   or "p014 and p033 run into the bottom margin - type 'revise p014 p033'".
   Then wait; do not run the command yet.
2. When the operator's next message plainly makes that decision, run
   exactly the matching command - book and asset/page ids written out in
   full, never a shell variable or a loop over several - signed `--by
   kieran` where the command takes `--by`. Never add `--autonomous`,
   `--force` or `--all-passing`: those never come from a typed go-ahead.
3. After any revision, run `produce` (or `assemble` / `preflight` if the
   operator's own words asked for them directly) rather than assuming the
   interior is still current - a revised page marks it stale until it is
   reassembled. Before the release step, read the QA findings for
   `technical.bottom_margin` and fix any page it names.
4. If the guard still refuses the command (for example because this session
   started before the go-ahead hook existed, so it never loaded), say so
   plainly and give the fallback: the operator runs it themselves, or
   switches to the default permission mode for that one command.
5. Go back to the loop (step 1 of section 2).

## 4. Never

- Never run `approve`, `reject`, `revise`, `assemble`, `preflight`,
  `policy set`, `pictures set` or any `cover` command yourself, except
  exactly `bookfactory approve ... --kind asset` for a picture the skill
  itself drew or typeset and checked (section 3d), exactly `cover finalize`
  or `cover preflight` when section 3f's conditions hold, and exactly the
  one command a go-ahead slip authorises (section 3g). Never `--force`.
  Never run `lock` or `advance` except as section 3a, 3f or 3g says.
  `produce` makes the only page approvals; the skill makes the only picture
  approvals it is authorised for, both under the recorded policy or the
  operator's own typed word.
- Never generate, submit or approve cover artwork
  (`cover-front-artwork`), and never approve or finalize the full-wrap
  cover other than the `cover finalize` step in 3f - `cover approve` stays
  the operator's under every policy, run only via section 3g.
- Never write into `approved/` folders or an approved cover, and keep the
  shell's own working folder out of them too.
- Never generate or submit a picture other than through section 3b or 3c,
  and never approve one other than through section 3d.
- Never use a free-trial "unlimited" Higgsfield allowance unless the
  operator says so.
- Never change the picture budget or the production policy.
- Never write a book id, page id or asset id as a shell variable, and never
  loop a shell command over several ids - write each one out in full, one
  command at a time.
- Never ask the operator to switch Claude Code's permission mode.

## 5. Report

In repository terms (`AGENTS.md` section 10), short and plain:

- which check-in choice the operator made in section 0;
- each file you wrote or command you ran to save copy (e.g. "wrote
  `brief/brief.md`", "`spec` p012 from file", "wrote `cover/cover.json`'s
  direction and back copy");
- what `produce` did along the way (renders, pages it approved);
- each picture you drew or typeset (asset id, draft path, which attempt
  passed for a drawn one), how many Higgsfield credits were used, and which
  pictures were approved under the recorded policy (section 3d);
- each lock or release step you ran under section 3a or 3f, as recorded
  under the policy;
- each decision you carried out on the operator's own typed go-ahead
  (section 3g), and the exact command it ran;
- where it stopped, its `stopped_because` and `message`, and what the
  operator now needs to decide, in the plain words they can type back (e.g.
  "type 'lock the look' to lock the reference set", or "review the full-wrap
  cover and type 'approve cover v2' to approve it").

End with **"Your next step:"** and the one action for the operator.
