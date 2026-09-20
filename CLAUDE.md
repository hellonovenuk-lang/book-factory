# CLAUDE.md

This repository's rules for AI agents live in [`AGENTS.md`](AGENTS.md) - read it
first, in full, before doing anything else. It is vendor-neutral and applies to
you exactly as written.

Claude-specific operating notes (starting a session, the split between
operating a book and maintaining Book Factory itself, image generation, how to
report back) are in
[`integrations/claude/BOOK_FACTORY.md`](integrations/claude/BOOK_FACTORY.md).
Read that too.

This file exists only to point you at those two, not to duplicate or override
them.

## Branch policy

Work exclusively on `main` unless the operator explicitly instructs you, for
the specific task at hand, to use a different branch. Do not create a feature,
recovery, or temporary branch by default.

See `AGENTS.md` section 1a ("Work on main and verify persistence") for the
full rule, including fetching remote `main` before changing files and
verifying that finished work is actually pushed and present on remote `main`,
not just committed locally.
