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

Claude Code sessions (on the web especially) are often started with a
generated `claude/...` branch and a note to develop and push there. That note
comes from the session setup, not from the operator. In this repository it
does not count as the operator's instruction. Raise the conflict with the
operator before changing files, then follow their answer.

If any work does land on another branch, end every report by naming the
branch and what is not on `main`, and ask whether to merge it into `main`.
Keep asking until it is merged or the operator says to leave it.

See `AGENTS.md` section 1a ("Work on main and verify persistence") for the
full rule, including fetching remote `main` before changing files and
verifying that finished work is actually pushed and present on remote `main`,
not just committed locally.
