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

Add `--json` if you would rather parse it.

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
authorizes autonomous production (the operator chose this at intake, not by
saying nothing). Even then, `bookfactory approve` refuses `--autonomous`
unless that authorization is actually on record, and every such approval is
written to the audit log as granted under it - never as an ordinary approval.
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
operator already supplied every production detail up front). Either way, once
`book.json`'s `intake.completed` is true, never ask again - read
`brief/intake.json` instead.

## 4. Never mutate approved work

Anything under `pages/approved/` or `assets/approved/` is finished. Do not
overwrite it, do not regenerate it, do not "just fix" it.

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
`readable_image` are measured on submission; a draft that fails one is kept and
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
printed size. Never upscale a small file. Set title, author, spine text only
when it safely fits, and back copy as real selectable type. Reserve the KDP
barcode area and check the wrap at print size and the front as a thumbnail.
Submit a versioned draft with `bookfactory cover submit`.

In `visual_checkpoint` mode, the full wrap is an explicit operator approval
even if interior pages proceeded automatically. Do not run `cover approve` for
them. Their explicit approval records the reviewed artwork and PDF together.
For a provisional draft sized from a checksummed preserved interior,
`cover approve` records visual approval while the final interior is pending.
Once the assembled interior has matching dimensions, run
`cover finalize --draft <revision>` and then `cover preflight`. A changed
page count requires a revised draft and review. `status.readiness` distinguishes interior and cover.
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
| See the intake questionnaire | `bookfactory questionnaire --json` |
| Persist questionnaire answers | `bookfactory intake <book> --from-file <answers.json>` |
| Know where the book is | `bookfactory status <book> --json` |
| Know what to do next | `bookfactory next <book> --json` |
| See a task in full | `bookfactory task <book> --json` |
| Register artwork you made | `bookfactory submit <book> <asset-id> --kind asset --file <path>` |
| Register a page render | `bookfactory submit <book> <page-id> --kind page --file <path>` |
| Render a page from its spec | `bookfactory render <book> --page <page-id> --submit` |
| Check the whole project | `bookfactory validate <book>` |
| Run quality checks | `bookfactory qa <book> --json` |

Commands you must not run without the operator asking:
`approve`, `reject`, `lock`, `advance --force`, `assemble`, `preflight`.
