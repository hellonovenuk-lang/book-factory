# Making a book with Book Factory

This is the guide for you, the person producing the book. It assumes no
programming knowledge. Every step is a command you type; the system tells you
what the next one is.

---

## The fast path: one idea, ChatGPT does the rest

For a normal new book, you do not need to work through the steps below by
hand. Open a fresh ChatGPT Work session with access to this repository and say
something like:

> Create a new Book Factory project. Idea: a fake rehabilitation manual for
> men who are addicted to golf. Ask me the setup questionnaire, then continue
> autonomously through the whole book unless you genuinely need my judgement.

ChatGPT will create the project, ask you a short, one-time questionnaire
(twelve questions, covering the idea, the buyer, the humour level, the visual
feel, and how hands-off you want it to be), and then drive the entire
pipeline - brief, manuscript, visual development, illustrations, rendering,
QA, assembly and KDP preflight - stopping only where the repository or your
own answers say it must. If the session ends partway through, open a new one
and say "Continue Book Factory project \<book-id\>" - it resumes from exactly
where the repository left off.

Claude Code is not part of this loop. It is the tool used to build and
maintain Book Factory itself; you do not need it to make a book.

The rest of this document is the manual, step-by-step version - useful if you
want the checkpointed workflow, want to understand what is happening under the
hood, or are doing something the fast path does not cover.

## The whole thing in one paragraph

You create a project. You fill in a brief and lock it. You write a sample, agree
the voice, and lock it. You write the manuscript and lock it. You get a small set
of reference artwork approved and lock the visual style. Only then do you plan
pages and produce them. Each page gets specified, illustrated, rendered and
explicitly approved. Then quality checks, then assembly, then a KDP check, then
the full-wrap print cover. At every point, `bookfactory next` tells you what to
do.

---

## Setup, once

```bash
pip install -e .
bookfactory doctor
```

`doctor` should report a render backend. If it does not, nothing can be printed;
see `docs/RENDERING.md`.

## The loop

There are only two commands you need to remember:

```bash
bookfactory status <book>    # where am I?
bookfactory next <book>      # what do I do?
```

Run `next`, do what it says, run `next` again. That is the job.

---

## 1. Start a project

```bash
bookfactory create "Golf Addict" --pages 90 --policy visual_checkpoint
```

This creates `books/golf-addict/` with guided templates already in it.

`--policy` is required - there is no default, because it decides how often
production stops for you:

| Policy | Stops for you |
| --- | --- |
| `visual_checkpoint` (recommended) | At the visual lock (the small reference set) and the full-wrap cover. Everything else runs. |
| `checkpointed` | At every approval and every lock. |
| `autonomous` | Only when production is genuinely blocked. |

You can change your mind at any point:

```bash
bookfactory policy show golf-addict
bookfactory policy set golf-addict checkpointed --by "Your Name" --reason "Want to see every page"
```

`policy set` records who changed it, when, why, and from what, in the audit
log (`bookfactory history golf-addict --event production_policy_changed`),
and the next task's `mode` follows the new policy straight away. It is yours
to run: agents are told never to run it unless you ask. Every
template has TODO markers; the system will not let you lock anything while
they are still there.

Useful options: `--bw` for a black and white interior, `--trim 5.5x8.5` for a
different size, `--bleed` if artwork runs off the edge of the page,
`--id` to choose the folder name yourself.

## 2. Fill in the brief

Open `books/golf-addict/brief/brief.md` and answer it honestly. The section that
matters most is **recognition triggers** - the specific real behaviours that make
a buyer say "that is literally Dave". Those are what they are paying for. Five is
a minimum; ten is better.

Also fill in `concept.md` and `audience.md`.

Then:

```bash
bookfactory lock concept golf-addict
```

If it refuses, it will tell you exactly which file still has placeholders in it.

## 3. Agree the voice before writing the book

Write `manuscript/writing-sample.md`: one ordinary passage, one structured piece
like a checklist, and one chapter opener. Roughly two pages in total.

Read it. Is that the book? If not, change it now - it is two pages, not ninety.

When it is right, write the rules that made it right into
`style/voice-bible.md`, including the **banned phrases** list. Anything that
annoyed you and had to be edited out goes on that list, and the quality checks
will catch it if it comes back.

```bash
bookfactory lock voice golf-addict
```

## 4. Write the manuscript

Write `manuscript/manuscript.md` against the locked voice. Anything that will
appear on a page should appear here first - page specs quote the manuscript, so
nothing gets invented at layout time.

```bash
bookfactory lock manuscript golf-addict
```

Locking takes an immutable, checksummed snapshot into `manuscript/versions/`.
You can keep editing the working file afterwards; the pages reference the locked
version, so they cannot silently drift.

## 5. Settle the look before you draw ninety pages

This is the step that, skipped, cost the most last time.

Fill in `style/visual-bible.md` properly: what the character looks like, what
they wear, line style, medium, palette, how the edges of illustrations are
treated, and - importantly - the **prohibited deviations**, the things that
drifted before.

Then get the reference set approved. `bookfactory next` walks you through it one
at a time. The default set is:

1. Main character
2. Supporting character or pet
3. A chapter opener example
4. A normal internal page example
5. A diagram, checklist or test page example
6. Palette and type rules on one sheet

If your book has no supporting character, delete that entry from
`style/reference-set.json`. Add entries if you need more.

For each one, `next` gives you a task. Hand the task to ChatGPT along with
`integrations/chatgpt/BOOK_FACTORY.md`, get artwork back, and:

```bash
bookfactory submit golf-addict ref-character-main --kind asset --file dave.png
bookfactory approve golf-addict ref-character-main --kind asset
```

Or reject it and ask for another:

```bash
bookfactory reject golf-addict ref-character-main --kind asset --reason "Wrong coat"
```

Rejected work is kept, never deleted. Submit as many drafts as you like.

When all six are approved:

```bash
bookfactory lock visual golf-addict
```

**Now, and not before, page production is allowed.** Everything drawn from here
on points at these exact files.

## 6. Plan the pages

Write a JSON file listing every page in order:

```json
{
  "pages": [
    {"title": "Half title", "type": "front_matter"},
    {"title": "Contents", "type": "contents"},
    {"title": "The First Warning Sign", "type": "chapter_opener", "chapter": 1},
    {"title": "The Mate Taxonomy", "type": "editorial_illustration", "chapter": 1,
     "required_assets": ["p004-mate-taxonomy"]}
  ]
}
```

```bash
bookfactory plan golf-addict --from-file plan.json --front-matter 2
```

`--front-matter 2` means the first two pages carry no printed number.

Page types available: `chapter_opener`, `editorial_illustration`,
`text_illustration`, `checklist`, `diagnostic_test`, `comparison`, `diagram`,
`quote`, `certificate`, `closing`, `front_matter`, `contents`.

You can also add pages one at a time:

```bash
bookfactory plan golf-addict --add --title "The Mate Taxonomy" --type editorial_illustration --chapter 1
```

## 7. Produce the pages

For each page, `next` will ask for three things in order:

**A page spec** - `pages/specs/p004.json`, holding the exact final copy and a
brief for the illustration. Copy comes before artwork, always: the picture is
drawn to fit the words.

**The artwork** - hand the task to ChatGPT, get a picture, submit and approve it.

**The render** - this is deterministic and takes a second:

```bash
bookfactory render golf-addict --page p004 --submit
```

Leave off `--page` to render and submit every page that is ready in one go:

```bash
bookfactory render golf-addict --submit
```

It skips a page with no spec yet, and skips a page that is already approved
(unless you have opened a revision on it) - approved work is never touched. If
a page fails to render, it is listed with the reason and the command still
renders the rest; fix the spec and re-run just that page with `--page`.

Then look at it and decide:

```bash
bookfactory approve golf-addict p004 --kind page
```

Nothing is approved because you did not complain. Approval is always a command.

## 8. Look at the whole book

```bash
bookfactory review golf-addict
```

Produces, in `books/golf-addict/output/review/`:

* `full-book-contact-sheet.pdf` - every page as a labelled thumbnail, twelve to
  a sheet, with gaps and drafts marked. This is where you spot drift.
* `full-book-review.pdf` - the book as it currently stands.
* `chapter-01.pdf`, `chapter-02.pdf`, ... - chapter by chapter.
* `production-status.md` - a table of what is done.

Built from existing renders only. It never draws anything new.

## 9. Quality checks

```bash
bookfactory qa golf-addict
```

Four layers: content, visual, technical and assembly. Errors must be fixed.
Warnings are usually worth reading. Items marked as needing a human are things a
machine cannot judge - whether a joke lands, whether the character has drifted -
and you have to look at the review PDF for those.

## 10. Assemble

```bash
bookfactory assemble golf-addict
```

Produces `output/interior.pdf`. Assembly reads only approved pages, checks every
checksum, and keeps manifest order. If anything is missing or altered it stops
and tells you which page. It will never quietly use the nearest file.

## 11. KDP check

```bash
bookfactory preflight golf-addict
```

Checks trim size, page count, margins, gutter, embedded fonts and file size
against `bookfactory/kdp/profiles/kdp-default.json`. Amazon changes its rules; if
they do, that file is the only thing that needs updating.

Warnings are informational - a short gift book cannot carry text on its spine,
which is not a defect. Failures must be fixed.

## 12. Full-wrap print cover

New print books require `cover/cover.json`. Set paper, finish, direction,
author, back copy and the intended artwork placement. After the interior is
final, `bookfactory cover dimensions <book>` calculates bleed and spine from
its actual PDF page count. Register `cover-front-artwork` as `cover_artwork`
against locked references. Submit native text-free art through the normal
asset draft workflow.

Build the wrap from `cover/cover.json` rather than typesetting it by hand:

```bash
bookfactory cover build <book>
```

This places the front artwork (or none, for a text-only cover), sets title,
author, back copy and, when the page count allows it, spine text - all as
real selectable type - and reserves KDP's barcode zone. It writes a
print-size preview and an Amazon-thumbnail preview to look at, and runs the
cover checks. If something needs to change, edit `cover/cover.json`, never
the PDF, and build again. Once the checks pass, register the draft:

```bash
bookfactory cover build <book> --submit
```

(`bookfactory cover submit <book> --file <full-wrap.pdf>` still registers a
cover PDF made another way.)

Under `visual_checkpoint`, wait for the operator's explicit approval:

```bash
bookfactory cover approve <book> --draft vN --by '<operator>'
bookfactory cover preflight <book>
```

Under `autonomous`, an agent may approve the cover itself with
`cover approve ... --autonomous`; the audit log and `cover/cover.json` then
carry `authorization: autonomous_production_policy:autonomous`. That flag is
refused under `visual_checkpoint` and `checkpointed`.

Approval preserves previous drafts and promotes their native artwork. The
approved cover is the chosen draft itself, `cover/drafts/cover-vN.pdf`: it is
made read-only and `cover/cover.json` records its path and sha256 under
`approved`, so it survives a fresh clone and is stored once. A copy is written
to `output/cover.pdf` for upload; that copy is gitignored and `cover preflight`
recreates it. `bookfactory validate` and `status` report an approved cover
whose tracked file is missing or changed. An approval recorded before `path`
existed resolves to the draft of the same revision when the checksums match;
if none does, `validate` says so and the cover needs submitting and approving
again. The separate cover preflight checks the
final size, printable text, barcode clearance, and native image resolution at
actual placement. A new submission never silently approves itself.

A cover with no artwork - type and simple vector shapes only - is a recorded
choice, not a missing file:

```bash
bookfactory cover artwork <book> --mode none --by '<operator>' --reason '...'
```

That sets `"artwork": "none"` in `cover/cover.json` (see
`schemas/cover.schema.json`) and logs `cover_artwork_mode_set`. `next` then
skips registering and drawing `cover-front-artwork`, and submission and
approval no longer look for it. Everything else is checked as before: wrap
size, selectable title/author/back copy, embedded fonts, safety margins, the
barcode zone, and 300 DPI for any image the wrap does contain. Switching mode
supersedes drafts still awaiting review and clears the cover preflight, so
submit a new draft afterwards. `--mode native` switches back.

For an older interior-only project, run `bookfactory cover init <book>` to
opt into this new gate. If it was already `release_ready`, that command logs a
move back to `cover_production`. Its prior interior and approvals stay intact.

## 13. Done

```bash
bookfactory advance golf-addict --to release_ready
```

`output/interior.pdf` and `output/cover.pdf` are the two upload files for a
cover-required print project (the latter a copy of the tracked approved cover
draft). `status.readiness` reports their states separately.

---

## Changing something already approved

Never edit an approved file. Do this instead:

```bash
bookfactory revise golf-addict p058 --reason "Page number in the caption is wrong"
```

That opens a revision. The currently approved page stays canonical - the book
stays assemblable - while you produce the replacement. Edit the spec, re-render,
submit, and approve the new version. The old one moves to
`pages/approved/_history/` and is never deleted.

This is the only way to change approved work, and that is the point: fixing a
typo on page 58 must never cause page 58's artwork to be redrawn.

## When something looks wrong

```bash
bookfactory validate golf-addict
```

Checks the structure of everything: schemas, the page manifest, every checksum.
It tells you precisely what is wrong.

If you have just pulled the project from git, file permissions do not survive the
transfer:

```bash
bookfactory relock golf-addict
```

## Starting a fresh AI session

Open any assistant and say:

> Continue Book Factory project golf-addict.

Point it at `AGENTS.md`, and at `integrations/chatgpt/BOOK_FACTORY.md` if it is
ChatGPT. It will read the repository and pick up exactly where you left off. You
never have to explain the history again.

## The one-line reference

```
bookfactory create "Title" --policy <p>        start a project (manual, every detail up front)
bookfactory create-from-idea "One-line idea"   start a project (autonomous flow, questionnaire required)
bookfactory questionnaire                      show the intake questionnaire
bookfactory intake <book> --from-file a.json   persist the questionnaire answers, once
bookfactory policy show <book>                 the recorded production policy
bookfactory policy set <book> <p> --by <you>   change it (operator only, audited)
bookfactory status <book>                      where it stands
bookfactory next <book>                        what to do next
bookfactory task <book>                        the current task in full
bookfactory plan <book> --from-file plan.json  plan the pages
bookfactory spec <book> p004 --from-file s.json write a page spec
bookfactory asset add <book> <asset-id>        register artwork
bookfactory submit <book> <id> --file art.png  register a draft
bookfactory approve <book> <id>                approve it
bookfactory reject <book> <id> --reason "..."  reject it
bookfactory revise <book> <id>                 change approved work
bookfactory lock concept|voice|manuscript|visual <book>
bookfactory render <book> --page p004 --submit
bookfactory review <book>                      contact sheet and review PDFs
bookfactory qa <book>                          quality checks
bookfactory validate <book>                    structural check
bookfactory assemble <book>                    build the interior PDF
bookfactory preflight <book>                   check against KDP
bookfactory history <book>                     what happened to this book
```
