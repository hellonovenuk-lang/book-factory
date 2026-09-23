# PLAN archive

Finished phases from `PLAN.md`, with their verification logs. Newest last.

---

## Phase 1: Foundations (done)

Built directly by the main session, no helpers yet.

| # | Task | Files | Status |
|---|---|---|---|
| 1.1 | Load the rules for real: `@`-import `AGENTS.md` and `integrations/claude/BOOK_FACTORY.md` (and this file) from `CLAUDE.md`; update the "exists only to point" line | `CLAUDE.md` | [x] |
| 1.2 | "Working with Kieran" section: plain English, terms explained, recommendation first, one question at a time, every reply ends with "Your next step" | `CLAUDE.md` | [x] |
| 1.3 | Ideas parking lot | `IDEAS.md` | [x] |
| 1.4 | Glossary, seeded with the terms used so far | `GLOSSARY.md` | [x] |
| 1.5 | `/handover` command: updates "Start here", ticks tasks, saves, sends to GitHub, checks it arrived | `.claude/skills/handover/SKILL.md` | [x] |
| 1.6 | Keep personal settings files out of GitHub | `.gitignore` | [x] |

**Test-drive:** run `/handover`, open a fresh session, say only "continue".

**Done when:**
- [x] The fresh session says where we are and what is next without being told.
- [x] All Phase 1 files are on GitHub's `main`.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-22 | 1 | `@` imports in `CLAUDE.md` point at existing files | all 3 found |
| 2026-09-22 | 1 | `/handover` settings header is valid | parsed OK |
| 2026-09-22 | 1 | Only the intended files changed; personal settings are git-ignored | confirmed with `git status`, `git check-ignore` |
| 2026-09-22 | 1 | Phase 1 commits are on GitHub `main` | local and remote both at `0ebf942` |
| 2026-09-22 | 1 | `/handover` runs as a command in the session that created it | worked |
| 2026-09-22 | 1 | Fresh session told only "continue" explains where we are | passed; operator confirmed the summary |

---

## Phase 2: Planning and handing out work (done)

| # | Task | Files | Status |
|---|---|---|---|
| 2.1 | `/plan-phase`: turns an idea into a small phase; maps which files each task touches *before* any work is handed out; plain-words "Done when" | `.claude/skills/plan-phase/` | [x] |
| 2.2 | `/fan-out` plus the standard brief (read first / files you may touch / parts / done when / decisions you made on your own); hands out only tasks whose files don't overlap | `.claude/skills/fan-out/` | [x] |
| 2.3 | Helper *builder*: edits only the files its brief names; never commits, pushes, approves or locks | `.claude/agents/implementer.md` | [x] |
| 2.4 | Helper *checker*: cannot edit; runs the checks and reports evidence | `.claude/agents/verifier.md` | [x] |
| 2.5 | Helper *docs keeper*: the only helper that edits `AGENTS.md`, `docs/OPERATOR.md`, `integrations/*` | `.claude/agents/docs-sync.md` | [x] |
| 2.6 | One-page guide, with the cheat sheet near the top of `CLAUDE.md` | `integrations/claude/WORKFLOW.md`, `CLAUDE.md` | [x] |
| 2.7 | Usage rules for helpers: at most 3 at once; small jobs done by the main session instead; helpers on Sonnet by default, Opus only when the brief says the job is tricky; a turn limit (`maxTurns`) on every helper; `/fan-out` shows a one-line preview (how many helpers, which model, rough size) and waits for the operator's OK; finished phases moved out of `PLAN.md` (it loads into every session and helper, about 7,000 tokens of rules already); checker reports in plain English | `.claude/skills/fan-out/`, `.claude/agents/*.md`, `.claude/skills/handover/SKILL.md`, `integrations/claude/WORKFLOW.md` | [x] |

**Test-drive:** use `/plan-phase` to plan Phase 3.

**Done when:**
- [x] Phase 3's plan is written here and the operator understands every line of it.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-22 | 2 | Header of every new command and helper file is valid | all 6 parsed OK |
| 2026-09-22 | 2 | Every file the new guides point to exists | none missing |
| 2026-09-22 | 2 | `/plan-phase` test-drive: Phase 3 planned with the operator | operator said OK to every line |

---

## Phase 3: Safety checks and proof (done)

Planned with `/plan-phase` on 2026-09-22; operator agreed every line.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 3.1 | `/verify-phase`: proves every "Done when" item with fresh command output. Runs `scripts/build_demo_book.py` on a throwaway copy of the repository, because it rewrites about 200 tracked demo files | main | `.claude/skills/verify-phase/SKILL.md` | [x] |
| 3.2 | Approval guard hook: before any Bash command, asks the operator if it runs `bookfactory approve / lock / policy set / reject / revise / cover approve / cover finalize / advance --force` (including disguised forms such as `python -m bookfactory ...` or chained commands); blocks Bash writes into `approved/` folders and the approved cover | helper: builder, **tricky (Opus)**: must catch disguised commands; a gap is a real risk | `.claude/hooks/guard-authority.py`, `tests/test_hook_guard_authority.py` | [x] |
| 3.3 | Quick-check hook: after a `.py` or `.json` file is saved, checks it still parses | helper: builder, routine (Sonnet) | `.claude/hooks/quick-check.py`, `tests/test_hook_quick_check.py` | [x] |
| 3.4 | Session-start hook: in web sessions installs what the tests need (`pip install -e ".[dev]"`); always warns if not on `main`; shows "Start here" | helper: builder, routine (Sonnet) | `.claude/hooks/session-start.sh` | [x] |
| 3.5 | Settings: switches on the three hooks; forbids editing approved pages, assets and the approved cover; pre-approves safe read-only commands. The only task that edits the settings file, done after 3.2-3.4 | main | `.claude/settings.json` | [x] |
| 3.6 | Add the safety checks to the guide and glossary | main | `integrations/claude/WORKFLOW.md`, `GLOSSARY.md` | [x] |

**Order:** round 1: helpers on 3.2, 3.3, 3.4 while the main session writes
3.1. Round 2: main session does 3.5 and 3.6, then the checker checks
everything.

**Note:** "Nothing is installed from outside the repository" (rules above)
means Claude plugins and add-ons. The Python packages Book Factory's own
tests need (listed in `pyproject.toml`) are fine to install.

**Test-drive:** built with `/fan-out`, checked with `/verify-phase`, closed
with `/handover`.

**Done when:**
- [x] The checker shows all tests passing.
- [x] A pretend "approve" is stopped and handed to the operator. (Live trial 2026-09-23: in auto mode the guard's "ask" was settled without reaching the operator, so the guard now blocks outside the default permission mode; the retried trial was blocked.)
- [x] A pretend write into an approved folder is blocked.
- [x] `/verify-phase` proves those three with fresh results.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-22 | 3 | Baseline before Phase 3 | 225 passed, 2 skipped |
| 2026-09-22 | 3 | Main session's own 13 test commands against the guard | all correct (ask / deny / allow) |
| 2026-09-22 | 3 | Live: Write into an approved folder | refused by the settings file's deny rule |
| 2026-09-22 | 3 | Live: pretend approve in the session that created the hooks | not stopped (hooks load at session start); book didn't exist, nothing changed |
| 2026-09-22 | 3 | Checker, following `/verify-phase` | passed: 370 passed, 2 skipped; guard asks on approve, denies approved write; demo build OK on a throwaway copy; only the 9 planned files changed |
| 2026-09-23 | 3 | Live: pretend approve in a fresh session (auto mode) | not stopped: guard said "ask" but auto mode let it run; book didn't exist, nothing changed |
| 2026-09-23 | 3 | Guard changed: asks become blocks outside the default permission mode | guard tests pass; full suite 378 passed, 2 skipped |
| 2026-09-23 | 3 | Live: same pretend approve, retried | blocked, with the reason telling Claude to ask Kieran in the chat |

---

## Phase 4: Render every page in one go (done)

Planned 2026-09-23 with Kieran; the first real job for the routine, from
`docs/REVIEW-2026-09.md` item #2. `bookfactory render <book> --submit`
without `--page` already renders and submits every page, but it stops at the
first approved page, at the first page with no spec, and at the first page
that fails to render. This phase makes it safe to run on a real book.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 4.1 | Whole-book render: with `--submit`, skips approved pages (unless a revision is open); always skips pages with no spec; carries on past a page that fails; reports rendered / skipped / failed with reasons; the command exits non-zero if any page failed. Tests for each case | helper: builder, routine (Sonnet) | `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `tests/test_render.py` | [x] |
| 4.2 | Operator guide explains rendering the whole book and what is skipped | helper: docs keeper, routine (Sonnet) | `docs/OPERATOR.md` | [x] |
| 4.3 | Mark review item #2 as partly done | main | `docs/REVIEW-2026-09.md` | [x] |
| 4.4 | Check everything with proof (`/verify-phase`) | helper: checker | none (read-only) | [x] |

**Order:** round 1: 4.1 and 4.2 together while the main session does 4.3.
Then the checker checks everything.

**Test-drive:** on a throwaway copy of the demo book, approve one page, break
another, run `render --submit` on the whole book and read what it reports.

**Done when:**
- [x] One command renders and submits every page that is ready, and approved pages are never touched.
- [x] A broken page is listed as failed, and the other pages still get done.
- [x] `pytest` passes and the demo build passes.
- [x] Everything is saved to GitHub `main` and checked there.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 4 | Checker: only the 3 files of task 4.1 uncommitted | confirmed |
| 2026-09-23 | 4 | Checker: full `pytest` | 383 passed, 2 skipped (baseline 378 + 5 new) |
| 2026-09-23 | 4 | Checker: demo build on a throwaway copy | finished, Release Ready, 24 pages |
| 2026-09-23 | 4 | Test-drive: whole-book `render --submit` on the built demo book, one spec broken | all 24 pages skipped as approved, exit 0; approved PDFs' sha256 unchanged |
| 2026-09-23 | 4 | Broken page fails, rest carry on (demo book had no unapproved page, so by tests) | 5 new tests in `tests/test_render.py` pass |

---

## Phase 5: Cover build (done)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #5. Today
each cover is typeset by a one-off script (the running book has three:
`build_cover_v1.py`, `_text_v2.py`, `_v3.py`; the demo script has its own).
`bookfactory cover build <book>` does it from `cover/cover.json` in seconds,
the same way every time.

**The command:** `bookfactory cover build <book> [--submit]`. Reads title
(the book's), optional `subtitle`, `author`, `back_copy`, optional
`spine_text` (set only when KDP allows it, else left off and reported) and an
optional `design` block (`background`, `ink`, `accent` colours;
`title_font`, `body_font` font files inside the book). Places the approved
(or latest reviewable) `cover-front-artwork` on the front, or none for a
text-only cover. Keeps the barcode area clear. Writes
`output/cover-build/cover-wrap.pdf` plus a full-wrap preview PNG and a
front thumbnail PNG (regenerable, not tracked), runs the cover checks, and
with `--submit` registers a new cover draft only if they pass. It never
approves.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 5.1 | `cover build` with template, previews, checks, `--submit`, schema fields, the cover-layout task pointing to it, and tests | helper: builder, routine (Sonnet) | `bookfactory/render/cover.py` (new), `templates/cover/wrap.html.j2` (new), `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `bookfactory/core/tasks.py`, `schemas/cover.schema.json`, `tests/test_cover_build.py` (new) | [x] |
| 5.2 | Demo script uses `cover build` instead of its own typesetting | main, after 5.1 | `scripts/build_demo_book.py` | [x] |
| 5.3 | Rules and guides say covers are built with `cover build` | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/*` | [x] |
| 5.4 | Mark review item #5 done | main | `docs/REVIEW-2026-09.md` | [x] |
| 5.5 | Check everything with proof, and test-drive on a throwaway copy of the running book | helper: checker | none (read-only) | [x] |

**Notes:** the 5.1 builder hit its 40-turn limit, most likely waiting on the
slow full test run; its work was complete and its 8 tests passed. Main then
found that WeasyPrint ignores CSS `writing-mode`, so spine text came out
horizontal across both covers. Fixed by rotating it, sized from the spine
width, with a test that renders real spine text. Main also tightened the
AGENTS.md 9a wording so both previews must be looked at.

**Order:** round 1: 5.1 and 5.3 together; main does 5.4. Round 2: main
does 5.2, then the checker.

**Test-drive:** on a throwaway copy, build the running book's cover from its
`cover.json` and look at the preview and thumbnail.

**Done when:**
- [x] One command builds a full-wrap cover PDF and previews from `cover.json`, and it passes Book Factory's own cover checks.
- [x] With `--submit` it becomes a new cover draft; it never approves.
- [x] `pytest` passes and the demo build (now using `cover build`) passes.
- [x] Everything is saved to GitHub `main` and checked there.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 5 | Main: WeasyPrint spine test | `writing-mode` ignored (text horizontal, 1.7in wide); rotation keeps it vertical inside the spine |
| 2026-09-23 | 5 | Checker: only the phase's 12 files changed | confirmed |
| 2026-09-23 | 5 | Checker: full `pytest` | 392 passed, 2 skipped (383 + 9 new) |
| 2026-09-23 | 5 | Checker: demo build on a throwaway copy, now via `cover build --submit` | Release Ready; cover draft v1 built and submitted, cover preflight pass |
| 2026-09-23 | 5 | Test-drive: `cover build` on a throwaway copy of the running book | no problems; previews legible, artwork clear, nothing crosses the spine |

---

## Phase 6: Series presets (done)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #6. Book 2
of a series should start from book 1's locked look and voice instead of
redoing visual development, the slowest creative stage.

**The command:** `bookfactory create "<title>" --policy <policy> --series-from
<source-book>` (other `create` options as usual). The source must have its
voice and visual style locked. It copies into the new book: the voice bible
and writing sample, the visual bible, design tokens and reference set, and
the cover `design` block with any font files it names. Each required
reference's **approved** file from the source is registered and submitted in
the new book as a **draft** recording where it came from (source book,
revision, sha256). Nothing is approved or locked: the new book's own policy
and `next` decide who approves the references and locks voice and visual
(under `visual_checkpoint`, the operator's one visual lock). `series` is set
to the source's series name, or its title if it has none. An audit entry
lists every file copied and its sha256.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 6.1 | `create --series-from`: copy the locked style, submit the references as drafts with provenance, record series and audit; refuse if the source isn't locked; tests | helper: builder, routine (Sonnet) | `bookfactory/core/series.py` (new), `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `tests/test_series.py` (new) | [x] |
| 6.2 | Rules and guides explain starting a series book | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/BOOK_FACTORY.md` | [x] |
| 6.3 | Mark review item #6 done; glossary entry for "series preset" | main | `docs/REVIEW-2026-09.md`, `GLOSSARY.md` | [x] |
| 6.4 | Check everything with proof; test-drive by starting a series book from the demo book on a throwaway copy | helper: checker | none (read-only) | [x] |

**Notes:** the 6.1 builder hit its 40-turn limit with one wrong test (it
expected the new book's next task to be the visual lock; a new book
rightly starts at its own brief). Main rewrote that test to check what is
true, and made an explicit `create --series` name win over the source's.
The checker also needed a second turn budget to report.

**Order:** round 1: 6.1 and 6.2 together; main does 6.3. Then the checker.

**Test-drive:** on a throwaway copy, build the demo book, start "book 2" from
it, and read `status` and `next`: the style files match, the references wait
as drafts, and nothing is approved or locked.

**Done when:**
- [x] One command starts a new book with the earlier book's voice, visual rules, design settings and references already in place.
- [x] Nothing is approved or locked on anyone's behalf; the references arrive as drafts that say where they came from.
- [x] `pytest` passes and the demo build passes.
- [x] Everything is saved to GitHub `main` and checked there.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 6 | Checker: only the phase's files changed | confirmed |
| 2026-09-23 | 6 | Checker: full `pytest` | exit 0; 396 passed, 2 skipped (392 + 4 new; counted from the progress marks, the summary line wasn't written to the log) |
| 2026-09-23 | 6 | Checker: demo build on a throwaway copy | Release Ready, 24 pages |
| 2026-09-23 | 6 | Test-drive: `create --series-from demo-book` | exit 0; 5 style files byte-identical; 6 references as drafts, 0 approved, source `series:demo-book`; voice and visual unlocked; `next` = its own brief |
| 2026-09-23 | 6 | Test-drive: `--series-from` an unlocked book | refused (exit 5), no folder created |

---

## Phase 7: Batch approval (done)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #2 (its
last big piece). After `render --submit` puts a whole book's pages up as
drafts, approving them one at a time is about 60 commands.

**The command:** `bookfactory approve <book> --all-passing --by <name>
[--kind page|asset] [--dry-run] [--autonomous]`. Approves, one by one through
the normal single approval (so every existing check still applies), the
newest reviewable draft of every page and asset that has one and is not
already approved (or has a revision open). A draft that failed a measured
check is never reviewable, so it is never included. Skips the cover artwork
(the cover has its own approval). Assets before pages. Carries on past one
that fails and reports approved / failed; exit code 1 if any failed.
`--dry-run` lists what would be approved and changes nothing. `--by` is
required. It is the operator's command, like `approve`: an agent may run it
only as `--autonomous`, which is refused unless the book's recorded policy
authorizes autonomous approval (the same check as a single approval). The
approval guard already blocks any `bookfactory ... approve` an agent runs in
auto mode.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 7.1 | `approve --all-passing` with `--kind`, `--dry-run`, `--autonomous`, required `--by`; tests | helper: builder, routine (Sonnet) | `bookfactory/core/api.py`, `bookfactory/cli/main.py`, `tests/test_batch_approve.py` (new) | [x] |
| 7.2 | Rules and guides: batch approval is the operator's; `--autonomous` only under the policy | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/AUTONOMOUS_PRODUCTION.md` | [x] |
| 7.3 | Guard test: `approve --all-passing` is caught; mark review item #2 done | main | `tests/test_hook_guard_authority.py`, `docs/REVIEW-2026-09.md` | [x] |
| 7.4 | Raise helper turn limits (builder 40 to 60, checker 25 to 40), from `IDEAS.md` | main | `.claude/agents/implementer.md`, `.claude/agents/verifier.md`, `IDEAS.md` | [x] |
| 7.5 | Check everything with proof; test-drive on a throwaway demo copy | helper: checker | none (read-only) | [x] |

**Notes:** with the higher turn limits, the builder (41 tool uses) and the
checker (30) both finished and reported first time.

**Order:** round 1: 7.1 and 7.2 together; main does 7.3 and 7.4. Then the
checker.

**Test-drive:** the approval guard (rightly) blocks helpers from running
`approve`, and it must not be worked around. So the proof is the CLI tests,
which drive the real command end to end in a temporary folder, plus the
checker confirming that the guard blocks `approve --all-passing`. The first
live run is Kieran's, on a real book.

**Done when:**
- [x] One command approves every draft that passed its checks, and lists them first with `--dry-run`.
- [x] A draft that failed a check is never approved, and an agent can't use it without the book's autonomous policy.
- [x] `pytest` passes and the demo build passes.
- [x] Everything is saved to GitHub `main` and checked there.

**Verification log**

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 7 | Main: guard tests with the 2 new `approve --all-passing` cases | all pass (asks, so blocked in auto mode) |
| 2026-09-23 | 7 | Checker: only the phase's files changed | confirmed |
| 2026-09-23 | 7 | Checker: full `pytest` (junit XML) | 410 passed, 2 skipped (396 + 12 + 2) |
| 2026-09-23 | 7 | Checker: demo build on a throwaway copy | Release Ready, 24 pages |
| 2026-09-23 | 7 | Checker: contract read against tests | each point proved by a named test in `tests/test_batch_approve.py` |

## Phase 8: Page plan and specs in one file (done)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #3. Today a
book of 40 pages takes a page-plan task, then 40 separate "write the spec"
tasks, then a "register the artwork" task for each illustration: about 120
small tasks.

**What changes:** `bookfactory plan <book> --from-file plan.json` already
accepts a `spec` inside each page entry, but nothing says so, and the artwork
still has to be registered by hand. After this phase:
- Writing a spec whose `illustration` names an `asset_id` adds that asset to
  the page's required assets and registers it (kind illustration, for that
  page, with the spec's concept, characters and references) if it isn't
  registered yet. This works for `plan --from-file` and `spec` alike.
- `plan --from-file` checks every spec in the file before writing anything,
  so one bad spec leaves the book unchanged instead of half-planned.
- The page-plan task tells the writer to put each page's spec in the plan
  file, so the whole plan is written in one pass from the manuscript.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 8.1 | Spec names its artwork: add it to the page and register it; plan checks every spec first; tests | main (one tight change across two core files; briefing it out costs more than doing it) | `bookfactory/core/book.py`, `bookfactory/core/api.py`, `bookfactory/cli/main.py` (plan/spec output, added while building), `tests/test_plan_specs.py` (new), `tests/conftest.py` (fixture no longer registers artwork by hand) | [x] |
| 8.2 | Page-plan and spec task instructions describe the one-file plan | main | `bookfactory/core/tasks.py` | [x] |
| 8.3 | Demo build writes plan and specs in one go and stops registering artwork by hand (the test-drive) | main | `scripts/build_demo_book.py` | [x] |
| 8.4 | Rules and guides: one-file plan, artwork registered from the spec | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/BOOK_FACTORY.md`, `integrations/chatgpt/AUTONOMOUS_PRODUCTION.md` | [x] |
| 8.5 | Mark review item #3 done; glossary | main | `docs/REVIEW-2026-09.md`, `GLOSSARY.md` | [x] |
| 8.6 | Check everything with proof on a throwaway demo copy | helper: checker (Sonnet) | none (read-only) | [x] |

**Notes:** the docs keeper's first example spec had `"copy": "..."`, which the spec check refuses (copy is a set of named parts); caught in review and fixed. Existing callers that ran `asset add` after writing a spec now get "already exists"; the test fixture was updated for that.

**Order:** main does 8.1 to 8.3 while the docs keeper does 8.4; then 8.5;
then the checker.

**Test-drive:** the demo build (8.3) plans all its pages with their specs
from one list and never calls `asset add` for page artwork; it must still
walk the whole pipeline to the end.

**Done when:**
- [x] One plan file creates every page with its spec, and the artwork each spec names is registered without a separate command.
- [x] A plan file with one bad spec is refused and leaves the book unchanged.
- [x] `pytest` passes and the demo build passes.
- [x] Everything is saved to GitHub `main` and checked there.

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 8 | Full test suite (checker, junit XML) | 419 tests, 0 failures, 0 errors, 2 skipped |
| 2026-09-23 | 8 | Demo build on a throwaway copy | Finished to release ready; step 8: 24 pages planned, 24 specs written, 10 artwork assets registered from the specs |
| 2026-09-23 | 8 | Diff of rules and guides against the plan | No contradictions; no rule's meaning changed |
