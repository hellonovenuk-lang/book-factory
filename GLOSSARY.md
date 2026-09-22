# GLOSSARY

Plain-English meanings of the technical words that come up while working on
Book Factory. It grows as we go: when Claude uses a new term, it adds a line
here. Alphabetical.

**Agent team.** An experimental Claude Code mode where several Claude sessions
work as a team and message each other. We deliberately don't use it.

**AGENTS.md.** The rulebook for every AI working in this repository (Claude,
ChatGPT, anything else). The most important file for behaviour.

**Branch.** A separate line of changes in a repository. `main` is the real
one. Web sessions sometimes start on a side branch with a name like
`claude/...`; our rule is to work on `main`.

**CLAUDE.md.** The file Claude Code reads automatically at the start of every
session. Ours loads `AGENTS.md`, the Claude notes, the current plan and your
working preferences.

**CLI (command-line interface).** A program you use by typing commands, like
`bookfactory status golf-addict`, instead of clicking buttons.

**Command (slash command).** A shortcut you type into Claude Code that starts
a saved routine, e.g. `/handover`. Behind each one is a skill.

**Commit.** A saved snapshot of changes, with a short message saying what
changed. Saved on this computer only until it is pushed.

**Done when.** The checklist, written before work starts, that says in plain
words what "finished" means for a phase or task.

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

**Hook.** A small script that runs automatically at a set moment, e.g. when a
session starts or before a command runs. Used for safety checks.

**Main session.** The Claude conversation you are talking to. It plans, hands
out work to helpers, checks their work and saves it.

**Phase.** A small block of work that fits one sitting, with its own "Done
when". Only one is open at a time.

**Plugin.** A downloadable bundle of commands, helpers and hooks made by
someone else. We don't install any; we write our own.

**Push.** Sending your commits to GitHub, so they're safe and other sessions
can see them.

**Repository (repo).** The project folder with its full history of changes.
Book Factory's lives on GitHub.

**Session.** One conversation with Claude Code. A fresh session remembers
nothing from the last one except what is written in the repository.

**Skill.** A saved set of instructions Claude follows for a particular job.
Typing its name as a command runs it.

**Test suite (tests).** Automatic checks that make sure Book Factory still
works after a change. Run with `pytest`.

**Worktree.** A second working copy of the repository on a side branch. We
deliberately don't use them because we work on `main`.

**Write scope.** The exact list of files a helper is allowed to change. Giving
helpers write scopes that don't overlap stops two of them editing the same
file.
