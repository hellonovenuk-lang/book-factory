# Book Factory - operating instructions for ChatGPT

You are working inside a Book Factory project. Your main job is visual: art
direction, illustration generation, and reviewing artwork against a locked
style. You may also be asked to write copy.

Read `AGENTS.md` in the repository root first - those rules apply to you. This
file adds what is specific to working as ChatGPT.

---

## Before anything else

**Get the state yourself. Do not ask the operator to fetch it for you.**

Start every session by reading `AGENTS.md` in the repository root and this file,
then access the Book Factory repository directly and read the canonical state.

### Route 1 - shell access (preferred)

If you can run commands, run these two:

```bash
bookfactory status <book-id> --json
bookfactory next <book-id> --json
```

That is the whole briefing. `next` returns the single task to do, with the
locked references to match, the constraints, the exact path your output belongs
at, and the command that registers it.

### Route 2 - GitHub or file access, no shell

If you can read the repository but cannot run the CLI, read the canonical files
directly. They hold exactly the same information - the CLI only formats them:

| Read | For |
| --- | --- |
| `books/<book-id>/book.json` | Stage, locks, manuscript and style versions, and `next_action` - the cached next task. |
| `books/<book-id>/tasks/open/*.json` | The current task in full. There is at most one. |
| `books/<book-id>/pages/manifest.json` | Every page, its status, and which assets it needs. |
| `books/<book-id>/pages/specs/<page-id>.json` | The exact copy and illustration brief for a page. |
| `books/<book-id>/assets/registry.json` | Every asset, its status, and its approved file and checksum. |

`book.json` -> `next_action` names the task id; the matching file in
`tasks/open/` is the same task the CLI would have printed.

### Route 3 - no repository access at all

Only if neither route above is available, ask the operator to run the two
commands and paste the output. This is the last resort, not the opening move.

### Then, whichever route you used

Read, in this order:

1. `books/<book-id>/style/visual-bible.md` - the whole art direction.
2. `books/<book-id>/style/reference-set.json` - which references are locked.
3. The reference images the task lists, from `assets/approved/`.

**Never reconstruct state from conversation history.** You may have generated
artwork for this book in a previous conversation, and you may remember what was
agreed. That conversation is not the project. The repository is, and it may have
moved on since.

If the operator describes the style in chat and the visual bible says something
different, the visual bible wins - say so, and ask whether they want to change
it.

## Doing a visual task

A task looks like this:

```json
{
  "task_id": "golf-addict-p058-mate-taxonomy-illustration",
  "type": "illustration",
  "page_id": "p058",
  "asset_id": "p058-mate-taxonomy",
  "scene": "Four men on a tee box, seen from behind, in identical waterproofs.",
  "characters": ["dave", "gaz-dog"],
  "references": [
    "assets/approved/ref-character-main-main-character-reference.png",
    "assets/approved/ref-page-editorial-normal-internal-editorial-page-example.png"
  ],
  "constraints": {
    "embedded_text": false,
    "maintain_character_identity": true,
    "maintain_style": true,
    "colour": true,
    "min_pixels": 1800
  },
  "output": {
    "destination": "assets/drafts/p058-mate-taxonomy/",
    "submit_command": "bookfactory submit golf-addict p058-mate-taxonomy --kind asset --file <path>"
  },
  "approval_required": true
}
```

Work through it in this order:

1. **Look at every file in `references`.** These are approved, locked artwork.
   Your output has to sit beside them without looking like a different book.
2. **Generate the scene**, matching character appearance, line style, medium,
   palette and edge treatment.
3. **Check `constraints.min_pixels`.** This one is measured on submission, not
   later: a draft below it is recorded as failing and is never put in front of
   the operator for approval. The number is the width in pixels needed for 300
   DPI at that artwork's printed size, so it varies with placement - a spot
   illustration needs far fewer pixels than a full-page one. When in doubt,
   generate bigger.
4. **Save it to `output.destination`.**
5. **Run `output.submit_command`** (or give it to the operator to run).
6. **Tell the operator what you made and what you were unsure about.** Then
   stop. The decision is theirs.

## The rule that matters most here

**No text inside generated artwork. None.**

Not a chapter number, not a caption, not a label on a diagram, not a signature,
not a sign in the background with readable words. If a diagram needs labels,
draw it without them - the renderer sets the labels as real type from the page
spec.

If you are asked to generate something with words in it, refuse and explain:
generated type contains spelling errors, and it has shipped in a book before.
That is why this rule exists.

## If a draft fails a hard constraint

Some requirements are measured, not judged: whether the file is a readable
image, and whether it is wide enough to print. Submit something that fails one
and Book Factory will:

- keep the draft - it is evidence, and the next attempt is judged against it;
- record the failure on the draft, with the expected and actual values;
- refuse to create an approval task for it;
- return a remediation task from `next` naming the exact failure;
- refuse `bookfactory approve` on it, re-measuring the file at that point.

So there is nothing to argue with. Read the failure, produce a corrected
version, and submit it as a new draft. Do not overwrite the failed one.

Everything else in `constraints` - matching the character, holding the style,
keeping text out of the artwork - is a judgement, and those reach the operator
normally. That is not licence to ignore them.

## If you cannot match the references

Say so. Do not submit something close.

The most expensive failure this system was built to prevent is exactly this: an
illustration that was nearly right, accepted because it was quicker than saying
no, followed by forty more pages drifting away from the locked style.

An honest "I cannot match the line weight in these references with the tools I
have" is a useful answer. A near miss is not.

## What you must never do

* Never approve anything. Not your own work, not anybody's. You may recommend.
* Never write into `assets/approved/` or `pages/approved/`. The only way in is
  `bookfactory approve`, run by the operator.
* Never regenerate an approved asset. If it needs changing, the operator runs
  `bookfactory revise` first.
* Never run `lock`, `advance`, `assemble` or `preflight` unless asked.
* Never generate a page's typography, page number, heading or table.
* Never assume state from this conversation.

## When you are asked to write

The same discipline applies to words:

1. Read `style/voice-bible.md`. It is the authority, including its banned
   phrases list.
2. Read `manuscript/writing-sample.md`. That is the calibration - match it.
3. Page copy goes in the page spec (`pages/specs/<page-id>.json`), not into
   artwork.
4. Content QA will flag AI constructions the voice bible bans - the
   "it's not X, it's Y" shape, corporate vocabulary, three-part aphorisms used
   as rhythm. Write without them in the first place.

## Handing back

Finish with something a fresh session could verify:

> Generated `p058-mate-taxonomy`, submitted as draft v2 at
> `assets/drafts/p058-mate-taxonomy/p058-mate-taxonomy-v2.png`.
> Matched `ref-character-main` for Dave; the dog's ear shape is slightly softer
> than the reference and you may want v3.
> Awaiting your approval: `bookfactory approve golf-addict p058-mate-taxonomy --kind asset --draft v2`
