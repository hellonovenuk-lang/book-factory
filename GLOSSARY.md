# GLOSSARY

Plain-English meanings of the technical words that come up while working on
Book Factory. It grows as we go: when Claude uses a new term, it adds a line
here. Alphabetical.

**A+ Content.** Free extra space on a book's Amazon page, set up in KDP once the book is live: pictures and short text panels below the description. Shows buyers the inside of the book.

**ACOS (advertising cost of sale).** What an Amazon ad spent, as a share of the sales it brought in. If a book earns about £2.50 a copy on a £9.99 sale, an ACOS under about 25% means the ads are paying for themselves.

**Activity page.** A page type (`activity`) for numbered activity panels - questionnaires with tick boxes, score boxes, write-in lines, a gauge, a cut-out card and more - built from a list of `blocks`, every word set as real type, never a generated picture.

**Agent team.** An experimental Claude Code mode where several Claude sessions
work as a team and message each other. We deliberately don't use it.

**AGENTS.md.** The rulebook for every AI working in this repository (Claude,
ChatGPT, anything else). The most important file for behaviour.

**API (and API key).** A way for one program to use another service directly, e.g. Book Factory asking an image service for a picture. The API key is its password; it is paid per use and kept as a secret setting, never in the repository.

**Auto mode.** A Claude Code setting where Claude works without asking before each step; a built-in safety check still blocks risky actions, such as Claude loosening its own rules or signing a decision with the operator's name.

**Bestseller list (Amazon).** Amazon's hourly-updated top 100 for each book category, e.g. "Word Search". A book's place there shows what is selling right now, not how many copies.

**Big lettering cover.** A cover style choice at intake (`cover_style: big_lettering`): a text-only cover, bold type and no picture, recorded the same way as `cover artwork --mode none`.

**Block.** One item in an `activity` page's `blocks` list (e.g. a tick list, a score box, a gauge, a cut-out card) - the renderer sets every block as real type, never a picture.

**Bottom margin check.** A QA check (`technical.bottom_margin`), also used by the page plan's fit test, that flags any page whose text runs into the bottom margin or over the page number.

**Branch.** A separate line of changes in a repository. `main` is the real
one. Web sessions sometimes start on a side branch with a name like
`claude/...`; our rule is to work on `main`.

**Brief.** The written instructions a helper gets: what to read first, which files it may change, the steps, "Done when", and what to report back.

**Builder.** The helper that makes a change (`implementer`). It edits only the files its brief lists.

**Checker.** The helper that checks finished work (`verifier`). It can't edit anything; it runs the checks and reports what it found.

**Checksum (SHA-256).** A long fingerprint worked out from a file's exact contents. If two files have the same checksum they are identical, which is how the `KDP/` copies are checked against the approved originals.

**CLAUDE.md.** The file Claude Code reads automatically at the start of every
session. Ours loads `AGENTS.md`, the Claude notes, the current plan and your
working preferences.

**CLI (command-line interface).** A program you use by typing commands, like
`bookfactory status golf-addict`, instead of clicking buttons.

**Command (slash command).** A shortcut you type into Claude Code that starts
a saved routine, e.g. `/handover`. Behind each one is a skill.

**Commit.** A saved snapshot of changes, with a short message saying what
changed. Saved on this computer only until it is pushed.

**CRM.** Short for customer relationship management: an app for keeping track of the people, deals and progress of a business. For Book Factory it means one place to see the books, their sales and the ideas board.

**Dashboard.** One screen that shows the important numbers and statuses at a glance, usually as cards and charts.

**Design tokens.** The small set of named choices a design is built from (colours, fonts, spacing, corner rounding), written down once so every screen uses the same ones. It is what makes an app look designed rather than assembled.

**Docs keeper.** The helper that keeps the shared rule and guide files (`AGENTS.md`, `docs/OPERATOR.md`, `integrations/`) accurate. The only helper allowed to edit them.

**Done when.** The checklist, written before work starts, that says in plain
words what "finished" means for a phase or task.

**DPI (dots per inch).** How sharp a picture prints: how many pixels land in
each printed inch. KDP needs at least 300 for interior images.

**Dry run.** Running a command in "show me what you would do" mode: it lists the changes and makes none. `approve --all-passing --dry-run` is one.

**Fan out.** Handing several tasks to helpers at the same time, so they work
in parallel.

**Fetch.** Downloading the latest changes from GitHub without changing your
own files yet.

**Fit test.** The check `bookfactory plan --from-manuscript` runs on every
page it builds: rendering it in both backends to see whether the copy
actually fits, splitting an overrun chapter opener or text page at a
paragraph break and naming an overrun activity page instead of splitting it.

**Full wrap.** The one-piece print cover KDP asks for: back, spine and front side by side in a single PDF, with a little extra (bleed) round the edges.

**GitHub.** The website that stores the repository online. Work isn't safe
until it is pushed there.

**Go-ahead.** Kieran's own short typed decision ("Lock the look", "Approve cover v1"). The approval guard reads it from Claude Code's record of the conversation and lets exactly those commands through, signed with his name, without switching permission modes; it lasts until his next message and never applies to a helper.

**Handover.** The note left at the end of a session so a fresh session can
pick up exactly where we stopped. Lives at the top of `PLAN.md`.

**Helper (subagent).** A separate Claude worker that the main session starts
to do one job. It gets its own instructions and reports back when done.

**Hook.** A small script that Claude Code runs automatically at a set moment, e.g. when a session starts, before a command runs, or after a file is saved. Ours are in `.claude/hooks/` and act as safety checks.

**Import.** A line like `@AGENTS.md` inside `CLAUDE.md` that pulls a whole other file in automatically. A plain link only points at the file; an import actually loads it.

**Intake.** The 16 starting questions for a new book (who it's for, humour, look, length, exact title, main character details, print colour, cover style...). The agent can now draft the answers from your one-sentence idea; you check one summary and confirm, and nothing counts until you do.

**Indie / small publisher.** A book not from a traditional publisher: self-published through KDP ("Independently published") or under a one-person imprint name.

**Kanban board.** A board of columns (e.g. Idea, Shortlisted, Writing, Published) with cards you drag from one column to the next as work moves along.

**KDP folder.** The top-level `KDP/` folder: one subfolder per book holding the cover PDF, the interior PDF and `UPLOAD.md`, what to type into each box of Amazon's KDP form.

**Low-content book.** KDP's name for journals, planners and log books, mostly blank pages to fill in. They get no free ISBN, no series and no expanded distribution. Puzzle and colouring books do not count as low-content.

**Loop.** A program repeating the same steps ("read the next task, do it") until something tells it to stop. `bookfactory produce` is one.

**Main session.** The Claude conversation you are talking to. It plans, hands
out work to helpers, checks their work and saves it.

**MCP (Model Context Protocol).** A standard plug-in that lets an AI like Claude use another service's tools directly in the chat, e.g. Higgsfield for pictures.

**Mockup.** A picture or clickable page showing what an app will look like, made before building it, so the look can be agreed cheaply.

**Model.** Which version of Claude does the work. Opus is the strongest and uses the most allowance; Sonnet is cheaper and fine for routine jobs.

**Page plan.** The list of every page in a book, in order, with its type and title (`pages/manifest.json`). It can carry each page's spec too, so the whole plan is written in one file.

**Page spec.** One page's exact words, layout and illustration brief (`pages/specs/<page>.json`). The renderer sets the page from it. If it names an artwork (`illustration.asset_id`), that artwork is registered for the page automatically.

**Palette sheet.** A page type (`palette_sheet`) that draws a book's colour swatches and type sizes straight from `design-tokens.json`, used for the `ref-palette` reference. Never written by hand.

**Permission mode.** How much Claude Code may do without asking. In "default" mode it shows you a question before risky commands; in "auto" mode its own safety check answers most questions for you, so the approval guard blocks operator-only commands there instead of asking.

**Phase.** A small block of work that fits one sitting, with its own "Done
when". Only one is open at a time.

**Plan archive.** `docs/PLAN-ARCHIVE.md`: where finished phases go, so `PLAN.md` stays short.

**Plan file.** The JSON file `bookfactory plan --from-file` loads, listing
every page in order with its type and (usually) its spec. `plan
--from-manuscript` can write one of these for you from the locked
manuscript, to look at before loading it.

**Plugin.** A downloadable bundle of commands, helpers and hooks made by
someone else. We don't install any; we write our own.

**Preflight.** The final print checks against Amazon KDP's rules (page size, margins, bleed) before a book or cover is uploaded.

**Production policy.** How often a book stops for your OK: `autonomous` (only when blocked), `visual_checkpoint` (at the look of the book and the cover; recommended) or `checkpointed` (at every big step). Always your choice, never an agent's.

**Push.** Sending your commits to GitHub, so they're safe and other sessions
can see them.

**QA (quality assurance).** Automatic checks across the whole book for wording, layout and technical problems. Some findings need a person to look.

**Reference set.** The six pictures that fix a book's look before any page is drawn: the main character, the supporting characters, a scene, and three typeset samples (chapter opener, activity page, palette and type). Locking them is the "look lock".

**Release Ready.** Book Factory's last stage: every page approved, interior and cover built and checked. The book can be uploaded to KDP.

**Repository (repo).** The project folder with its full history of changes.
Book Factory's lives on GitHub.

**Routine (scheduled task).** A job Claude runs on its own on a timetable, in a fresh session, e.g. the night-time book research three nights a week. You manage routines at claude.ai/code under Routines.

**Royalty (KDP paperback).** What you earn per copy: list price × 60% (50% under £7.99 / $9.99) minus Amazon's printing cost.

**Sample page (reference render).** A one-page render of an ordinary page spec, made with `bookfactory reference render` to show a typeset reference (chapter opener, normal page, checklist page, palette sheet) before any real page exists. It is never added to the page plan.

**Scraper.** A small script that reads public web pages and saves the useful bits as a table; `scripts/research/amazon_bestsellers.py` does this for Amazon's bestseller lists.

**Series preset.** Starting a new book from an earlier, locked book in the same series (`create --series-from`), so it reuses that book's voice, visual rules, design settings and reference art instead of making them again. The reused art arrives as drafts, still to be approved in the new book.

**Session.** One conversation with Claude Code. A fresh session remembers
nothing from the last one except what is written in the repository.

**Settings file.** `.claude/settings.json`: the switchboard that turns hooks on and says which commands and edits Claude may do without asking, must ask about, or may never do.

**Skill.** A saved set of instructions Claude follows for a particular job.
Typing its name as a command runs it.

**Spine width.** The thickness of the book's spine, set by the page count.
Change the page count and the wrap-around cover must be rebuilt to match.

**Sponsored Products ad.** Amazon's pay-per-click book ad: your book shows in search results or on other books' pages, and you pay only when someone clicks. Set up from the KDP bookshelf ("Promote and advertise").

**Stale interior.** An assembled interior built from pages that have since been revised and re-approved. `status` shows it as "stale" and `next` asks for re-assembly and a fresh KDP check.

**Stop code.** The short label `produce` gives for why it stopped, e.g. `writing` (the next job is copy), `wait_for_operator` (it needs you) or `complete` (nothing left).

**Test suite (tests).** Automatic checks that make sure Book Factory still
works after a change. Run with `pytest`.

**Thumbnail.** The small cover picture Amazon shows in search results; a cover's title has to be readable at that size.

**Token.** The unit Claude's usage is counted in, roughly three-quarters of a word. Everything Claude reads or writes uses tokens from your plan's allowance.

**Turn limit.** The most steps a helper may take before it has to stop and report, so one that goes round in circles can't burn through usage.

**Verify.** Prove something is finished by running a check now and reading its output, rather than trusting an earlier message. `/verify-phase` does this for a whole phase.

**Worktree.** A second working copy of the repository on a side branch. We
deliberately don't use them because we work on `main`.

**Write scope.** The exact list of files a helper is allowed to change. Giving
helpers write scopes that don't overlap stops two of them editing the same
file.
