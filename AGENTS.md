# Rules for agents working in Book Factory

These rules apply to every AI agent - Claude, ChatGPT, or anything that comes
next - and to every human operating the system. They are vendor-neutral on
purpose. Vendor-specific notes live in `integrations/`.

If you are an agent and you read nothing else, read this file.

---

## 1. Read the repository first. Always.

Before doing anything, run:

```bash
bookfactory status <book-id>
bookfactory next <book-id>
```

Add `--json` if you would rather parse it. Both are read-only, as are `task`
and `validate`: they change nothing in the repository, so looking at a book
never leaves anything to commit. `qa` writes only its report.

The repository is the state of the project. Conversation history is not. If
something you were told in chat contradicts what is in the repository, **the
repository wins**, unless the user explicitly says they are changing it now - in
which case change the repository, then proceed.

Never reconstruct project state from memory or from what a previous message
said. Read the files.

## 1a. Work on main and verify persistence.

Work directly on the repository's `main` branch unless the operator explicitly
instructs you to use another branch for the specific task. Do not create a
feature, recovery, or temporary branch by default. Fetch remote `main` and
inspect Git status before changing files; preserve any newer remote work.

A branch assigned automatically by the tool or hosting environment that starts
your session (for example a generated `claude/...` or `codex/...` branch) is
not an operator instruction. It does not override this rule. If the
environment tells you to use such a branch, or blocks pushes to `main`, say so
to the operator **before** changing any files and ask which to use. Do not
quietly work on the assigned branch and mention it at the end.

Whenever any of your work ends up on a branch other than `main`, for any
reason (including with the operator's permission), end every report by
reminding the operator which branch holds it and what is not yet on `main`.
Then ask whether it should be merged into `main`. Keep reminding them at each
handoff until it is merged or the operator says to leave it on the branch.

A local commit is not a completed handoff. Push finished work to remote `main`
and verify that the commit and required artifacts are actually present there.
If write access, file-size limits, or another gate prevents this, preserve
important outputs in durable storage, link them from the repository when
possible, and report precisely what remains local and what is remote. Never
claim a project is restored or release ready merely because it exists in a
scratch checkout.

## 2. Do the task you were given. One at a time.

`bookfactory next` returns exactly one task. Do that task. Then run `next`
again. Do not work ahead, and do not do three stages at once because they look
easy.

`bookfactory task <book-id> --json` gives you the full task, including the
locked references you must match and the exact path your output belongs at.

## 3. Never approve anything on the user's behalf

Approval is a decision only the operator makes. It has to be an explicit
command.

* You may **submit** a draft.
* You may **recommend** approval, and say why.
* You may never run `approve` because the user did not object, because the work
  looks fine, or because it would unblock you.

Silence is not approval. Enthusiasm is not approval.

**The one exception**: a book whose recorded `production_policy` explicitly
authorizes autonomous production (the operator chose this - at intake, with
`bookfactory create --policy`, or with `bookfactory policy set` - not by
saying nothing). Even then, `bookfactory approve`, `bookfactory lock` and
`bookfactory cover approve` refuse `--autonomous` unless that authorization is
actually on record, and every such approval or lock is written to the audit
log as granted under it - never as an ordinary one. `lock --autonomous` and
`cover approve --autonomous` also refuse what the policy keeps as a
checkpoint (the visual lock and the full-wrap cover under
`visual_checkpoint`).
See `integrations/chatgpt/AUTONOMOUS_PRODUCTION.md` for the full contract.
This does not relax the rule for a `checkpointed` book, and it never means
"the operator probably would have said yes".

## 3a. Read `mode`, do not guess it

Every task from `bookfactory next` carries a `mode`: `continue_automatically`,
`wait_for_operator`, `remediate`, `blocked`, or `complete`. It already encodes
the book's recorded production policy plus whether a prior attempt failed a
measurable requirement - do the task, or stop, accordingly, instead of
re-deriving that judgement from the task's `type` or `approval_required`.

## 3b. Intake happens once, if it is required at all

A book started with `bookfactory create-from-idea` requires the intake
questionnaire before anything else - `next` returns a `type: "intake"` task
until it is answered. A book started with `bookfactory create` does not (its
operator already supplied every production detail up front, including the
required `--policy`).

Never choose a production policy for the operator. `create` refuses to run
without `--policy`; if the operator has not said which, ask them
(`visual_checkpoint` is the recommended answer). `bookfactory policy show
<book>` shows the recorded policy and is read-only. Either way, once
`book.json`'s `intake.completed` is true, never ask again - read
`brief/intake.json` instead.

An agent may draft the intake answers from the idea, to save the operator
retyping what they already said: `bookfactory intake <book> --draft --by
<agent> --from-file <answers.json>` saves a best-guess draft
(`book.json`'s `intake.draft`, `brief/intake-draft.json`), listing any
question it could not answer under `"unclear"`. A draft never completes
intake - `next` still returns the intake task - and it must never include
`production_policy`: the agent drafts answers, never the policy. Show the
operator one summary (the drafted answers, the unclear questions, and the
policy question) and wait for their reply. Only the operator's own reply is
recorded, with `bookfactory intake <book> --confirm --by <operator> --policy
<policy they chose> [--set key=value ...]`, which merges their corrections
and completes intake, on record as agent-drafted and operator-confirmed.

`create --series-from <book>` still requires `--policy`, chosen the same way.
It copies the source book's locked voice and visual style and its approved
references into the new book, but only as drafts recording where they came
from. Approving and locking them in the new book is decided by the new book's
own production policy and `bookfactory next` - never assumed already done
because the source book approved them.

## 4. Never mutate approved work

Anything under `pages/approved/` or `assets/approved/` is finished, and so
is the approved cover PDF (the `cover/drafts/` file that `cover/cover.json`'s
`approved.path` names). Do not overwrite it, do not regenerate it, do not
"just fix" it.

If an approved page needs changing:

```bash
bookfactory revise <book-id> <page-id> --reason "what is wrong"
```

That opens a revision, keeps the approved version live until the replacement is
approved, and preserves the old one in `_history/`. Then submit a new draft and
ask the operator to approve it.

Fixing a typo on page 58 must never cause page 58's artwork to be redrawn.

## 5. Image generation draws pictures. It never sets type.

This is not a style preference. Generated type contains spelling errors, and it
has shipped in a book before.

**Generate:** illustrations, characters, scenes, visual jokes, decorative
artwork, textures.

**Never generate:** chapter numbers, page numbers, headings, body text, tables,
quizzes, captions, contents pages, footers, any label in a diagram, any
structured layout.

All of those are typeset by the deterministic renderer from the page spec. If a
diagram needs labels, the artwork is drawn without them and the labels are set
as real type over or beneath it.

If a page spec sets `illustration.embedded_text: true`, treat it as a mistake
and raise it with the operator.

## 6. Match the locked references. Exactly.

After visual lock, every illustration task lists the approved reference files it
must match. Look at them. Match the character, the line style, the palette, the
edge treatment.

If you cannot match them, **stop and say so**. Do not submit something near
enough. Near enough is what produced a book where the main character's face
changed between chapters.

Read `style/visual-bible.md` before generating anything. It is the whole
specification, and it was written so that you do not need any prior
conversation.

A task's `references` only ever lists real, approved artwork suitable for
style matching - Book Factory filters out any reference tagged
`deterministic_layout` (a synthetic fixture built to test the renderer's
geometry, never real art) before building a visual task. If you ever need a
fixture purely to test layout, register it with
`--reference-role deterministic_layout` so it can never leak into a real
illustration task.

## 6a. Some constraints are measured, not judged

A task's `constraints` block mixes two kinds of requirement. `min_pixels` and
`readable_image` (and, for cover artwork, `min_height_pixels`) are measured on
submission; a draft that fails one is kept and
recorded, but it never becomes an approval task and `approve` will refuse it.
`next` returns a remediation task naming the failure instead.

The rest - matching the character, holding the style, keeping text out of the
artwork - are judgements for the operator. They still bind you; they are just
not enforced mechanically.

## 7. Write output where the task says

Every task carries `output.destination` and `output.submit_command`. Put the
file where it says and run the command it gives. Do not invent filenames, and do
not write into `approved/` directly - the only way into `approved/` is
`bookfactory approve`.

Drafts are cheap. Submit as many as you like; every revision is kept.

## 8. Never skip a gate

Locks exist to stop expensive mistakes:

* No manuscript before the voice is locked.
* No mass page production before the manuscript **and** the visual style are
  locked.
* No assembly before every page is approved.
* No print-book release before both interior and cover preflight pass.

If a gate blocks you, it will tell you exactly what is missing. Fix that, or
report it. `--force` exists for the operator, not for you.

## 9. Assembly is never creative

`bookfactory assemble` reads approved files and concatenates them. If you are
tempted to generate a missing page so assembly can finish, stop. A missing page
is a finding, not an obstacle.

## 9a. Print covers are part of production

New print projects include `cover/cover.json`. After the final interior PDF,
record cover direction, paper, finish, author and back copy. Calculate the
bleeding full wrap with `bookfactory cover dimensions`. Make native text-free
artwork against the approved character and editorial references. Submit it as
`cover-front-artwork`; native width AND height must reach 300 DPI at its actual
printed size. Never upscale a small file. `bookfactory cover build <book>`
then typesets the full wrap from `cover/cover.json`: title, author, back copy,
and spine text only when it safely fits, all as real selectable type; it
places the artwork (or none, for a text-only cover) and reserves the KDP
barcode area. It writes a print-size preview and a thumbnail preview and runs
the cover checks. Look at both previews; change `cover/cover.json`, never the
PDF, and rebuild until the wrap works at print size and as a thumbnail. Then
register the versioned draft with `bookfactory cover build <book> --submit`.

A text-only cover (no artwork at all) is the operator's decision, never a
shortcut when artwork is late. It is recorded with
`bookfactory cover artwork <book> --mode none --by <operator>`, which writes
`"artwork": "none"` to `cover/cover.json` and logs who chose it. Only the
artwork steps are then skipped; every other cover check still applies, and any
image the wrap does place must still reach 300 DPI.

In `visual_checkpoint` mode, the full wrap is an explicit operator approval
even if interior pages proceeded automatically. Do not run `cover approve` for
them. Their explicit approval records the reviewed artwork and PDF together.
Only under `autonomous` does the cover-approval task read
`continue_automatically`; then approve with
`bookfactory cover approve <book> --draft vN --by <agent> --autonomous`, which
records `authorization: autonomous_production_policy:autonomous` (on the
cover and on the artwork it promotes). It is refused under
`visual_checkpoint` and `checkpointed`. `cover finalize` records no new
decision - it carries the reviewed approval, and its `authorization`,
forward - so it has no `--autonomous` of its own.
For a provisional draft sized from a checksummed preserved interior,
`cover approve` records visual approval while the final interior is pending.
Once the assembled interior has matching dimensions, run
`cover finalize --draft <revision>` and then `cover preflight`. A changed
page count requires a revised draft and review. `status.readiness` distinguishes interior and cover.
The approved cover is the tracked draft itself (`cover/drafts/cover-vN.pdf`,
read-only, its sha256 in `cover/cover.json`'s `approved`); `output/cover.pdf`
is only a regenerable upload copy, recreated by `cover preflight`. `validate`
and `status` report an approved cover whose file is missing or changed.
An old project without `cover/cover.json` remains legacy interior-only until
`bookfactory cover init` migrates it. This command reopens a former
`release_ready` project and logs why, preserving interior approval history.

## 10. Say what you did, in terms of the repository

When you finish, report in terms a fresh session could verify:

* which command you ran,
* which file you wrote,
* which draft revision it became,
* what the operator now needs to decide.

Do not say "I've updated the book". Say "submitted `assets/drafts/p058-mate-taxonomy/p058-mate-taxonomy-v2.png`
as draft v2; awaiting approval".

---

## Quick reference

| You want to | Run |
| --- | --- |
| Start a book from one idea | `bookfactory create-from-idea "<idea>" --json` |
| Start a book, every detail known | `bookfactory create "<title>" --policy <policy chosen by the operator>` |
| Start book 2 of a series | `bookfactory create "<title>" --policy <policy chosen by the operator> --series-from <book>` |
| See the recorded production policy | `bookfactory policy show <book> --json` |
| See the intake questionnaire | `bookfactory questionnaire --json` |
| Persist questionnaire answers | `bookfactory intake <book> --from-file <answers.json>` |
| Draft intake answers from the idea | `bookfactory intake <book> --draft --by <agent> --from-file <answers.json>` |
| Confirm drafted intake answers (operator only) | `bookfactory intake <book> --confirm --by <operator> --policy <policy> [--set key=value ...]` |
| Know where the book is | `bookfactory status <book> --json` |
| Know what to do next | `bookfactory next <book> --json` |
| See a task in full | `bookfactory task <book> --json` |
| Plan every page with its spec in one file | `bookfactory plan <book> --from-file <plan.json>` |
| Register artwork you made | `bookfactory submit <book> <asset-id> --kind asset --file <path>` |
| Register a page render | `bookfactory submit <book> <page-id> --kind page --file <path>` |
| Render a page from its spec | `bookfactory render <book> --page <page-id> --submit` |
| Typeset the full-wrap cover | `bookfactory cover build <book> [--submit]` |
| Check the whole project | `bookfactory validate <book>` |
| Run quality checks | `bookfactory qa <book> --json` |

Commands that need authority: `approve`, `approve --all-passing`, `lock`,
`advance`, `assemble`, `preflight`, `cover approve`, `cover finalize`,
`cover preflight`. Run one only when:

* the operator asked you to, or
* it is what the current task from `bookfactory next` asks for, **and** that
  task's `mode` is `continue_automatically`. For an approval, a lock or
  `cover approve` that means using `--autonomous` (section 3), so the audit
  log records it as made under the book's recorded production policy.

If the task's `mode` is `wait_for_operator`, stop and ask, whatever the command.
`mode` already accounts for the production policy (section 3a), so you do not
need to work it out yourself.

`approve --all-passing` batches ordinary `approve` over every reviewable
draft; it needs the same authority as a single `approve` and follows the same
rule. An agent may run it only with `--autonomous`, and only when the book's
recorded production policy authorizes autonomous approval - exactly the check
a single `approve --autonomous` makes, and every approval it makes is audited
the same way. A draft passing its measured checks (section 6a) is not the
operator's judgement that it is right; it only means the draft is eligible to
be reviewed.

`reject`, `revise`, `advance --force` and `policy set` are for the operator
only. Run them only when the operator asks.

`policy set <book> <mode> --by <operator>` is how autonomy is granted or
withdrawn after a book is created. Never run it unless the operator
explicitly asks for that change, in those terms - not to unblock yourself, not
because a checkpoint seems unnecessary, and never with your own name in
`--by`. Every change is audited as `production_policy_changed`.
