# PLAN

The current block of work on **Book Factory itself** (its code, rules and
Claude Code setup). This is not a book's production plan: a book's state lives
in `books/<id>/` and is read with `bookfactory status` / `next`.

Only the main session edits this file. Helpers report back; they never write
here.

---

## Start here

> **Doing:** Phase 21, the look of the CRM (a mockup to agree before building). Phases 17-20 are done and archived in `docs/PLAN-ARCHIVE.md`.
> **Finished (2026-09-27, covers and KDP):** Amazon cover research (categories: Humor > Sports, Humor > Parodies, the sport's own category; covers with a big title, one family scene and a gift line). Kieran let Claude draw and submit cover artwork through Higgsfield, with approval staying his (`integrations/claude/BOOK_FACTORY.md` "Cover artwork", `/write-book` section 3e). Golf and Padel switched to artwork covers (Kieran's words, audited): Golf cover v4 reuses the unused Sunday-roast picture (0 credits); Padel cover v2 has a new breakfast scene of Josh explaining the scoring (2 credits, 6 left). Both approved by Kieran, cover preflight passes, both Release Ready. New top-level `KDP/` folder: per book `cover.pdf`, `interior.pdf` (copies, checksums in the sheet) and `UPLOAD.md` (every KDP form field); the Runner's Guide sheet moved in.
> **Next action:** Kieran uploads Golf and Padel to KDP from `KDP/<book>/UPLOAD.md` (order a printed proof first); otherwise start the next real book with `/write-book`, or plan Phase 21 from `IDEAS.md` (a `kdp pack` command is a good candidate).

**Unfinished, carried over:**
- `KDP/` is filled by hand: if a Golf, Padel or Runner's cover or page changes, its `KDP/<book>/` copies and checksums must be refreshed (idea for a command in `IDEAS.md`).
- The local-only branch `backup-stale-local-main` (an old copy of `main` from this container's clone, no new work) vanishes with the container; nothing to merge.
- none else (the first live runs of `approve --all-passing`, of `produce` page approvals and of `/write-book` are Kieran's, on a real book; helpers are rightly blocked from the first two)

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
- `git reset --hard` in auto mode: the auto-mode safety check blocks it as destructive. To match remote `main`, keep a backup branch first, then `git checkout -B main origin/main`.
- Editing Claude's own rule files to loosen a limit in auto mode: blocked as "Self-Modification" even with Kieran's go-ahead. Stop, tell Kieran, and let him decide; after he typed "save the rule change" it went through.
- Signing `--by kieran` from a vague reply ("let's do it!", "these are good"): blocked. Ask Kieran to type the exact decision ("Switch the golf and padel covers to artwork", "Approve golf cover v4").
- Piping `bookfactory cover build --json` into `json.load`: a PyMuPDF deprecation warning is printed first, so the JSON doesn't parse. Use `grep` on the output, or read the files it names.

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

Phase 17: Page plan straight from the manuscript (done, see `docs/PLAN-ARCHIVE.md`)

Phase 18: Big decisions at intake (done, see `docs/PLAN-ARCHIVE.md`)

Phase 19: Pictures in the loop, and the last steps on their own (done, see `docs/PLAN-ARCHIVE.md`)

Phase 20: A smoother `/write-book` (done, see `docs/PLAN-ARCHIVE.md`)

## Phase 21: The look of the CRM (in progress)

Goal: agree exactly how the Book Factory CRM looks (books, KDP sales, ideas
board), on phone and laptop, before any real building starts. Kieran asked for
it 2026-09-27; it will be a hosted site he opens on his phone and his laptop.
Later phases (data, the real app, putting it online) are planned once the look
is agreed. Everything for the CRM lives in `crm/`.

| # | Task | Who | Files |
|---|---|---|---|
| 21.1 ✓ | Design brief and design tokens: colours, two fonts, spacing, rounding, animation speed; starting from the books' own look (paper cream, ink black, one accent) | main | `crm/design/BRIEF.md`, `crm/design/tokens.json` |
| 21.2 ✓ | Front-cover pictures of the three books for the mockup, taken from the approved cover PDFs (read only) | main | `crm/mockup/covers/*.jpg` |
| 21.3 ✓ | Clickable mockup: Home, Shelf, Sales (sample figures, labelled), Ideas board; laptop and phone layouts, light and dark | main | `crm/mockup/index.html` |
| 21.4 | Publish it as a private page; up to two rounds of changes from Kieran's comments | main | `crm/mockup/index.html` |
| 21.5 | Update `PLAN.md`, save to `main` | main | `PLAN.md`, `IDEAS.md` |

**Test-drive:** Kieran opens the mockup on his phone and laptop and clicks through all four screens.

**Done when:**
- [ ] Kieran can open the mockup on his phone and his laptop (published 2026-09-27: https://claude.ai/artifact/7cT2qafLBNQeUKLHJgGgbg, version 1).
- [ ] All four screens are there, with the three real books and covers.
- [ ] Kieran has said "that's the look".

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
| 2026-09-27 | none | Golf cover v4 and Padel cover v2: cover build checks, previews at print and thumbnail size, cover preflight, validate | no build problems; both cover preflights pass; both books validate and are Release Ready; KDP copies match the approved checksums |
