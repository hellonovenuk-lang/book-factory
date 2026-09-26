# IDEAS

The parking lot. When a new idea comes up in the middle of a phase, it goes
here as one line so it is not lost, and work goes back to the open phase.

When a phase finishes, look here to choose the next one. Move an idea into
`PLAN.md` when it becomes a phase; delete it when it is done or dropped.

Format: `- YYYY-MM-DD: the idea, in one line (where it came from)`

## Waiting

- 2026-09-22: Publish the Claude Code audit report as a private page to refer back to (audit session)
- 2026-09-23: Approval guard blocks a plain Python text edit of `PLAN.md` because the text mentions "approve"; make it tell real commands from words in text (Phase 4 planning)
- 2026-09-23: `spec <book> --from-file` for many pages at once, for a book whose plan already exists without specs (Phase 8 planning)
- 2026-09-23: For review item #4 (images), try the Higgsfield MCP first: it uses Kieran's existing subscription credits (no API key), so Claude could draw and submit illustrations in chat. The Higgsfield API (pay-as-you-go dollars, separate from the subscription) is the fully automatic route later
- 2026-09-23: When the roadmap is finished: publish artifacts (private pages) explaining each workflow, plus one page showing the complete pipeline and how the workflows connect (Kieran)
- 2026-09-23: A picture budget per book, chosen by the operator (e.g. cover + chapter openers only; rest typeset text, checklists, exercises and diagrams), recorded on the book and checked when the page plan is written. Nothing limits the number of pictures today. (Kieran). *Done in Phase 11. The chart was only an example; Kieran dropped it 2026-09-23.*
- 2026-09-23: `produce` slice 3: write briefs, manuscript and page copy through the Claude API (review #8, Phase 12 planning). *Decided by Kieran 2026-09-23: no API call. Claude Code writes the copy itself (on his subscription), inside the slice 5 morning routine, following the voice rules; `produce` does the rest.* *Done in Phase 14: `/write-book`.*
- 2026-09-23: `produce` slice 4: make pictures through Higgsfield inside the loop, within the picture budget (review #8, Phase 12 planning) *Done in Phase 19.*
- 2026-09-23: Update `integrations/claude/BOOK_FACTORY.md`: it still calls ChatGPT Work the normal production route, but Kieran produces in Claude Code with pictures through the Higgsfield connector (Kieran, Golf Addict's Guide start)
- 2026-09-23: A command to change a book's format after `create` (colour or black and white, trim, page count), audited; the Golf Addict's Guide needed `book.json` edited by hand to switch to black and white (Golf Addict's Guide brief)
- 2026-09-23: `produce` slice 5: a scheduled Claude Code routine that starts `produce` in the morning and reports where it stopped (review #8, Phase 12 planning)
- 2026-09-23: Let `/write-book` also do the concept, voice and manuscript locks when a book's policy is `autonomous` (Phase 14 planning)
- 2026-09-24: Cover build doesn't notice when the author line overlaps the front artwork (Golf Addict's Guide cover, 4.7 x 7 in art); add an overlap check (found on the Golf Addict's Guide)
- 2026-09-24: Guard: let `advance --to release_ready`, `cover finalize` and `cover preflight` through when the book's next task asks for them and its mode is continue_automatically (today they always ask, so auto mode stops at the very end) (Golf Addict's Guide retrospective) *Done in Phase 19.*
- 2026-09-24: `bookfactory plan --from-manuscript`: turn a locked manuscript into a page plan (activity pages for numbered activities, text pages, openers), fit-test every page in both engines and split overflowing openers; the Golf plan was built by a one-off scratch script (Golf Addict's Guide retrospective). *Done in Phase 17.*
- 2026-09-24: Picture checks on submission: flag colour in a black-and-white book's art (and offer an automatic greyscale copy) and flag likely pseudo-lettering; both were caught by eye on the Golf book (Golf Addict's Guide retrospective)
- 2026-09-24: Ask the big creative decisions at intake: main character's age and family, cover style (big lettering or picture), colour or black and white, exact title; changing Dave's age and the cover style late cost rework and credits (Golf Addict's Guide retrospective). *Done in Phase 18.*
- 2026-09-24: A "big-lettering gift book" cover preset (colours, fonts, banner) so a new book's cover starts from what sells, not the plain default (Golf Addict's Guide retrospective)
- 2026-09-24: Higgsfield returned nano_banana_2 when nano_banana_pro was requested, every time; check what we're paying for (Golf Addict's Guide retrospective)
- 2026-09-26: `/write-book` says `produce` stops with `picture` for character and layout references too, but `produce` only does it for a page illustration (references give `not_mechanical`); make the two agree (padel book, first live run)
