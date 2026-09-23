# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 10 (test one picture through Higgsfield). The test ran and is written up under Phase 10's findings; waiting for Kieran's verdict on the picture.
> **Finished:** Phases 8 and 9 this session; Higgsfield connected and one test picture made, submitted and checked in a throwaway copy (2 credits; 68 left).
> **Next action:** get Kieran's verdict on the test picture, then either try one more picture with a tighter prompt, or plan the phase that writes the Higgsfield routine into the rules (docs keeper: `integrations/claude/BOOK_FACTORY.md` "Images").

**Unfinished, carried over:**
- none (the first live run of `approve --all-passing` is Kieran's, on a real book; helpers are rightly blocked from it)

**Don't try again:**
- `git rev-parse --short HEAD origin/main` fails ("Needed a single revision"): run `git rev-parse --short` once per ref.
- Testing a new hook in the same session that created `.claude/settings.json`: hooks load only when a session starts, so the trial does nothing. Permission deny rules do work straight away. (Edits to an already-registered hook script do take effect at once.)
- Running `scripts/build_demo_book.py` in the real checkout: it rewrites about 200 tracked demo files. Use the throwaway copy in `/verify-phase`.
- Relying on a hook's "ask" in auto mode: auto mode settles it without showing Kieran. Use "deny" there.
- Plain `pytest -q` took 10+ minutes and sometimes lost its summary line. `python3 -m pytest -q -p no:cacheprovider --junit-xml=<scratch>/junit.xml` ran the full suite in about 3 minutes (Phase 7); read the counts from the XML.
- Waiting for tests with `until ! kill -0 $(pgrep -f "pytest -q")`: the loop's own command contains "pytest -q", so it finds itself and never ends (one ran for 2 hours in Phase 4). Run the tests in the foreground, or wait on the exact process id.
- Test-driving `approve` through a helper: the guard blocks it, correctly. Don't work around it; prove it with tests in a temporary folder and leave the live run to Kieran.

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

## Phase 10: Test one picture through Higgsfield (in progress)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #4 and the
`IDEAS.md` line on the Higgsfield connector (MCP, paid from Kieran's plan
credits: 70 at the start; a 4K picture costs 4). A test only: nothing is
changed in any real book, and no rule changes until Kieran has judged the
picture.

**How:** in a throwaway copy of the repository, give the runner book one test
page whose spec names a test illustration (registered automatically, Phase
8). Take the illustration task Book Factory then issues, send its approved
reference pictures to Higgsfield, generate one picture (Nano Banana Pro,
4K), bring the file back and submit it as a draft, so Book Factory's measured
checks (size, readable image) judge it. Show Kieran the picture beside the
references.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 10.1 | Throwaway test: task, references to Higgsfield, one picture, download, submit, measured checks | main | none in the repository (throwaway copy; picture kept in the scratchpad for Kieran) | [x] |
| 10.2 | Record what worked, what didn't, the cost, and the routine to write into the rules if Kieran is happy | main | `PLAN.md`, `IDEAS.md` | [ ] |

**Findings (2026-09-23 test):**
- The whole route works from this cloud session: a test page planned with
  its spec registered its artwork by itself (Phase 8); `task` issued the
  illustration task with 3 approved references; the references were uploaded
  to Higgsfield (`media_upload`, then `curl` PUT from here, then
  `media_confirm`); `generate_image` made the picture; `curl` downloaded it;
  `submit` accepted it as draft v1 and its measured checks passed (1792x2400,
  needs 1530 wide). The next task became the operator's review, as it should.
- **Plan limit:** Nano Banana Pro at 4K is refused on the basic plan
  ("Requires plus plan or higher"). 2K works: 2 credits, and a portrait 3:4
  picture comes out 1792 wide, enough for a 6x9 book's full page. The job
  reported running as `nano_banana_2`, not `nano_banana_pro`. Credits: 70
  before, 68 after. Each picture took about 2 minutes.
- **Quality (Claude's review, for Kieran to judge):** Alex and Sam clearly
  match their references and the ink-and-grey style is close; the joke reads;
  no text. But a **brand logo appeared on Alex's shorts** (banned by the
  visual bible), there are **two kettles**, the background is busier than the
  reference and the paper slightly pinker. As submitted it would need a
  revision. A prompt that explicitly says "plain unbranded shorts, one
  kettle, sparse background" is the obvious next try.
- Rule 6 still holds: an operator (or an agent under `autonomous`) must
  judge the match; the measured checks cannot see a logo.

**Done when:**
- [x] One picture made through Higgsfield from a real Book Factory task, with the book's approved references, has been submitted as a draft in a throwaway copy, and its measured checks are reported.
- [ ] Kieran has seen it beside the references, and the findings and cost are written down.
- [ ] Everything is saved to GitHub `main` and checked there.

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
  rules before starting. Fan out only when it saves real time, keep it to 3 at
  once, and use the cheaper model for routine jobs (task 2.7, added
  2026-09-22 at the operator's request).

## Verification log

| Date | Phase | Check | Result |
|---|---|---|---|
