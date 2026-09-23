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

## Phase 9: One-prompt start (done)

Chosen 2026-09-23 by Kieran, from `docs/REVIEW-2026-09.md` item #7. Today a
book started from one idea stops at a 12-question form that the operator
answers in full before anything happens.

**What changes:** the agent drafts the answers from the idea; the operator
checks one summary, fixes anything wrong and confirms in one reply.
- `bookfactory intake <book> --draft --by <agent> --from-file <answers.json>`
  saves the agent's best guesses as a **draft**, with an optional `unclear`
  list of the questions it could not answer from the idea. A draft never
  completes intake. Any answer given must be valid; an answer left out must
  be listed as unclear. A draft that contains `production_policy` is refused:
  the policy is always the operator's own choice (`AGENTS.md` 3b).
- `bookfactory intake <book> --confirm --by <operator> --policy <mode>
  [--set key=value ...]` merges the operator's corrections into the draft,
  checks the full set, and completes intake exactly as today, recording that
  the answers were drafted by the agent and confirmed by the operator, and
  which answers the operator changed.
- The intake task explains both steps: draft and show the summary if there is
  no draft yet; otherwise show the draft and wait for the operator's reply.
  Its mode stays `wait_for_operator`.
- The plain `intake --from-file` (the operator answering everything) keeps
  working.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 9.1 | Draft and confirm in the core: draft state, checks, audit entries; tests | main (tight change across small core files) | `bookfactory/core/intake.py`, `bookfactory/core/models.py`, `bookfactory/core/api.py`, `bookfactory/core/audit.py`, `schemas/book.schema.json`, `bookfactory/core/book.py` (status shows a waiting draft, added while building), `tests/test_intake_draft.py` (new) | [x] |
| 9.2 | `intake --draft` and `intake --confirm` on the command line; `status` shows a waiting draft | main | `bookfactory/cli/main.py` | [x] |
| 9.3 | Intake task instructions for the draft-then-confirm routine | main | `bookfactory/core/tasks.py` | [x] |
| 9.4 | Rules and guides: one-prompt start; the policy is still only the operator's | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/chatgpt/BOOK_FACTORY.md`, `integrations/chatgpt/AUTONOMOUS_PRODUCTION.md`, `integrations/README.md` (checked, no change needed) | [x] |
| 9.5 | Mark review item #7 done; glossary | main | `docs/REVIEW-2026-09.md`, `GLOSSARY.md` | [x] |
| 9.6 | Check everything with proof on a throwaway demo copy | helper: checker (Sonnet) | none (read-only) | [x] |

**Notes:** review caught two doc slips, both fixed: the example draft file nested its answers (the command now accepts both layouts), and one rule sentence ("never start with `create` to skip intake") had been dropped. The safety guard blocked a Bash edit of `api.py` because the new text mentioned the policy; the normal file-edit tool was used instead (the `IDEAS.md` guard item).

**Order:** main does 9.1 to 9.3 while the docs keeper does 9.4; then 9.5;
then the checker.

**Test-drive:** a test starts a book from one sentence, saves a draft with
one unclear answer, confirms it with one correction and a policy, and the
next task moves past intake.

**Done when:**
- [x] A book started from one sentence can have its 12 answers drafted by the agent and confirmed by the operator in one step.
- [x] A draft never completes intake on its own, and can never contain the production policy.
- [x] `pytest` passes and the demo build passes.
- [x] Everything is saved to GitHub `main` and checked there.

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 9 | Full test suite (checker, junit XML) | 431 tests, 0 failures, 0 errors, 2 skipped |
| 2026-09-23 | 9 | Demo build on a throwaway copy | Finished to release ready, 24 pages |
| 2026-09-23 | 9 | Real command-line try-out in a temp folder | Draft saved and shown as waiting; a draft with the policy refused; confirm completed intake with drafted_by, confirmed_by and the changed answer recorded |
| 2026-09-23 | 9 | Diff of rules and guides against the plan | No contradictions; the operator-only policy rule is intact |

## Phase 10: Test one picture through Higgsfield (done)

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
| 10.2 | Record what worked, what didn't, the cost, and the routine to write into the rules if Kieran is happy | main | `PLAN.md`, `IDEAS.md` | [x] |

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
- **Second try (Kieran asked):** the prompt added "completely plain unbranded
  shorts", "a single kettle", "nothing on the table except Sam's mug", "plain
  white paper, very sparse background, like the third reference". Result
  (draft v2, 1792x2400, measured checks passed, 2 more credits): no logo, one
  kettle, white paper, sparse background, characters still match. Clean on
  Claude's review. Lesson for the routine: name the visual bible's "Never"
  items and the reference's sparseness in every prompt, not just the scene.
- **Kieran's verdict (2026-09-23):** second picture approved.
- Rule 6 still holds: an operator (or an agent under `autonomous`) must
  judge the match; the measured checks cannot see a logo.

**Done when:**
- [x] One picture made through Higgsfield from a real Book Factory task, with the book's approved references, has been submitted as a draft in a throwaway copy, and its measured checks are reported.
- [x] Kieran has seen it beside the references, and the findings and cost are written down.
- [x] Everything is saved to GitHub `main` and checked there.

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 10 | Higgsfield picture from a real task, in a throwaway copy | Draft v1 and v2 both passed measured checks (1792x2400); v2 clean on review and approved by Kieran; 4 credits used, 66 left |

## Phase 11: Picture budget and the Higgsfield routine (done)

Chosen 2026-09-23 by Kieran: "chapter openers only is the default; if I want
more I'll request it." Nothing limits the number of pictures today, and each
costs Higgsfield credits and an operator review. Phase 10 proved Claude can
make book pictures through the Higgsfield connector; the rules still say
Claude cannot.

**What changes:**
- Every book records a **picture budget**: `chapter_openers` (pictures only
  on chapter-opener pages; the cover is separate and always allowed),
  `limit` with a number (at most that many page pictures), or `unlimited`.
  New books start at `chapter_openers`. Books made before this phase load as
  `unlimited`, so nothing already planned breaks.
- Writing a spec that names a picture (by `plan --from-file` or `spec`) is
  refused when it would break the budget, naming the page and how to ask the
  operator. A plan file that breaks it is refused whole (Phase 8's check).
- `bookfactory pictures show <book>` (read-only) and `bookfactory pictures
  set <book> <budget> [--count N] --by <operator>` (operator only, audited as
  `picture_budget_changed`; the approval guard asks first, like `policy set`).
- The page-plan task says what the budget allows.
- The rules say: never raise the budget yourself; and when the Higgsfield
  connector is available, Claude makes pictures through it with the Phase 10
  routine and prompt lesson, then submits them as drafts. Approval rules are
  unchanged.

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 11.1 | Budget in the core: state, show/set, the check on writing a spec, audit entry; tests | main | `bookfactory/core/models.py`, `bookfactory/core/book.py`, `bookfactory/core/api.py`, `bookfactory/core/audit.py`, `schemas/book.schema.json`, `tests/test_picture_budget.py` (new), `tests/conftest.py` | [x] |
| 11.2 | `pictures show` / `pictures set` on the command line; `status` shows the budget | main | `bookfactory/cli/main.py` | [x] |
| 11.3 | Page-plan task says what the budget allows | main | `bookfactory/core/tasks.py` | [x] |
| 11.4 | Demo build records its budget (`unlimited`, it has 10 page pictures) as the operator's choice | main | `scripts/build_demo_book.py`, `scripts/end_to_end_check.py` (same need, found while building) | [x] |
| 11.5 | Approval guard asks before `pictures set`; guard test | main | `.claude/hooks/guard-authority.py`, `tests/test_hook_guard_authority.py` | [x] |
| 11.6 | Rules and guides: the budget, and the Higgsfield picture routine for Claude | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/claude/BOOK_FACTORY.md`, `integrations/chatgpt/BOOK_FACTORY.md`, `integrations/chatgpt/AUTONOMOUS_PRODUCTION.md` | [x] |
| 11.7 | Check everything with proof on a throwaway demo copy | helper: checker (Sonnet) | none (read-only) | [x] |

**Notes:** the checker found one real regression: `tests/test_state.py` keeps its own list of known audit events and lacked `picture_budget_changed`; added, and the full suite re-run clean. `scripts/end_to_end_check.py` also needed the budget raised (its p002 has a picture). The checker hit its 40-turn limit before reporting and was asked to report what it had.

**Done when:**
- [x] A new book allows pictures only on chapter openers (plus the cover), and a plan asking for more is refused with a clear message.
- [x] Only the operator can raise the budget, and it is recorded who did.
- [x] The rules tell Claude how to make pictures through Higgsfield.
- [x] `pytest` passes, the demo build passes, and everything is saved to GitHub `main`.

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 11 | Full test suite (after the fix, main session, junit XML) | 446 tests, 0 failures, 0 errors, 2 skipped |
| 2026-09-23 | 11 | Demo build and end-to-end check on a throwaway copy (checker) | Demo release ready, 24 pages, budget unlimited recorded as the operator's; end-to-end 37/37 |
| 2026-09-23 | 11 | Command-line try-out (checker) | New book shows chapter_openers; the guard stops `pictures set` and allows `pictures show` |
| 2026-09-23 | 11 | Diff of rules and guides | No rule weakened; Higgsfield routine and budget rule consistent |

## Phase 12: `produce`, first slice (done)

Chosen 2026-09-23 by Kieran: review item #8 (`docs/REVIEW-2026-09.md`),
hands-off production. #8 is bigger than one sitting; this is its first slice.
The later slices are parked in `IDEAS.md`.

**What changes:**
- `bookfactory produce <book>` repeats "read the next task, do it" for the
  purely mechanical tasks only: `page_render` (`render --page <id>
  --submit`), `qa`, `assembly` and `preflight`. It runs one only when that
  task's `mode` is `continue_automatically`, so it follows the book's
  recorded policy (`AGENTS.md` section 3a).
- It stops at the first task of any other kind (writing, a picture, an
  approval, a lock, an operator decision, remediation, blocked, complete)
  and says in plain words why it stopped and what the next task is.
- It never approves, locks, advances or forces anything. It has a step limit
  (`--max-steps`) and stops if a step leaves the same task as next (no
  progress). `--dry-run` shows the first step it would take and changes
  nothing. `--json` for agents.
- The logic lives in `bookfactory/core/produce.py`; the CLI is only an
  adapter (`integrations/claude/BOOK_FACTORY.md`).

| # | Task | Who | Files | Status |
|---|---|---|---|---|
| 12.1 | The loop in the core, `api.produce`, and tests: runs each mechanical task, stops at every other kind with a reason, never approves/locks/advances, obeys `mode`, step limit, no-progress stop, dry run changes nothing | helper: builder, tricky (Opus: it sits on the safety rules) | `bookfactory/core/produce.py` (new), `bookfactory/core/api.py`, `tests/test_produce.py` (new) | [x] |
| 12.2 | `bookfactory produce <book> [--max-steps N] [--dry-run] [--json]`, after 12.1 | helper: builder, routine (Sonnet) | `bookfactory/cli/main.py`, `tests/test_produce_cli.py` (new) | [x] |
| 12.3 | Rules and guides: what `produce` does and never does; quick-reference line | helper: docs keeper, routine (Sonnet) | `AGENTS.md`, `docs/OPERATOR.md`, `integrations/claude/BOOK_FACTORY.md` | [x] |
| 12.4 | Park the later slices; new glossary terms; this plan | main | `IDEAS.md`, `GLOSSARY.md`, `PLAN.md` | [x] |

**Test-drive:** run `produce` on a throwaway copy of the demo book
(`/verify-phase`) and see where it stops and what it says.

**Done when:**
- [x] `bookfactory produce <book>` runs the mechanical steps by itself and stops with a plain reason at the first thing that needs writing, a picture or the operator.
- [x] Tests prove it never approves, locks or skips a gate.
- [x] All tests pass (`pytest`) and the demo build passes (`python scripts/build_demo_book.py`, on a throwaway copy).

**Notes:** the second checker hit its 40-turn limit and was asked to report what it had. A live render on the demo copy was not shown: setting one up needed `revise`, which the guard rightly blocks for helpers; the render path is proved by tests. As built, `produce` renders one page and then stops at its approval; slice 2 (in `IDEAS.md`) is what lets it continue.

| Date | Phase | Check | Result |
|---|---|---|---|
| 2026-09-23 | 12.1 | Checker: scope, produce.py calls only render/qa/assemble/preflight/next, full suite, demo build + produce on a throwaway copy | Pass: 466 tests, 0 failed, 2 skipped; demo build passed; produce stopped at an illustration task with a plain reason |
| 2026-09-23 | 12.2, 12.3 | Checker: scope, CLI calls only api.produce, exit codes, `--max-steps 0` refused, docs match the code, full suite, demo build + `produce` (plain, `--dry-run`, `--json`) on a throwaway copy | Pass: 471 tests, 0 failed, 2 skipped. A live render run wasn't shown, because making one needed `revise`, which the guard rightly blocks for helpers; the render path is proved by tests |
