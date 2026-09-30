---
name: nightly-book-research
description: Night-time research run that picks the one next book Book Factory should make, backs it with Amazon and web evidence, writes a full book plan, and saves it on main for Kieran to say go or no in the morning. Run by the scheduled routine three nights a week; also when Kieran asks for a fresh book proposal.
argument-hint: "[optional focus, e.g. 'kids books' or 'Valentine's']"
---

# Nightly book research

Kieran set this up on 2026-09-30: three nights a week, research the next
book we should create and write its plan, so that in the morning he only has
to decide go or no. You run alone, with nobody to ask. Do the research
properly, make one clear recommendation, save it, and stop.

Focus for this run: $ARGUMENTS (if empty, use the rotation in step 2).

## Hard limits (whatever you find)

This run proposes; it never produces. So never:

- create a book or write anything under `books/` (`bookfactory create`,
  `create-from-idea`, `intake`, `plan`, `submit` and the rest are for after
  Kieran says go);
- approve, lock, revise, advance or change any policy or picture budget;
- spend Higgsfield credits (reading the balance is fine);
- publish anything, touch KDP, ads, Gmail or any outside account;
- edit `PLAN.md`, `AGENTS.md`, `CLAUDE.md`, code, templates or skills.

You may write only: your proposal file, the index
`docs/research/nightly/README.md`, and (on Kieran's reply) one line in
`IDEAS.md`.

## 1. Get on main

Follow `CLAUDE.md` "Branch policy": `git fetch origin main`, then be on
`main` matching `origin/main` (if the session started on a `claude/...`
branch, switch to `main` yourself; don't ask). If a push to `main` is
refused at the end, say so plainly in your final message with the error.

## 2. Read what already exists

- `docs/research/nightly/README.md`: every earlier proposal and Kieran's
  decision. **Never re-propose an idea he said no to**, and read his reasons:
  they are the best guide to what he wants. Don't repeat an idea still
  "awaiting Kieran" either.
- `docs/research/2026-09-30-new-book-types.md`: the first big research run
  (puzzle and quiz books first; colouring, picture books and short stories
  parked, and why).
- `docs/BOOK-IDEAS.md` (hobby-addict ideas), `KDP/README.md` (what is live
  or ready), `bookfactory list` (books in the factory).
- `IDEAS.md`, for any build work already queued (e.g. the puzzle page).
- Check the date: the next gift date that matters (Christmas; Valentine's;
  UK Mother's Day in March; Father's Day in June; back to school). A gift
  book needs to be live about 5-6 weeks before it.

**Rotation.** Unless a focus was given, take the next angle after the last
proposal's angle in the index, so the week covers different ground:

1. **Dave series**: the next hobby-addict gift book (same look and buyer).
2. **New format for the same buyers**: puzzle, quiz or activity versions of
   the Dave world.
3. **A new line**: murder-mystery puzzles, kids' joke / would-you-rather
   books (separate pen name), large-print puzzles, or something the data
   turns up.

## 3. Gather evidence

- Refresh Amazon data (read-only, about 10 minutes):
  `python3 scripts/research/amazon_bestsellers.py --out <scratch>/amazon.csv`
  Add lists that fit tonight's idea with `--list market:node:"name"`; find
  node numbers with `--children uk:` or `--children uk:<node>`. Keep the
  CSV in the scratchpad; don't commit it.
- Web search for the idea: trend articles, the leading competitor books,
  anything new in KDP rules. Prefer primary sources (KDP help pages,
  Circana, The Bookseller, Publishers Weekly) over blogs.
- Look closely at the 5-10 books your book would sit next to: rank, price,
  pages, reviews, publication date, publisher (small or big), what their
  low reviews complain about. That is where our angle comes from.
- `mcp__Higgsfield__balance` if the book needs pictures (credits decide
  whether it's feasible).

## 4. Choose one book

Score the candidates on: demand (ranks, reviews, trend), room for a small
publisher (small publishers in the top 20), fit with what we have (Dave
buyers, look, voice), effort in Book Factory (typeset pages cost nothing;
each picture costs about 2 credits; new page types need a build phase),
money per copy (see the royalty table in the first report), and timing.

Pick **one** recommendation and two runners-up. Be honest when the evidence
is thin: "weak evidence, worth a cheap test" is a fine verdict.

## 5. Write the proposal

File: `docs/research/nightly/YYYY-MM-DD-<short-slug>.md`. Plain English,
technical words explained in brackets the first time (`CLAUDE.md`, "Working
with Kieran"). Sections, in order:

1. **Decision needed**, one line at the top: the book, and "Reply `go` or
   `no` (and why)".
2. **The pitch**: exact title and subtitle, who buys it and for whom, when
   (which gift date), why now, and what makes it different from what's on
   Amazon. Five lines, no more.
3. **Evidence**: a short table of the numbers that matter, plus the
   competitor table (title, rank, price, pages, reviews, small/big
   publisher). Say how sure you are.
4. **The book plan**: format (trim, black and white or colour, target
   pages, price UK/US, what you'd earn per copy), pen name (Dave brand or a
   separate one), the contents page by page or section by section, the
   picture budget (how many pictures, if any), and the cover direction.
5. **Samples**: enough real copy for Kieran to judge the voice and idea,
   e.g. the back-cover blurb plus 3 sample pages, 5 sample puzzles or jokes,
   or the opening of a chapter. Follow the voice of the live books if it's
   a Dave book.
6. **What Book Factory needs**: what it can make today, and any build work
   first (a new page type, a generator). If build work is needed, estimate
   it in phases (one phase = one sitting).
7. **Timeline**: the steps to "live on Amazon" and the date it could be live.
8. **Risks** and **runners-up** (one line each).
9. **Sources** (links).

## 6. Update the index and save

- Add a row to the table in `docs/research/nightly/README.md`: date, book,
  angle, one-line reason, link, status `awaiting Kieran`.
- Commit only the proposal and the index, naming both files (never
  `git add -A`), with a message saying what was proposed; push to `main`,
  then fetch and check `origin/main` has your commit (`AGENTS.md` 1a).

## 7. Report

End with a short message for Kieran's morning, as the push notification
and the first thing he reads:

- the book in one line, and why in one line;
- what it would take (e.g. "needs one build phase, then about 3 sittings");
- the proposal's path;
- **Your next step:** "Reply `go` or `no`, with a reason if no."

## When Kieran replies in this session

- **"go"**: set the row's status to `go, YYYY-MM-DD`; add one line to
  `IDEAS.md` (the book and the proposal's path); commit both, push, check.
  Then say what starts it: `/write-book "<title>"` if Book Factory can make
  it today, or `/plan-phase` for the build work first. If a phase is open in
  `PLAN.md`, say so and let Kieran choose (`CLAUDE.md`: protect the open
  phase). Don't start the book in this session unless he asks.
- **"no"** (with or without a reason): set the status to `no, YYYY-MM-DD:
  <his reason in his words>`; commit, push, check. Future runs learn from it.
- **Anything else** (questions, changes): answer, update the proposal if
  he asks, and keep the status `awaiting Kieran`.
