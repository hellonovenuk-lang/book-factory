# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 20 (a smoother `/write-book`). 20.2, 20.3, 20.4 and 20.5 are done, checked and on `main` (full suite 788 passed with them). **20.1 (go-ahead) and 20.6 (skill and guides) are unfinished on the branch `phase-20-go-ahead`** (commit a437900; Kieran agreed to the branch 2026-09-27). Phases 17, 18 and 19 are done (not yet archived; `/handover` moves them to `docs/PLAN-ARCHIVE.md`).
> **Resume Phase 20 in a fresh session (it starts from `main`, where the guard's self-lock doesn't exist):** check out `phase-20-go-ahead`, then (1) remove the self-lock Kieran declined (option A): the settings.json Edit/Write deny rules for `.claude/hooks/**`, `**/.claude/hooks/**`, `.claude/settings.json`, `.claude/settings.local.json`, and the guard's Bash-write denial of `.claude/hooks/` and `.claude/settings*.json` (keep the denial of writes to `~/.claude/projects/**` and the transcript); (2) make the three pending guard fixes from the 20.1 builder's report, reproduced here: add "if", "once", "when", "whenever", "provided", "assuming" to `_NEGATORS`; in `parse_decision` turn a leading "go ahead and" into a polite lead before splitting at "and"; in `writes()` take `unzip`'s destination only from `-d` (not `-o`); (3) delete `.claude/hooks/record-go-ahead.py` (unregistered, unused); (4) 20.6: finish `docs/OPERATOR.md` and `GLOSSARY.md`, and check the skill and guides describe the go-ahead as reading Kieran's real last message (strict wording, exact commands, never chained, never helpers), not a slip file; (5) second safety review of the guard (Opus), full suite, demo build in a throwaway copy, test-drive; (6) merge the branch into `main`, push, delete the branch.
> **Finished:** Phase 19: `produce` stops with `picture` at a page picture; `/write-book` draws it through Higgsfield, checks it, submits it and approves it with `--autonomous` only when the task's mode allows (never cover artwork or the full-wrap cover); the guard lets `advance --to release_ready`, `cover finalize` and `cover preflight` through when the book's next task asks for exactly that in continue_automatically, and an older hole (`cover --root X finalize`) is closed. 671 tests pass. The first live picture inside the loop is on the next real book (it spends Higgsfield credits). Phase 18: intake now also asks the exact title, the main character's age/family/look, colour or black-and-white printing and the cover style (big lettering, picture, or let Book Factory decide); confirming sets the book's title, `format.colour` and a text-only cover for big lettering, each audited; the brief, visual and cover tasks list them as "fixed at intake". Test-driven on a new book in a scratch copy. Helpers are no longer capped at 3 (Kieran); the checker may never stash or reset the real checkout. Earlier: Phase 17 (`plan --from-manuscript`), and the Golf book's p055/p061 table fix (still Release Ready, not yet uploaded).
> **Also finished (2026-09-26):** the first real `/write-book` run: *The Padel Addict's Guide to Talking About Anything Else* (`padel-addicts-guide`) went from idea to Release Ready in one session (80 pages, 9 opener pictures drawn and approved in the loop, 26 Higgsfield credits, big-lettering cover approved by Kieran; not yet uploaded). It found three gaps, now in `IDEAS.md`: references don't get the `picture` stop, the fit test misses text running into the bottom margin, and a revision doesn't mark the assembled interior stale.
> **Next action:** start the next real book with `/write-book` (first live run of pictures in the loop), or plan Phase 20 from `IDEAS.md`.

**Unfinished, carried over:**
- none (the first live runs of `approve --all-passing`, of `produce` page approvals and of `/write-book` are Kieran's, on a real book; helpers are rightly blocked from the first two)

**Don't try again:**
- `git rev-parse --short HEAD origin/main` fails ("Needed a single revision"): run `git rev-parse --short` once per ref.
- Testing a new hook in the same session that created `.claude/settings.json`: hooks load only when a session starts, so the trial does nothing. Permission deny rules do work straight away. (Edits to an already-registered hook script do take effect at once.)
- Running `scripts/build_demo_book.py` in the real checkout: it rewrites about 200 tracked demo files. Use the throwaway copy in `/verify-phase`.
- Relying on a hook's "ask" in auto mode: auto mode settles it without showing Kieran. Use "deny" there.
- Plain `pytest -q` took 10+ minutes and sometimes lost its summary line. `python3 -m pytest -q -p no:cacheprovider --junit-xml=<scratch>/junit.xml` ran the full suite in about 3 minutes (Phase 7); read the counts from the XML.
- Waiting for tests with `until ! kill -0 $(pgrep -f "pytest -q")`: the loop's own command contains "pytest -q", so it finds itself and never ends (one ran for 2 hours in Phase 4). Run the tests in the foreground, or wait on the exact process id.
- Test-driving `approve` through a helper: the guard blocks it, correctly. Don't work around it; prove it with tests in a temporary folder and leave the live run to Kieran.
- Editing plan files with a Python or shell script whose text mentions approve/assemble: the approval guard blocks it (known false alarm, in `IDEAS.md`). Use the Edit tool, or a script that doesn't name those words.
- Asking a checker to set up a live render on the demo copy with `revise`: the guard blocks it, correctly. Prove the render path with tests instead.
- Running `bookfactory lock --help` to check its arguments: the guard blocks any command naming lock/approve, even `--help`. Read the argparse definitions in `bookfactory/cli/main.py` instead.
- An `--autonomous` step written with a shell variable (`bookfactory approve $B ...`): the guard can't read `$B`, so it blocks. Write the book id out in full.
- Test-driving a book skill against the real checkout: it writes a new book into `books/`. Clone to the scratchpad and set `PYTHONPATH` and `BOOKFACTORY_ROOT` to the clone.

---

## Goal of this block

Make Claude Code reliable for the operator's routine: **plan a phase, hand
work out to helpers, check it with proof, hand over to a fresh session**. Each
phase builds some features; the next phase uses them, so every feature is
test-driven straight after it is built.

Background research and the reasons for each choice: the audit of 2026-09-22
(summarised under "Decisions" below). Longer-term roadmap for Book Factory
itself: `docs/REVIEW-2026-09.md`.

## Rules for this block

- Work on `main` (operator confirmed 2026-09-22). Fetch remote `main` before
  changing files; push at the end of each phase and check it arrived.
- One phase open at a time. Each phase fits one sitting. The next starts only
  when this one's "Done when" is ticked.
- New ideas go in `IDEAS.md`, not into the open phase.
- Nothing is installed from outside the repository. Every file is written here.

---

Phase 1: Foundations (done, see `docs/PLAN-ARCHIVE.md`)

Phase 2: Planning and handing out work (done, see `docs/PLAN-ARCHIVE.md`)

Phase 3: Safety checks and proof (done, see `docs/PLAN-ARCHIVE.md`)

Phase 4: Render every page in one go (done, see `docs/PLAN-ARCHIVE.md`)

Phase 5: Cover build (done, see `docs/PLAN-ARCHIVE.md`)

Phase 6: Series presets (done, see `docs/PLAN-ARCHIVE.md`)

Phase 7: Batch approval (done, see `docs/PLAN-ARCHIVE.md`)

Phase 8: Page plan and specs in one file (done, see `docs/PLAN-ARCHIVE.md`)

Phase 9: One-prompt start (done, see `docs/PLAN-ARCHIVE.md`)

Phase 10: Test one picture through Higgsfield (done, see `docs/PLAN-ARCHIVE.md`)

Phase 11: Picture budget and the Higgsfield routine (done, see `docs/PLAN-ARCHIVE.md`)

Phase 12: `produce`, first slice (done, see `docs/PLAN-ARCHIVE.md`)

Phase 13: `produce` approves pages (done, see `docs/PLAN-ARCHIVE.md`)

Phase 14: Claude writes the copy (done, see `docs/PLAN-ARCHIVE.md`)

Phase 15: The guard follows the recorded policy (done 2026-09-24; Kieran asked for it after too many stops on the Golf Addict's Guide. Changed `.claude/hooks/guard-authority.py`, `tests/test_hook_guard_authority.py`, `.claude/skills/write-book/SKILL.md`, `integrations/claude/BOOK_FACTORY.md`, `integrations/claude/WORKFLOW.md`.)

Phase 16: Activity panels, typeset diagrams and sample pages (done, see `docs/PLAN-ARCHIVE.md`)

## Phase 20: A smoother `/write-book` (open)

Goal: fix what made the first real `/write-book` run (the padel book) clunky.
Kieran's own typed go-ahead lets his decisions run in auto mode, so he never
switches modes; `/write-book` asks once how often to check in, handles the
reference set and the cover itself, and Book Factory catches the two faults
that slipped through (text running over the page number, an out-of-date
interior after a revision). Kieran asked for all of it 2026-09-26 ("Make all
changes, /fan-out responsibilities").

| # | Task | Who | Files |
|---|---|---|---|
| 20.1 | Go-ahead slip: a UserPromptSubmit hook records Kieran's typed words; the guard allows exactly the matching operator command signed `--by kieran` in any mode, for that turn only; Claude can never write the slip. Also fix two false alarms (a shell loop variable, a working folder inside `approved/`) | builder, tricky (Opus: a safety hook, must never let Claude grant itself authority) | `.claude/hooks/record-go-ahead.py`, `.claude/hooks/guard-authority.py`, `.claude/settings.json`, `.gitignore`, `tests/test_hook_go_ahead.py`, `tests/test_hook_guard_authority.py` |
| 20.2 ✓ | `produce` gives `picture` for drawn visual references too (not typeset samples, not the cover); book ids drop apostrophes and a leading "the" | builder, routine (Sonnet) | `bookfactory/core/produce.py`, `bookfactory/core/ids.py`, `tests/test_produce_picture.py`, `tests/test_ids_slug.py` |
| 20.3 ✓ | A revised page makes the assembled interior and its preflight stale: `status` says so and `next` asks for assembly again | builder, routine (Sonnet) | `bookfactory/core/book.py`, `bookfactory/core/gates.py`, `bookfactory/core/tasks.py`, `bookfactory/core/cover.py`, `tests/test_stale_interior.py` |
| 20.4 ✓ | The fit test and QA flag body text that runs into the bottom margin or over the page number | builder, routine (Sonnet) | `bookfactory/render/fit.py`, `bookfactory/qa/technical.py`, `tests/test_plan_fit.py`, `tests/test_qa_bottom_margin.py` |
| 20.5 ✓ | Cover fonts ship with Book Factory (no copying from Golf) and a big-lettering cover starts with a ready design block | builder, routine (Sonnet) | `bookfactory/render/cover.py`, `bookfactory/render/assets/fonts/*`, `bookfactory/core/api.py`, `tests/test_cover_design_defaults.py` |
| 20.6 | `/write-book` and the guides: one check-in choice at the start, the reference set end to end, the cover step, the go-ahead slip, no shell variables | docs keeper, routine (Sonnet), after 20.1 to 20.5 | `.claude/skills/write-book/SKILL.md`, `AGENTS.md`, `integrations/claude/BOOK_FACTORY.md`, `integrations/claude/WORKFLOW.md`, `docs/OPERATOR.md`, `GLOSSARY.md` |
| 20.7 | Check: full suite, demo build in a throwaway copy, docs vs code, guard safety review; then test-drive in a scratch copy of the padel book | checker (Sonnet), then main | `PLAN.md`, `IDEAS.md` |

**Test-drive:** 20.7, in a scratch copy of the padel book: the go-ahead slip lets a typed "lock the look" through and nothing else; reopening a page marks the interior stale; the old padel openers are flagged by the margin check.

**Done when:**
- [ ] In auto mode, typing "approve cover v1" (or "lock the look", "revise p014") lets exactly that command through, signed with Kieran's name, without switching modes; nothing Claude writes can do the same.
- [ ] `/write-book` asks once how often to check in, then draws and shows the six reference pictures together, and writes the cover for Kieran to approve.
- [ ] Text running over a page number, and an out-of-date interior after a revision, are both caught automatically.
- [ ] `pytest` passes, `scripts/build_demo_book.py` passes in a throwaway copy, and everything is pushed to `main` and checked there.

## Phase 17: Page plan straight from the manuscript (done)

Goal: one command reads a locked manuscript and writes the whole page plan
(openers, text pages, activity pages built from blocks), fit-tests every page
in both engines and splits text pages that overflow. The Golf plan needed a
one-off scratch script. The command writes a plan file only; loading it into a
book stays `plan --from-file`. Planned and agreed with Kieran 2026-09-24.

| # | Task | Who | Files |
|---|---|---|---|
| 17.1 ✓ | Parse the manuscript into plan pages: front matter, stage openers, text pages, `No. NN · Kind: Title` activities with their blocks (ticks, checklist, table, score, case note, cut-out, gauge) | builder, tricky (Opus: many block kinds must match the renderer's schema) | `bookfactory/core/manuscript_plan.py`, `tests/test_manuscript_plan.py` |
| 17.2 ✓ | Fit test: render each planned page in both engines; split an overflowing text page at a paragraph break; name an activity page that won't fit | builder, routine (Sonnet) | `bookfactory/render/fit.py`, `tests/test_plan_fit.py` |
| 17.3 ✓ | `bookfactory plan <book> --from-manuscript --out <plan.json>`: writes the plan file and a fit report, changes nothing in the book | main (small once 17.1 and 17.2 were in) | `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `tests/test_cli_plan_from_manuscript.py` |
| 17.4 ✓ | Document the manuscript layout the command reads; `/write-book` uses it for the page plan | docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/claude/BOOK_FACTORY.md`, `.claude/skills/write-book/SKILL.md`, `GLOSSARY.md` |
| 17.5 ✓ | Check: full suite, demo build in a throwaway copy | checker, routine (Sonnet) | none |
| 17.6 ✓ | Test-drive on a copy of the Golf book: compare with its real 71-page plan | main | `PLAN.md` |

**Test-drive:** 17.6 runs the command on a scratch clone of the Golf Addict's Guide and compares its output with the real plan, page for page.

**Done when:**
- [x] One command turns the Golf manuscript into a page plan that matches the real one page for page, with any differences listed and explained. (71 pages each; same types and order; split pages match word for word. Differences: the three split-off pages are titled "(continued)" not "(introduction)", and "About this programme" is back matter with no chapter, not chapter 8.)
- [x] Every page in that plan fits on its page in both engines, or the command names the ones that don't. (Golf: 68 fit, 3 openers split, none too long. The test-drive found that a one-paragraph opener could not be split; fixed so an opener can hand its only paragraph on, as Golf's Stage Seven and Eight did; test added.)
- [x] `pytest` passes, and `scripts/build_demo_book.py` passes in a throwaway copy.
- [x] Everything is pushed to `main` and checked there.

## Phase 19: Pictures in the loop, and the last steps on their own (done)

Goal: `/write-book` carries a book through its pictures and its final release
steps without stopping, whenever the recorded production policy allows. Part A:
`produce` stops with a new `picture` code at a page picture it can't draw;
`/write-book` then draws it through Higgsfield (the routine in
`integrations/claude/BOOK_FACTORY.md`), checks it against the references,
submits it, and approves a page picture with `--autonomous` only when the task's
mode is continue_automatically; cover artwork and the full-wrap cover stay
Kieran's. Part B: the guard lets `advance --to release_ready`, `cover finalize`
and `cover preflight` through when the book's next task asks for exactly that
command and its mode is continue_automatically. Kieran asked for both
2026-09-26 ("Start both").

| # | Task | Who | Files |
|---|---|---|---|
| 19.1 ✓ | `produce` stops with `picture` at a page-picture task in continue_automatically (not cover artwork) | builder, routine (Sonnet) | `bookfactory/core/produce.py`, `tests/test_produce_picture.py` |
| 19.2 ✓ | Guard: allow `advance --to release_ready`, `cover finalize`, `cover preflight` when the next task names that command in continue_automatically; ask otherwise | builder, tricky (Opus: a safety hook, must never widen past the policy) | `.claude/hooks/guard-authority.py`, `tests/test_hook_guard_authority.py` |
| 19.3 ✓ | `/write-book`: the picture loop (budget, Higgsfield, own check, submit, `--autonomous` page-picture approval, credits report) and the release steps | docs keeper, routine (Sonnet) | `.claude/skills/write-book/SKILL.md` |
| 19.4 ✓ | Rules and guides for both parts | docs keeper, routine (Sonnet) | `AGENTS.md`, `integrations/claude/BOOK_FACTORY.md`, `integrations/claude/WORKFLOW.md`, `docs/OPERATOR.md`, `GLOSSARY.md` |
| 19.5 ✓ | Check: full suite, demo build in a throwaway copy, docs vs code, guard decisions | checker, routine (Sonnet) | none |
| 19.6 ✓ | Test-drive in a scratch copy: `produce` stops with `picture`; the guard allows the three end steps only when the task asks | main | `PLAN.md`, `IDEAS.md` |

**Test-drive:** 19.6, in a scratch copy. The first live Higgsfield picture inside the loop is on the next real book (it spends Kieran's credits).

**Done when:**
- [x] `produce` says "picture" when the next job is a page picture, and `/write-book` knows how to draw, check, submit and (only when the policy allows) approve it, never the cover.
- [x] In auto mode, a book whose policy allows it goes through `cover finalize`, `cover preflight` and release ready without stopping; anything else still asks.
- [x] `pytest` passes, `scripts/build_demo_book.py` passes in a throwaway copy, and everything is pushed to `main` and checked there.

## Phase 18: Big decisions at intake (done)

Goal: starting a book also asks the exact title, the main character's age,
family and look, colour or black-and-white printing, and the cover style (big
lettering, picture, or let Book Factory decide); confirming intake sets the
book up from those answers, audited, and the writing tasks show them as fixed.
From the Golf Addict's Guide retrospective (late changes to Dave's age, the
cover style and black and white cost rework and credits). Planned and agreed
with Kieran 2026-09-26; he asked for every task at once.

| # | Task | Who | Files |
|---|---|---|---|
| 18.1 ✓ | Four new questions (`title`, `main_character_details`, `print_colour`, `cover_style`) with validation and drafting | builder, routine (Sonnet) | `bookfactory/core/intake.py`, `tests/test_intake_draft.py`, `tests/test_autonomous.py`, `tests/test_intake_questions.py` |
| 18.2 ✓ | Confirming intake applies them: title, `format.colour`, text-only cover for `big_lettering`, each audited | builder, routine (Sonnet) | `bookfactory/core/api.py`, `tests/test_intake_apply.py` |
| 18.3 ✓ | Writing tasks (brief, character and visual references, visual bible, cover) list the decisions as fixed at intake | builder, routine (Sonnet) | `bookfactory/core/tasks.py`, `tests/test_tasks_intake_decisions.py` |
| 18.4 ✓ | Guides and `/write-book` | docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/AUTONOMOUS_PRODUCTION.md`, `.claude/skills/write-book/SKILL.md`, `GLOSSARY.md` |
| 18.5 ✓ | Check: full suite, demo build in a throwaway copy, docs vs code | checker, routine (Sonnet) | none |
| 18.6 ✓ | Test-drive: a test book in a scratch copy, intake drafted and confirmed; title, printing and cover set with no hand edits | main | `PLAN.md`, `IDEAS.md` |

**Test-drive:** 18.6 starts a book from an idea in a scratch copy, drafts intake with the new questions marked unclear, confirms them, then reads `book.json`, `cover/cover.json`, the audit log and the brief task.

**Done when:**
- [x] Starting a new book asks the four new questions along with the others.
- [x] After confirming, the book already has the right title, colour or black-and-white printing and cover type, all in the audit log, with no hand edits.
- [x] The writing steps show those decisions, so the brief, character and cover follow them.
- [x] `pytest` passes, `scripts/build_demo_book.py` passes in a throwaway copy, and everything is pushed to `main` and checked there.

---


## Decisions (from the 2026-09-22 audit)

- **Rules stay in `AGENTS.md`** (shared with ChatGPT). `CLAUDE.md` imports it
  and adds only Claude-specific material.
- **Parallel helpers are for improving Book Factory itself, never for
  producing a book.** A book's tasks stay one at a time (`AGENTS.md` §2).
- **Helpers never commit or push.** The main session commits each checked task
  naming its exact files (no `git add -A`), and pushes once per phase.
- **No file is edited by two helpers in the same phase.** `/plan-phase` assigns
  every file to one task; shared docs belong to the docs keeper; the CLI file
  `bookfactory/cli/main.py` is changed by one task at a time.
- **Not used, on purpose:** git worktrees and `isolation: worktree` (clash with
  working on `main`); agent teams (experimental, and they turn helpers into
  teammates); outside plugins such as Superpowers, everything-claude-code and
  pro-workflow (their mandatory branches, TDD and always-on hooks clash with
  `AGENTS.md`; their best ideas are written into our own commands instead).
- **Command names avoid Claude's built-ins** (`/verify`, `/batch`,
  `/code-review`, `/simplify`). Don't use `/batch` here: it works in worktrees.
- **Everything lives in the repository**, not in `~/.claude/`, because web
  sessions start in a fresh container each time.
- **Helpers cost usage.** Each one is a separate Claude worker that reads the
  rules before starting. Fan out only when it saves real time, run every
  task whose files don't overlap at once (Kieran lifted the old limit of 3 on
  2026-09-26: "do as much as possible"), and use the cheaper model for routine jobs (task 2.7, added
  2026-09-22 at the operator's request).

## Verification log

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-24 | 15 | Full suite (junit) | 510 passed, 2 skipped, 0 failed |
| 2026-09-24 | 17 | Checker: scope, full suite (junit), demo build in throwaway copy, docs vs code, placeholder can't leak | 579 passed, 2 skipped, 0 failed; demo Release Ready; no mismatches |
| 2026-09-24 | 17 | Test-drive: `plan --from-manuscript` on a scratch copy of the Golf book, compared with its real plan | 71 = 71 pages, all fit (3 openers split), split bodies identical; opener one-paragraph fix and its test added after the checker ran, `tests/test_plan_fit.py` 8 passed |
| 2026-09-26 | 18 | Checker: scope, full suite (junit), demo build in throwaway copy, docs vs code, old books unaffected | 603 tests: 600 passed, 2 skipped, 1 failed (a Phase 17 Golf test made stale by the p055/p061 fix, not Phase 18; fixed, rerun passes); demo Release Ready; question order in AUTONOMOUS_PRODUCTION.md was wrong, fixed; Golf status/validate/task clean |
| 2026-09-26 | 18 | Test-drive: book from an idea in a scratch copy, intake drafted with the four new questions unclear, confirmed with --set | title set exactly, black and white, cover artwork none by kieran, three audit entries; the brief task lists all four as fixed at intake |
| 2026-09-26 | 19 | Checker: scope, full suite (junit), demo build in throwaway copy, docs vs code, guard safety review | 671 passed, 2 skipped, 0 failed; demo Release Ready; no mismatches; no new way past the guard |
| 2026-09-27 | 20 | Checkers on 20.2-20.5 (scope, named tests, real books read-only) and a full suite with all four in | 20.3 needed a fix (13 older cover tests assumed no assembly record; fixed so a missing record behaves as before) and a preflight-staleness addition; 20.5 needed measured title sizing (a long wide title overran); then full suite 788 passed, 2 skipped, 0 failed. Margin check found Golf p005, p013, p023, p031, p038, p045 print over the folio |
| 2026-09-27 | 20 | Safety review of 20.1 (Opus) | Failed round 1 (loose wording, chained commands allowed, helpers shared it, slip file forgeable); reworked to read the transcript; 3 small fixes left because the new self-lock blocked the builder; saved on branch `phase-20-go-ahead` |
| 2026-09-26 | 19 | Test-drive: guard decisions on a scratch copy of the finished Golf book; the picture stop via tests (reopening a Golf picture needs Kieran, correctly blocked) | cover preflight / advance / `cover --root X finalize` all ask (not the next task); `status` allowed; `produce` gives `picture` in tests |
