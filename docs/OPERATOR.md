# Making a book with Book Factory

This is the guide for you, the person producing the book. It assumes no
programming knowledge. Every step is a command you type; the system tells you
what the next one is.

---

## The whole thing in one paragraph

You create a project. You fill in a brief and lock it. You write a sample, agree
the voice, and lock it. You write the manuscript and lock it. You get a small set
of reference artwork approved and lock the visual style. Only then do you plan
pages and produce them. Each page gets specified, illustrated, rendered and
explicitly approved. Then quality checks, then assembly, then a KDP check. At
every point, `bookfactory next` tells you what to do.

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
bookfactory create "Golf Addict" --pages 90
```

This creates `books/golf-addict/` with guided templates already in it. Every
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

## 12. Done

```bash
bookfactory advance golf-addict --to release_ready
```

`output/interior.pdf` is your interior file.

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
bookfactory create "Title"                     start a project
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
