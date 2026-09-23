# Autonomous production - the normal way a book gets made now

Read `AGENTS.md` and `integrations/chatgpt/BOOK_FACTORY.md` first. This file is
the operating contract for running a whole book end to end in one continuous
session (or several, picked back up from repository state), without shuttling
tasks to a human or to another agent between every step.

Claude Code is not part of this loop. It builds and maintains Book Factory.
You are the normal production operator.

---

## The shape of a session

```
USER: "Create a Book Factory book about men who are addicted to golf."
  -> you create the project from the idea
  -> you draft your best-guess intake answers from the idea
  -> you show the user one summary: drafted answers, unclear questions,
     and the production policy question
  -> the user replies once, confirming or correcting it and choosing the policy
  -> you persist the confirmed answers
  -> you drive the book through every stage, continuously,
     stopping only when the repository or the policy genuinely requires it
  -> finished, QA'd, KDP-checked files
```

Tasks still exist underneath this (`bookfactory next` still returns exactly
one). That is an implementation detail for resumability, not something the
user should have to manage. Do not report back to the user after every single
task and wait to be told "continue" - that is the exact workflow this system
was built to replace.

## 1. Read the repository directly. Never trust conversation memory.

Every step below assumes you can run the CLI or read the files directly - the
"Route 1/2" of `integrations/chatgpt/BOOK_FACTORY.md`. If this is a brand new chat and the user says
"continue Book Factory project golf-addict", do not ask what has happened -
read it:

```bash
bookfactory status golf-addict --json
bookfactory next golf-addict --json
```

## 2. Starting from an idea

```bash
bookfactory create-from-idea "A fake rehabilitation manual for men addicted to golf." --json
```

This creates the project and marks the intake questionnaire required.
`bookfactory next` will now return a task of `"type": "intake"` before
anything else - including before the brief. Do not skip it and do not
improvise the answers yourself.

## 3. Intake - draft it from the idea, the operator confirms once

The recommended routine is draft-then-confirm, not a twelve-question form.
The user already gave you the idea; use it to answer what you reasonably can,
and only ask them to react to a summary.

1. **Draft your best-guess answers** for as many of the twelve questions as
   the idea supports (the full list is below, and `bookfactory questionnaire
   --json` returns it machine-readably). Every answer you do give must be
   valid - a choice question (`humour_level`, `visual_feel`,
   `colour_direction`, `main_character`, `length`) needs one of its listed
   choices, not free text. Anything you cannot reasonably infer, leave out of
   `answers` and list its key in `unclear` instead of guessing. Never include
   `production_policy` in the draft - that question is always the operator's,
   never the agent's, to answer.

   Example `answers.json`:

   ```json
   {
     "answers": {
       "idea": "A fake rehabilitation manual for men addicted to golf.",
       "buyer": "Partners and friends buying a joke gift.",
       "recipient": "A man who golfs most weekends and won't admit it's a problem.",
       "recognition_trigger": "The excuses for 'just nine holes' turning into a full day.",
       "humour_level": "medium",
       "visual_feel": "classic_editorial_caricature",
       "main_character": "book_factory_invents",
       "length": "80",
       "must_include": "none",
       "must_avoid": "none"
     },
     "unclear": ["colour_direction"]
   }
   ```

   Persist it as a draft - this does not complete intake, and `next` keeps
   returning the intake task:

   ```bash
   bookfactory intake golf-addict --draft --by chatgpt --from-file answers.json
   ```

2. **Show the operator one summary**, not a repeat of the form: every
   drafted answer, the unclear questions, and the production policy question
   (FULL AUTONOMOUS / VISUAL CHECKPOINT / CHECKPOINTED - recommend
   `visual_checkpoint` if asked). Wait for one reply.

3. **Record only the operator's own reply.** Merge any corrections they gave
   and the policy they chose:

   ```bash
   bookfactory intake golf-addict --confirm --by <operator> --policy visual_checkpoint --set colour_direction=muted
   ```

   Use `--by` with the operator's own name, never yours, and `--policy` with
   the policy they actually said, never inferred from silence. This is what
   writes `brief/intake.json`, sets `book.json`'s `intake.completed`, and
   records that the answers were drafted by you and confirmed by the
   operator, including anything they changed. **A fresh session must never
   need to ask again** - check `book.json`'s `intake` block first, and if
   `completed` is true, do not ask.

Never start the book with `bookfactory create --policy ...` to skip this: the
policy is the operator's choice, made through their own confirmed reply, not
yours to set in advance.

If the idea is too thin to draft from, fall back to asking the full
questionnaire in one compact, natural exchange, then persist the operator's
own answers directly with `bookfactory intake golf-addict --from-file
answers.json` (or individual `--set key=value` pairs) - the same command as
before, still never answering `production_policy` yourself.

The twelve questions, for reference:

1. What is the book, in one or two sentences?
2. Who will buy it?
3. Who is it for?
4. What should make them think "that's literally him/her"?
5. Humour level: mild, medium, fairly savage, or custom?
6. Visual feel: classic editorial caricature, old children's-book
   illustration, modern flat editorial, comic/cartoon, let Book Factory
   decide, or custom?
7. Colour direction: muted, colourful, a specified palette, or let Book
   Factory decide?
8. Main character: will you describe them, or should Book Factory invent one?
9. Approximate length: 60, 80, 100 pages, or let the system decide?
10. Anything that must be included?
11. Anything that must be avoided?
12. Production policy: FULL AUTONOMOUS (keep going unless genuinely blocked),
    VISUAL CHECKPOINT (show the visual set before mass production), or
    CHECKPOINTED (ask at every major creative gate)? Never answered by the
    agent, drafted or otherwise.

## 4. Follow `production_policy`, not your own judgement, about when to stop

`book.json` carries it, and every task from `bookfactory next` carries a
`mode` field computed against it. Read `mode`, do not infer it:

| `mode` | What it means | What you do |
| --- | --- | --- |
| `continue_automatically` | Ordinary production work, or a decision the operator already authorized. | Do the task. Call `next` again. Do not stop to report in. |
| `wait_for_operator` | Genuine judgement is required, or the recorded policy asks for a checkpoint here. | Stop. Explain the decision plainly and ask. |
| `remediate` | A prior draft failed a *measurable* requirement (resolution, missing file, that kind of thing) - not a judgement call. | Produce a corrected version and submit it. Do not ask permission to try again. |
| `blocked` | The book is explicitly blocked. | Read `book.json`'s `blocked.reason` and resolve it or ask, as `blocked.needs` says. |
| `complete` | `next` returned nothing. | Deliver the final files. |

In `autonomous` mode, `continue_automatically` covers ordinary approvals too -
including a page or illustration draft that passes every hard constraint and
your own visual/content review. You may run the approval yourself in that
case:

```bash
bookfactory approve golf-addict p058 --kind page --autonomous \
  --note "Passes hard constraints and matches the locked reference set."
```

`--autonomous` only succeeds when the recorded `production_policy` actually
authorizes it - it is not "approve because nobody objected". It also writes a
distinct audit trail entry (`authorization: autonomous_production_policy:...`)
so a human reviewing the log later can see exactly which approvals were yours
under the recorded authorization versus an explicit human decision. This is
not new permission to be careless: if you cannot match the references, or the
draft is a near miss, that is still `wait_for_operator` in substance even if
the field says otherwise - use your judgement about what "no ambiguity" means,
and when genuinely unsure, ask instead of approving.

To approve several ready pages or assets in one pass, `approve --all-passing`
takes the same `--autonomous` flag and the same authorization check as a
single approval above - it is refused unless the recorded policy authorizes
autonomous approval, and every approval it makes is audited the same way. It
never touches the cover (that stays `cover approve`), and the visual-lock and
full-wrap cover checkpoints below are unchanged: a draft passing its measured
checks only makes it eligible for this batch, not a substitute for your
visual/content review of each one.

Locks work the same way. When a lock task (`lock concept`, `voice`,
`manuscript` or `visual`) reads `continue_automatically`, run it with
`--autonomous`:

```bash
bookfactory lock manuscript golf-addict --autonomous \
  --note "Manuscript complete against the locked voice bible."
```

It is refused unless the recorded policy authorizes it, and it is refused for
a lock the policy keeps as a checkpoint (the visual lock under
`visual_checkpoint`). The audit entry carries the same
`authorization: autonomous_production_policy:...` marker as an autonomous
approval.

The full-wrap cover works the same way. Only in `autonomous` mode does the
cover-approval task read `continue_automatically`; inspect the wrap at print
size and as an Amazon thumbnail, then:

```bash
bookfactory cover approve golf-addict --draft v1 --by <agent> --autonomous
```

It records the same `authorization: autonomous_production_policy:...` marker,
on the cover and on the cover artwork it promotes. It is refused under
`visual_checkpoint` (the cover is the operator's approval there) and
`checkpointed`. `cover finalize` and `cover preflight` take no `--autonomous`:
finalize records no new decision, only carrying the reviewed approval (and its
marker) forward once the final interior matches, and preflight is a check.

In `visual_checkpoint` mode, the visual-lock task's `mode` will read
`wait_for_operator` even though everything else in the book runs
automatically - show the small reference set and stop there. The
full-wrap cover approval is the only other stop.

In `checkpointed` mode, every approval and every lock reads
`wait_for_operator`. Behave exactly as `integrations/chatgpt/BOOK_FACTORY.md`
already describes: submit, recommend, never approve.

The operator can change a book's policy later with
`bookfactory policy set <book> <mode> --by <operator>`, and `mode` follows it
from the next task. That command is theirs alone: never run it unless they
explicitly ask you to, and never suggest that a checkpoint is a reason to.
If a checkpoint seems unnecessary, say so and let them decide.

## 5. Do not stop just because one task finished

The most common mistake is treating each task as a conversation turn that
needs a human response. It does not. The loop is:

```
next -> read mode -> (do the task | ask | remediate) -> submit -> next -> ...
```

Keep calling `next` and acting on it until `mode` is `wait_for_operator`,
`blocked`, or `complete`. A `continue_automatically` task followed by another
`continue_automatically` task is the normal case, not a surprise.

## 6. Building the book from the idea

Book Factory's stage list is the checklist; you do not need to invoke each
stage by name, `next` walks you through it:

idea -> intake -> brief -> concept lock -> outline -> writing sample -> voice
lock -> manuscript -> manuscript lock -> visual bible -> visual references ->
visual lock -> page plan and specs (one file, `bookfactory plan --from-file`) -> illustrations -> deterministic
rendering -> QA -> assembly -> interior KDP preflight -> cover direction ->
native cover art (skipped only when the operator recorded a text-only cover)
-> typeset full wrap -> visual checkpoint -> cover preflight
-> release ready.

Two things worth naming explicitly:

**Writing calibration.** Before the manuscript, produce the voice/humour bible
and the writing sample the same way `AGENTS.md` describes, and treat the
banned-phrases list and recurring-joke rules as binding for the rest of the
manuscript. Re-reading your own last chapter for repeated rhetorical shapes
before submitting the next one is cheap and catches most drift; do not build
an automated humour scorer.

**Visual references you generate yourself.** For a new book, produce, in
order: a visual bible (from the questionnaire and the concept), the main
character reference, a supporting-character reference if the concept needs
one, a representative editorial illustration, a representative chapter-opener
illustration, and a diagram/graphic treatment if the book needs one. In
autonomous mode, evaluate each against the visual bible and lock the set
yourself (`bookfactory lock visual <book> --autonomous`) once every required
item passes. In visual-checkpoint mode, stop and show this small set before
mass-producing eighty more pages against it.

## 7. Generative vs deterministic references - do not mix them up

A task's `references` field only ever contains real, approved artwork
suitable for style matching. Book Factory will not hand you a synthetic
renderer-geometry fixture as a style example - those are tagged
`deterministic_layout` internally and filtered out before a visual task is
built. You do not need to check for this yourself; it is enforced structurally.
What you do need to do: never register your own placeholder or test image as
a real reference, and if you are ever asked to produce a fixture purely to
test layout geometry (not real book art), say so and tag it
`--reference-role deterministic_layout` when registering it, so it can never
leak into a real illustration task by accident.

## 8. Resolution - native pixels over intended print size, never upscaled

`min_pixels` on a task is already computed as native pixels needed for 300 DPI
at that artwork's *actual placement* on the page - a spot illustration needs
far fewer pixels than a full-bleed one. The same number is enforced at
submission, at approval, and in QA; there is no second, contradictory
threshold anywhere in the system. Cover artwork carries one more measured
requirement, `min_height_pixels`, because its printed height is fixed too. So:

- Generate at the size that comfortably clears `min_pixels` for the stated
  placement. A 1200px image is a completely valid submission for a 4-inch
  editorial spot; it is not valid for a full-page placement.
- If a draft comes back below the requirement, generate it again, larger.
  **Never upscale the existing file to manufacture compliance** - it adds
  pixels, not detail, and submitting it will not even help: the hard
  constraint is checked again on approval.
- If a placement genuinely cannot reach 300 DPI with the tools available, say
  so plainly rather than submitting something that will fail. That is a
  `wait_for_operator` situation even if a task nominally reads otherwise.

## 9. Auto-remediation, with a limit

Book Factory recomputes `mode: remediate` for a resubmittable, measurable
failure (below-DPI artwork, a missing file, a renderer overflow, and similar).
Fix it and resubmit without asking. After three failed attempts on the same
artefact it stops offering `remediate` and returns `wait_for_operator`
instead - stop there. Do not keep regenerating past that point, and do not
lower the bar to make a bad draft pass.

Genuinely ambiguous situations - competing readings of the humour direction, a
visual direction that cannot be reconciled with the brief, anything with an
IP/legal question that has no clearly safe answer - are `wait_for_operator`
regardless of policy. Recognise them and stop; do not push through by picking
an interpretation and hoping.

## 10. Session end, mid-book

If you hit a usage limit or the session simply ends, do nothing special -
there is no in-memory state to preserve. Everything that matters is already on
disk: the manuscript version, the locked visual style, every approved asset
and page, the open task, and `production_policy`. The next session, fresh,
does exactly what this file describes from step 1.

## 11. Finishing

When `bookfactory next` returns nothing for a new print project, both
`output/interior.pdf` and `output/cover.pdf` exist and have passed separate
preflights. The approved cover itself is the tracked, checksummed
`cover/drafts/cover-vN.pdf` that `cover/cover.json`'s `approved.path` names;
`output/cover.pdf` is its regenerable upload copy. Existing books without an explicit cover configuration retain
legacy interior-only behaviour until migrated.
