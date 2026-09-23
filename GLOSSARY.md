# GLOSSARY

Plain-English meanings of the technical words that come up while working on
Book Factory. It grows as we go: when Claude uses a new term, it adds a line
here. Alphabetical.

**API (and API key).** A way for one program to use another service directly, e.g. Book Factory asking an image service for a picture. The API key is its password; it is paid per use and kept as a secret setting, never in the repository.

**Agent team.** An experimental Claude Code mode where several Claude sessions
work as a team and message each other. We deliberately don't use it.

**AGENTS.md.** The rulebook for every AI working in this repository (Claude,
ChatGPT, anything else). The most important file for behaviour.

**Branch.** A separate line of changes in a repository. `main` is the real
one. Web sessions sometimes start on a side branch with a name like
`claude/...`; our rule is to work on `main`.

**Brief.** The written instructions a helper gets: what to read first, which files it may change, the steps, "Done when", and what to report back.

**Builder.** The helper that makes a change (`implementer`). It edits only the files its brief lists.

**Checker.** The helper that checks finished work (`verifier`). It can't edit anything; it runs the checks and reports what it found.

**CLAUDE.md.** The file Claude Code reads automatically at the start of every
session. Ours loads `AGENTS.md`, the Claude notes, the current plan and your
working preferences.

**CLI (command-line interface).** A program you use by typing commands, like
`bookfactory status golf-addict`, instead of clicking buttons.

**Command (slash command).** A shortcut you type into Claude Code that starts
a saved routine, e.g. `/handover`. Behind each one is a skill.

**Commit.** A saved snapshot of changes, with a short message saying what
changed. Saved on this computer only until it is pushed.

**Docs keeper.** The helper that keeps the shared rule and guide files (`AGENTS.md`, `docs/OPERATOR.md`, `integrations/`) accurate. The only helper allowed to edit them.

**DPI (dots per inch).** How sharp a picture prints: how many pixels land in
each printed inch. KDP needs at least 300 for interior images.

**Done when.** The checklist, written before work starts, that says in plain
words what "finished" means for a phase or task.

**Dry run.** Running a command in "show me what you would do" mode: it lists the changes and makes none. `approve --all-passing --dry-run` is one.

**Fan out.** Handing several tasks to helpers at the same time, so they work
in parallel.

**Fetch.** Downloading the latest changes from GitHub without changing your
own files yet.

**GitHub.** The website that stores the repository online. Work isn't safe
until it is pushed there.

**Handover.** The note left at the end of a session so a fresh session can
pick up exactly where we stopped. Lives at the top of `PLAN.md`.

**Helper (subagent).** A separate Claude worker that the main session starts
to do one job. It gets its own instructions and reports back when done.

**Hook.** A small script that Claude Code runs automatically at a set moment, e.g. when a session starts, before a command runs, or after a file is saved. Ours are in `.claude/hooks/` and act as safety checks.

**Import.** A line like `@AGENTS.md` inside `CLAUDE.md` that pulls a whole other file in automatically. A plain link only points at the file; an import actually loads it.

**Intake.** The 12 starting questions for a new book (who it's for, humour, look, length...). The agent can now draft the answers from your one-sentence idea; you check one summary and confirm, and nothing counts until you do.

**MCP (Model Context Protocol).** A standard plug-in that lets an AI like Claude use another service's tools directly in the chat, e.g. Higgsfield for pictures.

**Main session.** The Claude conversation you are talking to. It plans, hands
out work to helpers, checks their work and saves it.

**Model.** Which version of Claude does the work. Opus is the strongest and uses the most allowance; Sonnet is cheaper and fine for routine jobs.

**Page plan.** The list of every page in a book, in order, with its type and title (`pages/manifest.json`). It can carry each page's spec too, so the whole plan is written in one file.

**Page spec.** One page's exact words, layout and illustration brief (`pages/specs/<page>.json`). The renderer sets the page from it. If it names an artwork (`illustration.asset_id`), that artwork is registered for the page automatically.

**Permission mode.** How much Claude Code may do without asking. In "default" mode it shows you a question before risky commands; in "auto" mode its own safety check answers most questions for you, so the approval guard blocks operator-only commands there instead of asking.

**Phase.** A small block of work that fits one sitting, with its own "Done
when". Only one is open at a time.

**Plan archive.** `docs/PLAN-ARCHIVE.md`: where finished phases go, so `PLAN.md` stays short.

**Plugin.** A downloadable bundle of commands, helpers and hooks made by
someone else. We don't install any; we write our own.

**Production policy.** How often a book stops for your OK: `autonomous` (only when blocked), `visual_checkpoint` (at the look of the book and the cover; recommended) or `checkpointed` (at every big step). Always your choice, never an agent's.

**Push.** Sending your commits to GitHub, so they're safe and other sessions
can see them.

**Repository (repo).** The project folder with its full history of changes.
Book Factory's lives on GitHub.

**Series preset.** Starting a new book from an earlier, locked book in the same series (`create --series-from`), so it reuses that book's voice, visual rules, design settings and reference art instead of making them again. The reused art arrives as drafts, still to be approved in the new book.

**Session.** One conversation with Claude Code. A fresh session remembers
nothing from the last one except what is written in the repository.

**Settings file.** `.claude/settings.json`: the switchboard that turns hooks on and says which commands and edits Claude may do without asking, must ask about, or may never do.

**Spine width.** The thickness of the book's spine, set by the page count.
Change the page count and the wrap-around cover must be rebuilt to match.

**Skill.** A saved set of instructions Claude follows for a particular job.
Typing its name as a command runs it.

**Test suite (tests).** Automatic checks that make sure Book Factory still
works after a change. Run with `pytest`.

**Token.** The unit Claude's usage is counted in, roughly three-quarters of a word. Everything Claude reads or writes uses tokens from your plan's allowance.

**Turn limit.** The most steps a helper may take before it has to stop and report, so one that goes round in circles can't burn through usage.

**Verify.** Prove something is finished by running a check now and reading its output, rather than trusting an earlier message. `/verify-phase` does this for a whole phase.

**Worktree.** A second working copy of the repository on a side branch. We
deliberately don't use them because we work on `main`.

**Write scope.** The exact list of files a helper is allowed to change. Giving
helpers write scopes that don't overlap stops two of them editing the same
file.
