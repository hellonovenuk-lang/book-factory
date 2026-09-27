#!/usr/bin/env python3
"""Approval guard: a Claude Code PreToolUse hook for the Bash tool.

AGENTS.md sections 3 and 4 say an agent never approves, locks, rejects,
revises or changes policy on the operator's behalf, and never writes into
approved material. This hook makes those rules mechanical.

Before Claude runs a Bash command, the hook reads the command and answers:

* **ask**   - it runs a Book Factory command that needs the operator's
              authority (approve, lock, reject, revise, policy set,
              advance, assemble, preflight, cover approve/finalize/preflight),
              in any disguise the guard can see through.
* **deny**  - it would write into approved work (`pages/approved/`,
              `assets/approved/`, any `/approved/` path, or a
              `cover/drafts/*.pdf` file, which is where the approved cover
              lives).
* nothing   - anything else: the hook has no opinion. That includes
              `approve`, `lock` and `cover approve` run with
              `--autonomous` (and not signed with the operator's name):
              Book Factory itself refuses those unless the book's recorded
              production policy authorizes them (AGENTS.md section 3). It
              also includes the last release steps (`advance <book> --to
              release_ready`, `cover finalize`, `cover preflight`) when the
              book's own next task asks for exactly that step with mode
              `continue_automatically` (see `release_step_decision`).
* **deny**  - it would write, move, copy over or delete the guard's own
              files or what it trusts: `.claude/hooks/`,
              `.claude/settings*.json`, `.claude/state/`, and the session
              transcripts under `~/.claude/projects/` (or the payload's
              `transcript_path` folder).
* **allow** (explicit, with a reason) - a command line made only of
              `bookfactory` commands that Kieran's own latest typed message
              clearly decides ("Lock the look", "approve cover v1"). The
              guard reads that message from Claude Code's transcript, never
              from a file in the project, and never for a helper (subagent).
              See "the go-ahead" below for the exact, deliberately strict
              rules. Writes into approved work stay denied.

This is a guard against mistakes, not a sandbox against a deliberately
adversarial agent: a determined agent with a shell has ways round any list of
command patterns (a script run by name, for one). It stops the ordinary slips
and makes the rules mechanical; it does not replace them.

An **ask** only reaches the operator in the "default" permission mode. In
auto mode (and bypass or don't-ask modes) Claude Code settles an ask without
showing it, so the guard turns it into a **deny** there, or whenever the mode
is missing or unknown. The reason tells Claude to stop and ask the operator
in the chat.

Contract (Claude Code PreToolUse): JSON on stdin; an ask/deny decision is
printed to stdout as `hookSpecificOutput` JSON and the exit code is 0. If the
hook cannot read its input, or fails in any way, it asks (never a silent
allow, never a traceback), which becomes a deny outside "default" mode.

Registered in `.claude/settings.json` with matcher "Bash" and the command
`python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-authority.py"`.

Standard library only; Python 3.10+. When the guard is unsure it prefers a
false alarm (asking) over a miss.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ALLOW, ASK, DENY = "allow", "ask", "deny"
_RANK = {ALLOW: 0, ASK: 1, DENY: 2}

MAX_DEPTH = 6  # nesting of bash -c / $(...) / eval the guard follows

# -- reasons (plain English, shown to the operator) -------------------------

APPROVED_REASON = ("Approved work is never changed directly (AGENTS.md section 4). "
                   "Use `bookfactory revise` instead.")
BLOCKED_SUFFIX = (" Blocked, because in this permission mode the question would not reach "
                  "Kieran. Stop and ask Kieran in the chat. To run it, Kieran switches to "
                  "the default permission mode (the question then appears) or runs it "
                  "themselves.")
ASK_MODES = {"default"}  # permission modes where an ask is shown to the operator
UNREADABLE_REASON = ("The approval guard couldn't read this command, so it is asking to be "
                     "safe. Kieran must confirm.")

OPERATOR_ONLY = {
    "approve": "approves work, which only the operator may decide (AGENTS.md section 3)",
    "lock": "locks a stage of the book, which only the operator may decide (AGENTS.md section 3)",
    "reject": "rejects a draft, which only the operator may decide (AGENTS.md quick reference)",
    "revise": "reopens approved work, which only the operator may decide (AGENTS.md section 4)",
}
NEEDS_AUTHORITY = {
    "advance": "moves the book to its next stage, which needs the operator's authority "
               "(AGENTS.md quick reference)",
    "assemble": "builds the final interior, which needs the operator's authority "
                "(AGENTS.md quick reference)",
    "preflight": "runs the release check, which needs the operator's authority "
                 "(AGENTS.md quick reference)",
}
COVER_AUTHORITY = {
    "approve": "approves the cover, which only the operator may decide (AGENTS.md section 9a)",
    "finalize": "finalizes the approved cover, which needs the operator's authority "
                "(AGENTS.md section 9a)",
    "preflight": "runs the cover release check, which needs the operator's authority "
                 "(AGENTS.md quick reference)",
}
POLICY_SET = ("changes the book's production policy, which only the operator may do, and "
              "only when they ask for it (AGENTS.md quick reference)")
PICTURES_SET = ("changes how many pictures the book may have, which only the operator may "
                "do, and only when they ask for it (AGENTS.md section 5a)")
ADVANCE_FORCE = ("skips the stage gates, which only the operator may do "
                 "(AGENTS.md section 8)")

AUTHORITY_WORDS = ("approve", "lock", "reject", "revise", "advance", "assemble", "preflight",
                   "finalize", "set_policy", "policy")
_AUTHORITY_RE = re.compile(r"\b(" + "|".join(AUTHORITY_WORDS) + r")\b")
# `bookfactory ... <authority word>` on one line, used when the guard cannot
# see the command structure (text piped into a shell or an interpreter).
_LOOSE_BF_RE = re.compile(r"bookfactory[^\n]*?\b(approve|lock|reject|revise|advance|assemble"
                          r"|preflight|finalize|set)\b")


def ask_reason(what: str, why: str) -> str:
    return f"This runs `{what}`, which {why}. Kieran must confirm."


# Commands an agent may run itself with `--autonomous` (AGENTS.md section 3 and
# the quick reference). Book Factory refuses `--autonomous` unless the book's
# recorded production policy authorizes it, refuses what that policy keeps as
# a checkpoint (the visual lock and the full-wrap cover under
# visual_checkpoint), and audits every one as granted under the policy. So the
# guard lets these through and leaves that judgement to Book Factory.
AUTONOMOUS_OK = {"approve", "lock", "cover approve"}
# Options whose next word is a value, so a value can never pass for a flag.
_VALUE_OPTIONS = ("--by", "--note", "--version", "--draft", "--reason", "--root", "--count")
OPERATOR_NAMES = {"kieran"}
AUTONOMOUS_AS_OPERATOR = ("signs an `--autonomous` step with the operator's name; an agent "
                          "signs with its own name (AGENTS.md section 3)")


def autonomous_flags(rest: list[str]) -> tuple[bool, str | None]:
    """Whether `--autonomous` is given as a real flag, and the `--by` value."""
    autonomous, by = False, None
    k = 0
    while k < len(rest):
        a = rest[k]
        name = a.split("=", 1)[0]
        if a == "--autonomous":
            autonomous = True
        elif name == "--by":
            by = a.split("=", 1)[1] if "=" in a else (rest[k + 1] if k + 1 < len(rest) else None)
        if "=" not in a and name in _VALUE_OPTIONS:
            k += 2
            continue
        k += 1
    return autonomous, by


def autonomous_decision(what: str, rest: list[str], reason: str):
    """ALLOW an `--autonomous` step, else the ordinary ASK."""
    autonomous, by = autonomous_flags(rest)
    if not autonomous:
        return ASK, reason
    if SUBST in " ".join(rest) or "$" in " ".join(rest):
        return ASK, reason
    if by is not None and by.strip().lower() in OPERATOR_NAMES:
        return ASK, ask_reason(f"bookfactory {what} --autonomous", AUTONOMOUS_AS_OPERATOR)
    return ALLOW, ""


# -- the last release steps, when the book's own next task asks for them ------
#
# Rule (Phase 19, task 19.2): `bookfactory advance <book> --to release_ready`,
# `bookfactory cover finalize <book> [--draft vN]` and
# `bookfactory cover preflight <book>` are let through only when ALL hold:
#   * the command is plain enough to read: `bookfactory` is the program itself
#     (optionally after plain VAR=value words), nothing in it is a variable,
#     substitution or glob, no `cd`/`pushd`/`popd` anywhere in the command
#     line, only the options listed below, and no `--force`;
#   * the book id is a literal word;
#   * the book's current next task, read read-only (`api.next_task`, the same
#     derivation as `bookfactory next <book> --json`, in a subprocess with a
#     short timeout, at the same root the command would use: `--root`, else
#     BOOKFACTORY_ROOT, else the root found from the session's cwd), is the
#     matching task - by its id, its type and its instructions naming that
#     exact command - and its `mode` is `continue_automatically`.
# Otherwise the ordinary ASK stands. Any failure (error, timeout, unreadable
# output, unknown book) means ASK, never ALLOW.
#
# Why this is safe: these commands have no `--autonomous` flag, but a task's
# `mode` already encodes the book's recorded production policy (AGENTS.md
# section 3a; bookfactory/core/production.py compute_mode). The guard adds no
# judgement of its own: it only lets through the one step Book Factory itself
# says continues automatically. A checkpointed book gives the release task
# `wait_for_operator`, so it still asks.

RELEASE_LOOKUP_TIMEOUT = 10  # seconds; loading one book takes well under one
_PROJECT_DIR = Path(__file__).resolve().parents[2]
_BOOK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_DRAFT_RE = re.compile(r"^v[0-9]+$")
_CWD_CHANGE_RE = re.compile(r"\b(cd|pushd|popd)\b")
_NEXT_TASK_CODE = (
    "import json, sys\n"
    "from bookfactory.core import api\n"
    "root = sys.argv[2] or None\n"
    "print(json.dumps(api.next_task(sys.argv[1], root=root, persist=False)))\n"
)


def _plain(word: str) -> bool:
    """A literal word: no substitution, variable or glob."""
    return SUBST not in word and "$" not in word and not any(ch in word for ch in "*?[`")


def _parse_options(words: list[str], value_opts: set[str], flag_opts: set[str]):
    """Split `words` into ({option: [values]}, positionals), or None if unreadable.

    Only exact, full option names are accepted (no argparse abbreviations), so
    nothing can pass for something it is not.
    """
    opts: dict[str, list[str]] = {}
    positional: list[str] = []
    k = 0
    while k < len(words):
        w = words[k]
        if not _plain(w):
            return None
        if w.startswith("-"):
            name, eq, value = w.partition("=")
            if name in flag_opts and not eq:
                opts.setdefault(name, []).append("")
                k += 1
                continue
            if name in value_opts:
                if not eq:
                    if k + 1 >= len(words) or not _plain(words[k + 1]):
                        return None
                    value = words[k + 1]
                    k += 1
                opts.setdefault(name, []).append(value)
                k += 1
                continue
            return None  # --force, an abbreviation, anything unknown
        positional.append(w)
        k += 1
    return opts, positional


def release_step(sub: str, global_words: list[str], rest: list[str]):
    """Parse one release step: (what, book, root, draft) or None if not plain."""
    parsed_global = _parse_options(global_words, {"--root"}, {"--json"})
    if parsed_global is None:
        return None
    g_opts, g_pos = parsed_global
    if g_pos:
        return None
    if sub == "advance":
        parsed = _parse_options(rest, {"--root", "--to", "--by", "--note"}, {"--json"})
        if parsed is None:
            return None
        opts, pos = parsed
        if opts.get("--to") != ["release_ready"]:
            return None
        by = opts.get("--by", [None])[-1]
        if len(opts.get("--by", [])) > 1 or (by is not None and by.strip().lower() in OPERATOR_NAMES):
            return None
        what = "advance"
    else:
        # rest is everything after `cover`: options, the operation, then its args
        parsed = _parse_options(rest, {"--root", "--draft"}, {"--json"})
        if parsed is None:
            return None
        opts, pos = parsed
        if not pos or pos[0] not in ("finalize", "preflight"):
            return None
        what = f"cover {pos[0]}"
        pos = pos[1:]
        if what == "cover preflight" and "--draft" in opts:
            return None
    if len(pos) != 1 or not _BOOK_ID_RE.match(pos[0]) or ".." in pos[0]:
        return None
    drafts = opts.get("--draft", [])
    if len(drafts) > 1 or (drafts and not _DRAFT_RE.match(drafts[0])):
        return None
    roots = set(g_opts.get("--root", []) + opts.get("--root", []))
    if len(roots) > 1 or "" in roots:
        return None
    return what, pos[0], (roots.pop() if roots else None), (drafts[0] if drafts else None)


def lookup_next_task(book: str, root: str | None, context: dict):
    """The book's next task as `bookfactory next --json` gives it, or None on any failure."""
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (str(_PROJECT_DIR), env.get("PYTHONPATH", "")) if p)
        if context.get("bookfactory_root") is not None:
            env["BOOKFACTORY_ROOT"] = context["bookfactory_root"]
        cwd = context.get("cwd")
        if cwd is not None and not os.path.isdir(cwd):
            return None
        proc = subprocess.run([sys.executable, "-c", _NEXT_TASK_CODE, book, root or ""],
                              capture_output=True, text=True, cwd=cwd, env=env,
                              stdin=subprocess.DEVNULL, timeout=RELEASE_LOOKUP_TIMEOUT)
        if proc.returncode != 0:
            return None
        task = json.loads(proc.stdout)
        return task if isinstance(task, dict) else None
    except Exception:
        return None


def task_asks_for(task: dict, what: str, book: str, draft: str | None) -> bool:
    """Whether `task` is exactly the release step `what`, in continue_automatically."""
    if task.get("mode") != "continue_automatically" or task.get("book_id") != book:
        return False
    instructions = task.get("instructions")
    if not isinstance(instructions, str):
        return False
    if what == "advance":
        return (task.get("task_id") == f"{book}-release"
                and task.get("type") == "operator_decision"
                and task.get("gate") == "release_ready"
                and f"bookfactory advance {book} --to release_ready" in instructions)
    if what == "cover finalize":
        match = re.search(rf"bookfactory cover finalize {re.escape(book)} --draft (v[0-9]+)\b",
                          instructions)
        return (task.get("task_id") == f"{book}-cover-finalize"
                and task.get("type") == "assembly"
                and match is not None
                and (draft is None or draft == match.group(1)))
    if what == "cover preflight":
        return (task.get("task_id") == f"{book}-cover-preflight"
                and task.get("type") == "preflight"
                and f"bookfactory cover preflight {book}" in instructions)
    return False


def release_step_decision(sub: str, global_words: list[str], rest: list[str],
                          context: dict | None) -> bool:
    """True only when the release step may run without asking (rule above)."""
    try:
        if context is None:
            return False
        step = release_step("advance" if sub == "advance" else "cover", global_words, rest)
        if step is None:
            return False
        what, book, root, draft = step
        if what != sub:
            return False
        task = lookup_next_task(book, root, context)
        return task is not None and task_asks_for(task, what, book, draft)
    except Exception:
        return False


# -- the go-ahead: what Kieran himself typed this turn --------------------------
#
# Rule (Phase 20, task 20.1). The guard cannot see the chat, but every
# PreToolUse payload names Claude Code's own transcript (`transcript_path`, a
# JSONL file under ~/.claude/projects/, outside the project). A command line
# that would otherwise ask (and so be blocked outside the default mode) gets an
# explicit ALLOW only when ALL of these hold:
#
#  1. The call is from the main session, never a helper: the payload has no
#     `agent_id` and no `agent_type`.
#  2. The newest user entry in the transcript that is not a tool result or a
#     harness note is Kieran's own typed message: `"type": "user"`,
#     `"origin": {"kind": "human"}`, not `isMeta`, not `isSidechain`, no
#     `agentId`, the payload's `sessionId`, at most 60 minutes old. A task
#     notification, a helper's hand-back or any other non-human user entry
#     after it means nothing is authorised.
#  3. The message IS a decision (`parse_decision`): at most 20 words, no "?",
#     no negator anywhere (don't, not, never, no, wait, hold, stop, cancel,
#     later, yet, after, until, unless, before, "only if", any "...n't"); after
#     optional polite leads (ok, okay, yes, yep, great, good, please, "go ahead
#     and", "go on and") it is a list of clauses joined by "," ";" "." "and"
#     "then", each starting with a decision verb (lock, approve, revise,
#     reject, assemble, preflight, finalise/finalize, release/advance, "set
#     [the] policy", "set [the] picture budget"). A clause of bare ids
#     ("approve p014 and p015") continues the one before; "thanks" is ignored.
#     Anything else authorises nothing.
#  4. Every simple command on the line is a plainly written `bookfactory`
#     command (the program word itself, no VAR=value, wrapper, variable,
#     substitution, glob, redirection, pipe or loop), and each is either
#     read-only (status, next, task, validate, list, policy show, pictures
#     show) or an authority command a clause covers (`clause_covers`). All the
#     authority commands name the same book, and a bare "lock" covers one lock.
#  5. Each authority command uses only the options it really has, spelled in
#     full; never `--force`, `--all-passing` or `--autonomous`; signed `--by
#     kieran` where it takes `--by` (advance may be unsigned).
#
# Otherwise the ordinary decision for the line stands; the go-ahead never turns
# a DENY (writes into approved work or the guard's own files) into an allow.
#
# This is a guard against mistakes, not a sandbox against a deliberately
# adversarial agent: a determined agent with a shell has ways round any list of
# write patterns (a script run by name, say). The protections below (the
# transcript folder, `.claude/hooks/`, `.claude/settings*.json`,
# `.claude/state/` are denied to Bash writes and to Edit/Write) stop the
# ordinary slips.

GO_AHEAD_MAX_AGE = 60 * 60  # seconds
GO_AHEAD_CLOCK_SKEW = 60  # a message dated this far in the future still counts
GO_AHEAD_MAX_WORDS = 20
TRANSCRIPT_SCAN_LIMIT = 64 * 1024 * 1024  # bytes read backwards at most
CONFIG_REASON = ("This would change the guard's own files, Claude Code's settings or the "
                 "session transcript (`.claude/hooks/`, `.claude/settings*.json`, "
                 "`.claude/state/`, `~/.claude/projects/`). Claude never does that; Kieran "
                 "changes them himself.")
PATCH_REASON = ("A patch can write any file, including approved work and the guard's own "
                "files, and the guard can't see which. Make the change with the Edit tool "
                "instead, or Kieran applies the patch himself.")

# (positional names, options with a value, flags) - exact names only.
_GO_SPECS = {
    "approve": (("book", "id"), {"--kind", "--draft", "--by", "--note", "--root"},
                {"--json", "--dry-run"}),
    "reject": (("book", "id"), {"--kind", "--draft", "--reason", "--by", "--root"}, {"--json"}),
    "revise": (("book", "id"), {"--kind", "--reason", "--by", "--root"}, {"--json"}),
    "lock": (("what", "book"), {"--version", "--by", "--note", "--root"}, {"--json"}),
    "advance": (("book",), {"--to", "--by", "--note", "--root"}, {"--json"}),
    "assemble": (("book",), {"--out", "--root"}, {"--json"}),
    "preflight": (("book",), {"--root"}, {"--json"}),
    "cover approve": (("book",), {"--draft", "--by", "--root"}, {"--json"}),
    "cover finalize": (("book",), {"--draft", "--root"}, {"--json"}),
    "cover preflight": (("book",), {"--root"}, {"--json"}),
    "policy set": (("book", "mode"), {"--by", "--reason", "--root"}, {"--json"}),
    "pictures set": (("book", "budget"), {"--count", "--by", "--reason", "--root"}, {"--json"}),
}
_GO_SIGNED = {"approve", "reject", "revise", "lock", "cover approve", "policy set",
              "pictures set"}
_READ_ONLY = {"status", "next", "task", "validate", "list", "policy show", "pictures show"}

# the clause verb each command needs
_VERB_OF = {"approve": "approve", "reject": "reject", "revise": "revise", "lock": "lock",
            "assemble": "assemble", "preflight": "preflight", "advance": "release",
            "cover approve": "approve", "cover finalize": "finalize",
            "cover preflight": "preflight", "policy set": "policy", "pictures set": "budget"}
_VERB_WORDS = {"approve": "approve", "lock": "lock", "revise": "revise", "reject": "reject",
               "assemble": "assemble", "preflight": "preflight", "pre-flight": "preflight",
               "finalise": "finalize", "finalize": "finalize", "release": "release",
               "advance": "release"}
_LEADS = {"ok", "okay", "yes", "yep", "great", "good", "please", "also"}
_LEAD_PHRASES = (("go", "ahead", "and"), ("go", "on", "and"))
_COURTESY = {"thanks", "thank", "you", "cheers", "please", "ta"}
_NEGATORS = {"don't", "dont", "not", "never", "no", "nope", "wait", "hold", "stop", "cancel",
             "later", "yet", "after", "until", "unless", "before", "cannot", "without",
             "instead", "except", "but"}
_SEPARATORS = {",", ";", ".", "and", "then", "&"}
_COVER_WORDS = {"cover", "wrap"}
_LOCK_OBJECTS = {"look": "visual", "visual": "visual", "visuals": "visual", "style": "visual",
                 "concept": "concept", "brief": "concept", "voice": "voice",
                 "manuscript": "manuscript"}
# words that name nothing in particular: a clause of only these is "bare"
_FILLER = {"all", "them", "it", "these", "those", "the", "this", "that", "they", "both",
           "pages", "page", "pictures", "picture", "assets", "asset", "drafts", "draft",
           "everything", "ones", "one", "of", "remaining", "rest", "now", "too", "as", "well",
           "in", "for", "to", "a", "an", "please", "each", "every", "latest", "new", "is",
           "interior", "book", "its", "their"}
_ID_WORD_RE = re.compile(r"^(p[0-9]+[a-z]?|[a-z0-9]+([-_][a-z0-9]+)+)$")
_PAGE_ID_RE = re.compile(r"^p[0-9]+[a-z]?$")
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9_'-]*|[?,;.!&]")


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or _PROJECT_DIR)


def transcript_roots() -> list[Path]:
    """Where Claude Code keeps session transcripts."""
    roots = [Path.home() / ".claude" / "projects"]
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    if config:
        roots.append(Path(config) / "projects")
    return roots


def known_books() -> set[str]:
    try:
        return {p.name for p in (project_dir() / "books").iterdir() if p.is_dir()}
    except Exception:
        return set()


def _lines_backwards(path: Path):
    """The file's lines, last first, reading at most TRANSCRIPT_SCAN_LIMIT bytes."""
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        pos = fh.tell()
        buf = b""
        read = 0
        while pos > 0 and read < TRANSCRIPT_SCAN_LIMIT:
            step = min(1 << 16, pos)
            pos -= step
            read += step
            fh.seek(pos)
            buf = fh.read(step) + buf
            parts = buf.split(b"\n")
            buf = parts[0]
            for line in reversed(parts[1:]):
                if line.strip():
                    yield line
        if pos == 0 and buf.strip():
            yield buf


def _is_tool_result(entry: dict) -> bool:
    content = entry.get("message", {}).get("content") if isinstance(entry.get("message"),
                                                                   dict) else None
    if "toolUseResult" in entry:
        return True
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def _typed_text(entry: dict) -> str | None:
    message = entry.get("message")
    if not isinstance(message, dict) or message.get("role", "user") != "user":
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if not isinstance(block, dict) or block.get("type") not in ("text", "image"):
                return None
            if block.get("type") == "text":
                if not isinstance(block.get("text"), str):
                    return None
                texts.append(block["text"])
        return "\n".join(texts) if texts else None
    return None


def operator_message(payload: dict, now=None) -> str | None:
    """Kieran's latest typed message this turn, from the transcript, or None."""
    try:
        from datetime import datetime, timezone
        if "agent_id" in payload or "agent_type" in payload:
            return None  # a helper: never gets a go-ahead
        session_id = payload.get("session_id")
        path_text = payload.get("transcript_path")
        if not isinstance(session_id, str) or not session_id \
                or not isinstance(path_text, str) or not path_text.startswith("/"):
            return None
        path = Path(path_text)
        real = Path(os.path.realpath(path))
        if path.is_symlink() or not real.is_file() or real.suffix != ".jsonl":
            return None
        roots = [Path(os.path.realpath(r)) for r in transcript_roots()]
        if not any(real.is_relative_to(r) for r in roots) or "subagents" in real.parts:
            return None
        for line in _lines_backwards(real):
            try:
                entry = json.loads(line)
            except ValueError:
                return None
            if not isinstance(entry, dict) or entry.get("type") != "user":
                continue
            if _is_tool_result(entry):
                continue
            origin = entry.get("origin")
            if entry.get("isSidechain") or entry.get("agentId") \
                    or entry.get("isCompactSummary"):
                return None
            if origin is None and entry.get("isMeta"):
                continue  # a harness note inside the turn (skill text, image note)
            if not isinstance(origin, dict) or origin.get("kind") != "human" \
                    or entry.get("isMeta") or entry.get("sessionId") != session_id:
                return None  # the newest turn wasn't started by Kieran typing
            stamp = entry.get("timestamp")
            if not isinstance(stamp, str):
                return None
            recorded = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if recorded.tzinfo is None:
                return None
            age = ((now or datetime.now(timezone.utc)) - recorded).total_seconds()
            if age < -GO_AHEAD_CLOCK_SKEW or age > GO_AHEAD_MAX_AGE:
                return None
            return _typed_text(entry)
        return None
    except Exception:
        return None


# -- reading the message as a decision ------------------------------------------

class Clause:
    def __init__(self, verb: str):
        self.verb = verb
        self.words: list[str] = []

    @property
    def cover(self) -> bool:
        return bool(_COVER_WORDS & set(self.words))

    def drafts(self) -> set[str]:
        return {w for w in self.words if _DRAFT_RE.match(w)}


def _message_tokens(text: str) -> list[str]:
    text = text.lower().replace("’", "'").replace("‘", "'")
    return _WORD_RE.findall(text)


def parse_decision(text: str) -> tuple[list[Clause], set[str]] | None:
    """(clauses, book ids typed) when the whole message is a decision, else None."""
    if not isinstance(text, str) or "?" in text:
        return None
    tokens = _message_tokens(text.strip())
    words = [t for t in tokens if t not in _SEPARATORS and t not in "?!"]
    if not words or len(words) > GO_AHEAD_MAX_WORDS:
        return None
    joined = " " + " ".join(words) + " "
    if _NEGATORS & set(words) or any(w.endswith("n't") for w in words) \
            or " do not " in joined or " only if " in joined:
        return None
    books = set(words) & known_books()

    # split into segments at separators
    segments: list[list[str]] = [[]]
    for t in tokens:
        if t in _SEPARATORS or t == "!":
            segments.append([])
        else:
            segments[-1].append(t)
    segments = [s for s in segments if s]

    def strip_leads(seg: list[str]) -> list[str]:
        changed = True
        while seg and changed:
            changed = False
            if seg[0] in _LEADS:
                seg, changed = seg[1:], True
            for phrase in _LEAD_PHRASES:
                if tuple(seg[:len(phrase)]) == phrase:
                    seg, changed = seg[len(phrase):], True
        return seg

    def verb_of(seg: list[str]) -> tuple[str, list[str]] | None:
        if not seg:
            return None
        if seg[0] in _VERB_WORDS:
            return _VERB_WORDS[seg[0]], seg[1:]
        if seg[0] == "set":
            rest = seg[1:]
            if rest[:1] == ["the"]:
                rest = rest[1:]
            if rest[:1] == ["policy"]:
                return "policy", rest[1:]
            if rest[:2] in (["picture", "budget"], ["pictures", "budget"]):
                return "budget", rest[2:]
        return None

    clauses: list[Clause] = []
    for n, seg in enumerate(segments):
        # leads ("ok, please ...") only before the first clause and at a clause's start
        seg = strip_leads(seg)
        if not seg:
            if n == 0 or clauses:
                continue
            return None
        found = verb_of(seg)
        if found is not None:
            clause = Clause(found[0])
            clause.words = found[1]
            clauses.append(clause)
            continue
        if all(w in _COURTESY for w in seg):
            continue
        if clauses and all(_ID_WORD_RE.match(w) or _DRAFT_RE.match(w) or w in books
                           for w in seg):
            clauses[-1].words += seg  # "approve p014 and p015"
            continue
        return None  # a clause that isn't a decision: the whole message counts for nothing
    return (clauses, books) if clauses else None


def parse_authority_command(args: list[str]):
    """(what, positionals, options) for a plainly written authority command, or None."""
    k, global_words = 0, []
    while k < len(args) and args[k].startswith("-"):
        if args[k] == "--root" and k + 1 < len(args):
            global_words += args[k:k + 2]
            k += 2
            continue
        global_words.append(args[k])
        k += 1
    if k >= len(args):
        return None
    parsed = _parse_options(global_words, {"--root"}, {"--json"})
    if parsed is None or parsed[1]:
        return None
    roots = parsed[0].get("--root", [])
    sub, rest = args[k], args[k + 1:]
    what = sub
    if sub in ("cover", "policy", "pictures"):
        j = 0
        while j < len(rest) and rest[j].startswith("-"):
            if rest[j] == "--root" and j + 1 < len(rest):
                roots.append(rest[j + 1])
                j += 2
            elif rest[j] == "--json" or rest[j].startswith("--root="):
                if rest[j].startswith("--root="):
                    roots.append(rest[j].split("=", 1)[1])
                j += 1
            else:
                return None
        if j >= len(rest):
            return None
        what, rest = f"{sub} {rest[j]}", rest[j + 1:]
    if what in _READ_ONLY:
        return what, {}, {}
    if what not in _GO_SPECS:
        return None
    names, value_opts, flag_opts = _GO_SPECS[what]
    parsed = _parse_options(rest, value_opts, flag_opts)
    if parsed is None:
        return None
    opts, positional = parsed
    if len(positional) != len(names):
        return None
    if any(len(v) > 1 for v in opts.values()):
        return None
    roots += opts.get("--root", [])
    if len(set(roots)) > 1:
        return None
    pos = dict(zip(names, positional))
    if not _BOOK_ID_RE.match(pos["book"]) or ".." in pos["book"]:
        return None
    return what, pos, {name: v[0] for name, v in opts.items()}


def clause_covers(clause: Clause, what: str, pos: dict, opts: dict) -> str | None:
    """None if `clause` doesn't authorise this command; else "named", "bare" or "ok"."""
    if clause.verb != _VERB_OF[what]:
        return None
    words = clause.words
    drafts = clause.drafts()
    if what in ("approve", "reject", "revise"):
        if clause.cover:
            return None  # "approve cover v1" is the full-wrap cover, not a page
        item = pos["id"].lower()
        if drafts and opts.get("--draft") not in drafts:
            return None
        others = [w for w in words if not _DRAFT_RE.match(w) and w not in known_books()]
        if item in others:
            return "named"
        if all(w in _FILLER for w in others):
            # a bare "approve" / "revise": never cover artwork
            return None if item.startswith("cover") else "bare"
        return None
    if what in ("cover approve", "cover finalize"):
        if what == "cover approve" and not clause.cover:
            return None
        if drafts and opts.get("--draft") not in drafts:
            return None
        return "ok"
    if what == "cover preflight":
        return "ok" if clause.cover else None
    if what == "preflight":
        return None if clause.cover else "ok"
    if what == "assemble":
        return "ok"
    if what == "advance":
        return "ok" if opts.get("--to") == "release_ready" else None
    if what == "lock":
        objects = {_LOCK_OBJECTS[w] for w in words if w in _LOCK_OBJECTS}
        if objects:
            return "named" if pos["what"] in objects else None
        others = [w for w in words if w not in known_books()]
        return "bare" if all(w in _FILLER for w in others) else None
    if what == "policy set":
        text = " ".join(words).replace("visual checkpoint", "visual_checkpoint")
        named = set(text.split()) & {"checkpointed", "visual_checkpoint", "autonomous"}
        return "ok" if named == {pos["mode"]} else None
    if what == "pictures set":
        text = " ".join(words).replace("chapter openers", "chapter_openers")
        named = set(text.split()) & {"chapter_openers", "limit", "unlimited"}
        if named != {pos["budget"]}:
            return None
        if "--count" in opts and opts["--count"] not in words:
            return None
        return "ok"
    return None


def go_ahead_line(raw: str, message: str) -> bool:
    """Whether Kieran's `message` authorises the whole command line `raw` (rule above)."""
    try:
        decision = parse_decision(message)
        if decision is None:
            return False
        clauses, books = decision
        nested: list[str] = []
        heredocs: list[tuple[int, str]] = []
        toks = tokenize(raw, nested, heredocs)
        if nested or heredocs or any(t.kind == "redir" for t in toks):
            return False
        if any(t.kind == "op" and t.text not in (";", "&&") for t in toks):
            return False  # pipes, ||, &, subshells: not a plain list of commands
        authorised: list[tuple[str, dict, str]] = []
        for cmd in split_simple(toks, heredocs):
            if not cmd.words or cmd.words[0] != "bookfactory" \
                    or not all(_plain(w) for w in cmd.words):
                return False
            parsed = parse_authority_command(cmd.words[1:])
            if parsed is None:
                return False
            what, pos, opts = parsed
            if what in _READ_ONLY:
                continue
            by = opts.get("--by")
            if what in _GO_SIGNED or by is not None:
                if by is None or by.strip().lower() not in OPERATOR_NAMES:
                    return False
            if books and pos["book"] not in books:
                return False
            kinds = [c for c in (clause_covers(cl, what, pos, opts) for cl in clauses) if c]
            if not kinds:
                return False
            kind = "named" if "named" in kinds else kinds[0]
            authorised.append((what, pos, kind))
        if not authorised:
            return False
        if len({pos["book"] for _, pos, _ in authorised}) != 1:
            return False  # one book per go-ahead
        bare_locks = [a for a in authorised if a[0] == "lock" and a[2] == "bare"]
        if bare_locks and sum(1 for a in authorised if a[0] == "lock") > 1:
            return False  # a bare "lock" covers exactly one lock
        return True
    except Exception:
        return False


def _quote(prompt: str) -> str:
    text = " ".join(prompt.split())
    return text if len(text) <= 80 else text[:77] + "..."


# -- tokenizer ---------------------------------------------------------------

class Tok:
    """A shell token: a word, an operator (`;`, `|`, `&&` ...) or a redirection."""

    __slots__ = ("kind", "text", "quoted")

    def __init__(self, kind: str, text: str, quoted: bool = False):
        self.kind, self.text, self.quoted = kind, text, quoted

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Tok({self.kind!r}, {self.text!r})"


SUBST = "\x00SUBST\x00"  # placeholder left in a word where $(...) or `...` was


def _match_paren(s: str, i: int) -> int:
    """Index just after the `)` closing the `(` at s[i-1]. Quote-aware, lenient."""
    depth, n = 1, len(s)
    while i < n:
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            j = s.find("'", i + 1)
            i = n if j < 0 else j + 1
            continue
        if c == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == "\\" else 1
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def tokenize(s: str, nested: list[str], heredocs: list[tuple[int, str]]):
    """Split shell text into tokens.

    Command substitutions (`$(...)`, backticks, `<(...)`, `>(...)`) are cut
    out into `nested` so the caller can analyse them as commands of their own.
    Heredoc bodies go into `heredocs` as (token index of the `<<`, body).
    """
    toks: list[Tok] = []
    i, n = 0, len(s)
    word: list[str] = []
    in_word = False
    quoted = False
    pending_heredocs: list[tuple[int, str, bool]] = []  # (tok index, delimiter, strip tabs)

    def flush():
        nonlocal word, in_word, quoted
        if in_word:
            toks.append(Tok("word", "".join(word), quoted))
        word, in_word, quoted = [], False, False

    while i < n:
        c = s[i]
        if c == "\\":
            if i + 1 < n and s[i + 1] == "\n":  # line continuation
                i += 2
                continue
            if i + 1 < n:
                word.append(s[i + 1])
            in_word = True
            i += 2
            continue
        if c == "'":
            j = s.find("'", i + 1)
            j = n if j < 0 else j
            word.append(s[i + 1:j])
            in_word = quoted = True
            i = j + 1
            continue
        if c == '"':
            i += 1
            in_word = quoted = True
            while i < n and s[i] != '"':
                d = s[i]
                if d == "\\" and i + 1 < n:
                    if s[i + 1] == "\n":
                        i += 2
                        continue
                    if s[i + 1] in '"\\$`':
                        word.append(s[i + 1])
                        i += 2
                        continue
                    word.append(d)
                    i += 1
                    continue
                if d == "$" and i + 1 < n and s[i + 1] == "(":
                    end = _match_paren(s, i + 2)
                    nested.append(s[i + 2:end - 1])
                    word.append(SUBST)
                    i = end
                    continue
                if d == "`":
                    j = s.find("`", i + 1)
                    j = n if j < 0 else j
                    nested.append(s[i + 1:j])
                    word.append(SUBST)
                    i = j + 1
                    continue
                word.append(d)
                i += 1
            i += 1
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "(":
            end = _match_paren(s, i + 2)
            nested.append(s[i + 2:end - 1])
            word.append(SUBST)
            in_word = True
            i = end
            continue
        if c == "$" and i + 1 < n and s[i + 1] == "'":  # $'...' ANSI-C string
            j = i + 2
            buf = []
            while j < n and s[j] != "'":
                if s[j] == "\\" and j + 1 < n:
                    esc = s[j + 1]
                    buf.append({"n": "\n", "t": "\t"}.get(esc, esc))
                    j += 2
                    continue
                buf.append(s[j])
                j += 1
            word.append("".join(buf))
            in_word = quoted = True
            i = j + 1
            continue
        if c == "`":
            j = s.find("`", i + 1)
            j = n if j < 0 else j
            nested.append(s[i + 1:j])
            word.append(SUBST)
            in_word = True
            i = j + 1
            continue
        if c in "<>" and i + 1 < n and s[i + 1] == "(" and not in_word:
            end = _match_paren(s, i + 2)
            nested.append(s[i + 2:end - 1])
            toks.append(Tok("word", SUBST))
            i = end
            continue
        if c == "#" and not in_word:  # comment to end of line
            j = s.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "\n":
            flush()
            toks.append(Tok("op", ";"))
            i += 1
            if pending_heredocs:
                for idx, delim, strip in pending_heredocs:
                    body_lines = []
                    while i < n:
                        j = s.find("\n", i)
                        line = s[i:] if j < 0 else s[i:j]
                        i = n if j < 0 else j + 1
                        check = line.lstrip("\t") if strip else line
                        if check == delim:
                            break
                        body_lines.append(line)
                    heredocs.append((idx, "\n".join(body_lines)))
                pending_heredocs = []
            continue
        if c in " \t\r":
            flush()
            i += 1
            continue
        if c in ";&|()":
            flush()
            two = s[i:i + 2]
            if c == "&" and s[i:i + 3] == "&>>":
                toks.append(Tok("redir", ">>"))
                i += 3
                continue
            if two == "&>":
                toks.append(Tok("redir", ">"))
                i += 2
                continue
            if two in ("&&", "||", ";;", "|&"):
                toks.append(Tok("op", two))
                i += 2
                continue
            toks.append(Tok("op", c))
            i += 1
            continue
        if c in "<>":
            # a word made only of digits right before is a file descriptor (2>...)
            if in_word and "".join(word).isdigit() and not quoted:
                word, in_word = [], False
            flush()
            if s[i:i + 3] == "<<<":
                toks.append(Tok("redir", "<<<"))
                i += 3
                continue
            if s[i:i + 2] == "<<":
                strip = s[i:i + 3] == "<<-"
                i += 3 if strip else 2
                while i < n and s[i] in " \t":
                    i += 1
                j = i
                while j < n and s[j] not in " \t\n;&|<>()":
                    j += 1
                delim = s[i:j].strip("'\"").replace("\\", "")
                toks.append(Tok("redir", "<<"))
                pending_heredocs.append((len(toks) - 1, delim, strip))
                i = j
                continue
            op = c
            i += 1
            if i < n and s[i] in ">|&" and c == ">":
                op += s[i] if s[i] == ">" else ""
                i += 1
            elif i < n and s[i] in ">&" and c == "<":
                i += 1
            if op.startswith(">") and s[i - 1:i] == "&":
                j = i
                while j < n and s[j] in " \t":
                    j += 1
                if j < n and (s[j].isdigit() or s[j] == "-"):
                    # >&2 style duplication: no file involved
                    while j < n and (s[j].isdigit() or s[j] == "-"):
                        j += 1
                    i = j
                    continue
                # otherwise `>& file` sends output to a file
            toks.append(Tok("redir", op))
            continue
        word.append(c)
        in_word = True
        i += 1
    flush()
    return toks


class Simple:
    """One simple command: its words, redirections and any heredoc/here-string."""

    def __init__(self):
        self.words: list[str] = []
        self.redirs: list[tuple[str, str]] = []
        self.stdin_text: str | None = None
        self.piped_in = False
        self.run_by_other = False  # run by find -exec / xargs, not by the shell


def split_simple(toks: list[Tok], heredocs: list[tuple[int, str]]) -> list[Simple]:
    bodies = dict(heredocs)
    cmds: list[Simple] = []
    cur = Simple()
    k = 0
    piped = False
    while k < len(toks):
        t = toks[k]
        if t.kind == "op":
            if cur.words or cur.redirs:
                cmds.append(cur)
            cur = Simple()
            piped = t.text in ("|", "|&")
            cur.piped_in = piped
            k += 1
            continue
        if t.kind == "redir":
            target = toks[k + 1].text if k + 1 < len(toks) and toks[k + 1].kind == "word" else ""
            if t.text == "<<":
                cur.stdin_text = bodies.get(k, "")
            elif t.text == "<<<":
                cur.stdin_text = target
            else:
                cur.redirs.append((t.text, target))
            k += 2 if target else 1
            continue
        cur.words.append(t.text)
        k += 1
    if cur.words or cur.redirs:
        cmds.append(cur)
    return cmds


# -- path checks -------------------------------------------------------------

_PROTECTED_RE = re.compile(
    r"(^|/)approved(/|$)"            # pages/approved/, assets/approved/, any approved/ dir
    r"|(^|/)cover/drafts(/|$)"       # the approved cover lives among cover/drafts/*.pdf
)
_PROTECTED_TEXT_RE = re.compile(r"(^|[/'\"\s])approved/|/approved\b|cover/drafts")


def is_protected(path: str, cwd_protected: bool = False) -> bool:
    if not path or path == SUBST:
        return False
    p = path.replace(SUBST, "")
    if p.startswith("-"):
        return False
    if "=" in p and not p.startswith(("/", ".")) and "/" in p.split("=", 1)[1]:
        p = p.split("=", 1)[1]  # --option=path
    if _PROTECTED_RE.search(p):
        if "cover/drafts" in p and "approved" not in p:
            tail = p.split("cover/drafts", 1)[1].lstrip("/")
            # the directory itself, a glob, or a PDF inside it
            return tail == "" or tail.lower().endswith(".pdf") or any(ch in tail for ch in "*?[")
        return True
    if cwd_protected and not p.startswith(("/", "~")):
        return True
    return False


# The guard's own files, Claude Code's settings and the session transcripts.
_CONFIG_RE = re.compile(
    r"(^|/)\.claude/+(hooks|state|projects)(/|$)"   # hooks, old slip folder, transcripts
    r"|(^|/)\.claude/+settings[^/]*\.json$"          # settings.json, settings.local.json
    r"|(^|/)\.claude/*$"                             # the .claude folder itself
)
_CONFIG_TEXT_RE = re.compile(r"\.claude|go-ahead|settings(\.local)?\.json|guard-authority"
                             r"|\.jsonl\b")
_CONFIG_NAMES = {".claude", "hooks", "state", "projects", "settings.json",
                 "settings.local.json", "guard-authority.py", "go-ahead.json"}


def _path_text(path: str) -> str:
    p = path.replace(SUBST, "") if path else ""
    if p.startswith("-") and "=" in p:
        p = p.split("=", 1)[1]  # --option=path
    if p.startswith("-"):
        return ""
    return os.path.expanduser(p) if p.startswith("~") else p


def is_config_path(path: str, extra_dirs: tuple[str, ...] = ()) -> bool:
    """Whether `path` is (in) the guard's own files, settings or the transcripts."""
    p = _path_text(path)
    if not p:
        return False
    norm = os.path.normpath(p)
    if _CONFIG_RE.search(p) or _CONFIG_RE.search(norm):
        return True
    if norm.startswith("/"):
        for root in [str(r) for r in transcript_roots()] + list(extra_dirs):
            root = os.path.normpath(root)
            if norm == root or norm.startswith(root + "/"):
                return True
    # a glob that could reach them: .claude/st*, .cl*/hooks ...
    return any(ch in p for ch in "*?[") and any(
        s in p for s in (".cl", "hook", "sett", "stat", "proj"))


def is_config_parent(path: str) -> bool:
    """Whether `path` is a folder that holds `.claude` or the transcripts (the project,
    home, `~/.claude`), where a copied or moved folder could land as one of them."""
    p = _path_text(path)
    if not p:
        return False
    norm = os.path.normpath(p)
    if norm in (".", "..") or basename(norm) == ".claude":
        return True
    if not norm.startswith("/"):
        return False
    home = os.path.normpath(str(Path.home()))
    return norm in ("/", home, os.path.normpath(str(project_dir()))) \
        or norm == os.path.join(home, ".claude")


def _args(words: list[str]) -> list[str]:
    """Non-option words (after `--` everything counts)."""
    out, rest = [], False
    for w in words:
        if rest:
            out.append(w)
        elif w == "--":
            rest = True
        elif not w.startswith("-") or w == "-":
            out.append(w)
    return out


_PY_WRITE_RE = re.compile(
    r"open\s*\([^)]*['\"][rbtx]*[wax+][rbtwax+]*['\"]"
    r"|mode\s*=\s*['\"][rbt]*[wax+]"
    r"|write_text|write_bytes|\.touch\s*\(|unlink|rmtree|os\.remove|os\.rename|os\.replace"
    r"|\.rename\s*\(|\.replace\s*\(|chmod|chown|shutil\.(copy|move)|copyfile|truncate"
    r"|\bunlink\b|\brename\b|File\.write|fs\.write|writeFile|rmSync|unlinkSync"
    r"|open\s*\(?\s*[\w$]*\s*,\s*['\"]\s*[+>]"     # perl: open(F, ">path")
    r"|print[^;\n]*>\s*['\"]"                        # awk: print "x" > "path"
)
# more ways code can change a file, used only for the guard's own files
_CONFIG_WRITE_RE = re.compile(r"\bjson\.dump\b|makedirs|mkdir|syswrite|\bsystem\s*\(|subprocess"
                              r"|os\.popen|copytree|\bexec\b|\beval\b|symlink|\blink\b")


def code_writes_protected(code: str) -> bool:
    return bool(_PROTECTED_TEXT_RE.search(code) and _PY_WRITE_RE.search(code))


def code_writes_config(code: str) -> bool:
    return bool(_CONFIG_TEXT_RE.search(code)
                and (_PY_WRITE_RE.search(code) or _CONFIG_WRITE_RE.search(code)))


def code_calls_authority(code: str) -> bool:
    return "bookfactory" in code and bool(_AUTHORITY_RE.search(code))


# -- command analysis ---------------------------------------------------------

WRAPPERS = {"sudo", "doas", "nohup", "time", "command", "builtin", "exec", "nice", "ionice",
            "stdbuf", "setsid", "chronic", "unbuffer", "caffeinate", "!", "{", "}", "(",
            "then", "do", "else", "elif", "if", "while", "until", "coproc"}
# wrappers whose first non-option argument is not the command (timeout 5 cmd)
WRAPPERS_WITH_ARG = {"timeout"}
WRAPPER_OPTS_WITH_VALUE = {
    "sudo": ("-u", "-g", "-C", "-h", "-p", "-r", "-t", "-U", "-D", "--user", "--group"),
    "doas": ("-u", "-C"),
    "nice": ("-n", "--adjustment"),
    "ionice": ("-c", "-n", "-p", "-P", "-u"),
    "timeout": ("-s", "-k", "--signal", "--kill-after"),
    "stdbuf": ("-i", "-o", "-e"),
    "exec": ("-a",),
}
RUNNERS = {"uv", "poetry", "pdm", "hatch", "pipx", "pipenv", "conda", "micromamba", "rye"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "busybox"}
PY_RE = re.compile(r"^(python|pypy)[0-9.]*$")
OTHER_INTERPRETERS = {"perl", "ruby", "node", "nodejs", "deno", "php"}
# commands that only look at a word called bookfactory, never run it
LOOKS_ONLY = {"cat", "ls", "less", "more", "head", "tail", "file", "which", "type", "grep",
              "egrep", "rg", "git", "wc", "stat", "sha256sum", "md5sum", "echo", "printf",
              "cd", "pushd", "find", "du", "tree", "realpath", "readlink", "pip", "pip3",
              "diff", "whereis", "man"}
# commands that change files, when run by `find -exec` over approved material
FIND_WRITERS = {"rm", "rmdir", "unlink", "mv", "cp", "chmod", "chown", "chgrp", "touch",
                "truncate", "shred", "sed", "gsed", "perl", "tee", "dd", "ln", "install",
                "sh", "bash", "zsh", "python", "python3"}
_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?\+?=")


def basename(w: str) -> str:
    return w.rstrip("/").rsplit("/", 1)[-1]


def is_bookfactory_word(w: str) -> bool:
    b = basename(w)
    if b == "bookfactory":
        return True
    return w.endswith(("bookfactory/cli/main.py", "bookfactory/__main__.py"))


def strip_wrappers(words: list[str]) -> list[str]:
    """Drop leading assignments and wrapper commands (env, sudo, timeout, uv run ...)."""
    w = list(words)
    changed = True
    while w and changed:
        changed = False
        head = basename(w[0])
        if _ASSIGN_RE.match(w[0]):
            w = w[1:]
            changed = True
        elif head == "env":
            w = w[1:]
            while w and (w[0].startswith("-") or _ASSIGN_RE.match(w[0])):
                if w[0] in ("-u", "--unset", "-C", "--chdir", "-S", "--split-string"):
                    if w[0] in ("-S", "--split-string") and len(w) > 1:
                        w = w[1].split() + w[2:]
                        continue
                    w = w[2:]
                else:
                    w = w[1:]
            changed = True
        elif head in WRAPPERS or head in WRAPPERS_WITH_ARG:
            w = w[1:]
            while w and w[0].startswith("-"):
                opt = w[0]
                w = w[1:]
                # sudo -u user, nice -n 5, ionice -c 2, timeout -s KILL, stdbuf -o L
                if opt in WRAPPER_OPTS_WITH_VALUE.get(head, ()) and w:
                    w = w[1:]
            if head in WRAPPERS_WITH_ARG and w:
                w = w[1:]  # the duration
            changed = True
        elif head in RUNNERS and len(w) > 1:
            rest = w[1:]
            while rest and rest[0].startswith("-"):
                rest = rest[1:]
            if rest and rest[0] in ("run", "exec"):
                rest = rest[1:]
                while rest and rest[0].startswith("-"):
                    rest = rest[1:]
                w = rest
                changed = True
    return w


def analyze_bookfactory_args(args: list[str], shown: str = "bookfactory",
                             context: dict | None = None):
    """Decision for the arguments that follow the bookfactory program.

    `context` is given only when `bookfactory` is plainly the program being run
    (see `Analyzer.release_context`); without it the release steps always ask.
    """
    k = 0
    while k < len(args):
        a = args[k]
        if a == "--":
            k += 1
            continue
        if a.startswith("--r") and "=" not in a and "--root".startswith(a.split("=")[0]):
            k += 2
            continue
        if a.startswith("-"):
            k += 1
            continue
        break
    if k >= len(args):
        return ALLOW, ""
    sub = args[k]
    rest = args[k + 1:]
    if SUBST in sub or "$" in sub or any(ch in sub for ch in "*?["):
        return ASK, (f"This runs `{shown}` with a subcommand the guard can't read "
                     f"(`{sub.replace(SUBST, '$(...)')}`). It might need the operator's "
                     "authority. Kieran must confirm.")
    if sub in OPERATOR_ONLY:
        reason = ask_reason(f"bookfactory {sub}", OPERATOR_ONLY[sub])
        if sub in AUTONOMOUS_OK:
            return autonomous_decision(sub, rest, reason)
        return ASK, reason
    if sub == "advance":
        if any(r.startswith("--f") and "--force".startswith(r.split("=")[0]) for r in rest):
            return ASK, ask_reason("bookfactory advance --force", ADVANCE_FORCE)
        if release_step_decision("advance", args[:k], rest, context):
            return ALLOW, ""
        return ASK, ask_reason("bookfactory advance", NEEDS_AUTHORITY["advance"])
    if sub in NEEDS_AUTHORITY:
        return ASK, ask_reason(f"bookfactory {sub}", NEEDS_AUTHORITY[sub])
    if sub in ("policy", "cover", "pictures"):
        # The operation is the first word that is neither an option nor an
        # option's value: `cover --root X finalize` must read `finalize`, not
        # `X`. An option before the operation that the guard can't place asks.
        op = None
        k = 0
        while k < len(rest):
            r = rest[k]
            if not r.startswith("-"):
                op = r
                break
            if r in ("--root", "--r", "--ro", "--roo"):
                k += 2
                continue
            if r == "--json" or r.split("=", 1)[0] in ("--root", "--r", "--ro", "--roo"):
                k += 1
                continue
            return ASK, (f"This runs `bookfactory {sub}` with an option (`{r}`) before its "
                         "subcommand that the guard can't place. It might need the "
                         "operator's authority. Kieran must confirm.")
        if op is None:
            return ALLOW, ""
        if SUBST in op or "$" in op:
            return ASK, (f"This runs `bookfactory {sub}` with a subcommand the guard can't "
                         "read. It might need the operator's authority. Kieran must confirm.")
        if sub == "policy" and op == "set":
            return ASK, ask_reason("bookfactory policy set", POLICY_SET)
        if sub == "pictures" and op == "set":
            return ASK, ask_reason("bookfactory pictures set", PICTURES_SET)
        if sub == "cover" and op in COVER_AUTHORITY:
            reason = ask_reason(f"bookfactory cover {op}", COVER_AUTHORITY[op])
            if f"cover {op}" in AUTONOMOUS_OK:
                return autonomous_decision(f"cover {op}", rest, reason)
            if op in ("finalize", "preflight") and release_step_decision(
                    f"cover {op}", args[:k], rest, context):
                return ALLOW, ""
            return ASK, reason
    return ALLOW, ""


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MAX_LOOP_RUNS = 64  # more combinations than this: leave the variable unread (asks)
_LOOP_OPENERS = {"for", "while", "until", "select"}
_KEYWORD_PREFIX = {"do", "then", "else", "elif", "{", "(", "!"}


def _keyword(words: list[str]) -> tuple[str, int]:
    """The first word after any `do`/`then`/`{` ..., and its index."""
    k = 0
    while k < len(words) and words[k] in _KEYWORD_PREFIX:
        k += 1
    return (words[k], k) if k < len(words) else ("", k)


def _loop_var_reassigned(name: str, raw: str) -> bool:
    """Whether the loop variable might be changed inside the command (then don't expand)."""
    return bool(re.search(rf"(^|[^A-Za-z0-9_$]){name}(\[[^]]*\])?\+?=", raw)
                or re.search(r"\b(read|declare|typeset|local|export|mapfile|readarray|getopts"
                             r"|let|unset)\b|printf\s+-v", raw))


def _substitute(word: str, name: str, value: str) -> str:
    return re.sub(rf"\$\{{{name}\}}|\${name}(?![A-Za-z0-9_])", lambda _m: value, word)


class Analyzer:
    def __init__(self, raw: str, cwd: str | None, config_dirs: tuple[str, ...] = ()):
        self.raw = raw
        self.decision = ALLOW
        self.reason = ""
        self.session_cwd = cwd
        self.config_dirs = config_dirs  # the transcript's folder, from the payload
        # where the shell is now (changed by cd); None once the guard can't tell
        self.cwd = os.path.normpath(cwd) if cwd and cwd.startswith("/") else None
        self.cwd_protected = bool(cwd and is_protected(cwd.rstrip("/") + "/"))
        self.cwd_config = bool(cwd and self.is_config(cwd.rstrip("/") + "/"))

    def is_config(self, path: str) -> bool:
        return is_config_path(path, self.config_dirs)

    def release_context(self, cmd: Simple, words: list[str]) -> dict | None:
        """Where a plainly-run `bookfactory` would find its books, or None.

        None (so the release steps ask) unless everything before the program
        is a literal VAR=value assignment - no wrapper such as sudo, env, xargs
        - and nothing anywhere in the command changes directory. A literal
        BOOKFACTORY_ROOT assignment is honoured, as the program would honour it.
        """
        if cmd.run_by_other or _CWD_CHANGE_RE.search(self.raw):
            return None
        prefix = cmd.words[:len(cmd.words) - len(words)]
        context: dict = {"cwd": self.session_cwd, "bookfactory_root": None}
        for w in prefix:
            if not _ASSIGN_RE.match(w) or not _plain(w):
                return None
            name, _, value = w.partition("=")
            if name == "BOOKFACTORY_ROOT":
                context["bookfactory_root"] = value
            elif name.rstrip("+") == "BOOKFACTORY_ROOT" or name == "PWD":
                return None
        return context

    def note(self, decision: str, reason: str) -> None:
        if _RANK[decision] > _RANK[self.decision]:
            self.decision, self.reason = decision, reason

    # entry point for any piece of shell text
    def shell(self, text: str, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            self.note(ASK, UNREADABLE_REASON)
            return
        nested: list[str] = []
        heredocs: list[tuple[int, str]] = []
        toks = tokenize(text, nested, heredocs)
        for inner in nested:
            self.shell(inner, depth + 1)
        # `for NAME in literal words; do ...; done`: a `$NAME` inside the loop
        # is read once per listed value, and the strictest answer stands.
        # Anything else the guard can't resolve stays unread (and so asks).
        loops: list[tuple[str, list[str] | None] | None] = []
        for cmd in split_simple(toks, heredocs):
            key, k = _keyword(cmd.words)
            if key == "done" and loops:
                loops.pop()
            if key in _LOOP_OPENERS:
                binding = None
                w = cmd.words[k:]
                if key == "for" and len(w) >= 4 and w[2] == "in" and _NAME_RE.match(w[1]):
                    values = w[3:]
                    ok = all(_plain(v) and v for v in values) \
                        and not _loop_var_reassigned(w[1], self.raw)
                    binding = (w[1], values if ok else None)
                loops.append(binding)
            self.simple_expanded(cmd, depth, [b for b in loops if b is not None])

    def simple_expanded(self, cmd: Simple, depth: int, loops) -> None:
        text = " ".join(cmd.words + [t for _, t in cmd.redirs])
        used, seen = [], set()
        for name, values in reversed(loops):  # the innermost loop's variable wins
            if name in seen:
                continue
            seen.add(name)
            if values is not None and re.search(rf"\$\{{{name}\}}|\${name}(?![A-Za-z0-9_])",
                                                text):
                used.append((name, values))
        runs = 1
        for _, values in used:
            runs *= len(values)
        if not used or runs > MAX_LOOP_RUNS:
            self.simple(cmd, depth)
            return
        combos: list[dict[str, str]] = [{}]
        for name, values in used:
            combos = [{**c, name: v} for c in combos for v in values]
        for combo in combos:
            copy = Simple()
            copy.stdin_text, copy.piped_in = cmd.stdin_text, cmd.piped_in
            copy.run_by_other = cmd.run_by_other

            def sub(word: str) -> str:
                for name, value in combo.items():
                    word = _substitute(word, name, value)
                return word
            copy.words = [sub(w) for w in cmd.words]
            copy.redirs = [(op, sub(t)) for op, t in cmd.redirs]
            self.simple(copy, depth)

    def _resolve(self, path: str) -> str | None:
        """`path` as an absolute path from where the shell is now, or None."""
        p = path.replace(SUBST, "")
        if p.startswith("-") and "=" in p:
            p = p.split("=", 1)[1]
        if not p or p.startswith(("-", "~", "$")):
            return None
        if p.startswith("/"):
            return os.path.normpath(p)
        return os.path.normpath(os.path.join(self.cwd, p)) if self.cwd else None

    def deny_if(self, path: str) -> None:
        if not path or path == SUBST:
            return
        resolved = self._resolve(path)
        relative = not path.replace(SUBST, "").startswith(("/", "~"))
        if is_protected(path, self.cwd_protected and self.cwd is None) \
                or (resolved is not None and is_protected(resolved)):
            self.note(DENY, APPROVED_REASON)
        if self.is_config(path) or (resolved is not None and self.is_config(resolved)) \
                or (relative and self.cwd is None and self.cwd_config):
            self.note(DENY, CONFIG_REASON)

    def deny_if_destroyed(self, path: str) -> None:
        """For rm/mv/chmod...: also the folders that hold the guard's files."""
        self.deny_if(path)
        resolved = self._resolve(path)
        if is_config_parent(resolved if resolved is not None else path):
            self.note(DENY, CONFIG_REASON)

    def deny_config_landing(self, target: str, sources: list[str], recursive: bool) -> None:
        """Copying or moving a folder into the project, home or `.claude` could land it
        as `.claude/hooks`, `.claude/settings.json` ... : deny a recursive copy there,
        or a source named like one of them."""
        resolved = self._resolve(target)
        if not is_config_parent(resolved if resolved is not None else target):
            return

        def suspicious(s: str) -> bool:
            name = basename(s.replace(SUBST, "").rstrip("/"))
            if name in _CONFIG_NAMES or name in (".", "..", "") or not _plain(s):
                return True
            return name.endswith(".jsonl")
        if recursive or any(suspicious(s) for s in sources):
            self.note(DENY, CONFIG_REASON)

    def change_dir(self, target: str | None) -> None:
        """Follow a `cd`, so relative paths after it are judged from the right folder."""
        if target is None or target == "~" or target.startswith("~/"):
            home = os.path.expanduser(target or "~")
            target = home if home.startswith("/") else None
        if target is None or target == "-" or not _plain(target):
            self.cwd = None  # can't tell: keep the old flags
            return
        if target.startswith("/"):
            self.cwd = os.path.normpath(target)
        elif self.cwd is not None:
            self.cwd = os.path.normpath(os.path.join(self.cwd, target))
        else:
            if is_protected(target.rstrip("/") + "/"):
                self.cwd_protected = True
            if self.is_config(target.rstrip("/") + "/"):
                self.cwd_config = True
            return
        self.cwd_protected = is_protected(self.cwd + "/")
        self.cwd_config = self.is_config(self.cwd + "/")

    def in_config_parent(self) -> bool:
        """The shell is in the project root, home, `.claude` - or the guard can't tell."""
        return self.cwd is None or is_config_parent(self.cwd) or self.cwd_config

    def simple(self, cmd: Simple, depth: int) -> None:
        for op, target in cmd.redirs:
            if op.startswith(">"):
                self.deny_if(target)
        words = strip_wrappers(cmd.words)
        if not words:
            return
        prog = words[0]
        head = basename(prog)
        args = words[1:]

        # -- authority --------------------------------------------------
        if is_bookfactory_word(prog):
            self.note(*analyze_bookfactory_args(args, context=self.release_context(cmd, words)))
        elif PY_RE.match(head):
            self.python(args, cmd)
        elif head in SHELLS:
            self.shell_program(args, cmd, depth)
        elif head in ("eval", "source", "."):
            if head == "eval":
                self.shell(" ".join(args), depth + 1)
        elif head in OTHER_INTERPRETERS:
            for k, a in enumerate(args):
                if a in ("-e", "-E", "--eval", "-p", "--print", "-r") and k + 1 < len(args):
                    self.code(args[k + 1])
        elif prog == SUBST or prog.startswith("$"):
            # the program itself is a variable or a substitution: can't tell what it is
            if any(a in OPERATOR_ONLY or a in NEEDS_AUTHORITY or a in ("set", "finalize")
                   for a in args):
                self.note(ASK, ("This runs a command the guard can't read (the program name is "
                                "a variable), with an argument that looks like a Book Factory "
                                "authority command. Kieran must confirm."))
        # any later word that is the bookfactory program (xargs, watch, sudo -E ...)
        if not is_bookfactory_word(prog) and not PY_RE.match(head) \
                and head not in LOOKS_ONLY:
            for seq in (words, cmd.words):
                for k, w in enumerate(seq[1:], start=1):
                    if is_bookfactory_word(w):
                        self.note(*analyze_bookfactory_args(seq[k + 1:]))
        if head == "find":
            for k, w in enumerate(words):
                if w in ("-exec", "-execdir", "-ok", "-okdir"):
                    end = k + 1
                    while end < len(words) and words[end] not in (";", "+"):
                        end += 1
                    inner = Simple()
                    inner.run_by_other = True
                    inner.words = words[k + 1:end]
                    self.simple(inner, depth + 1)
        if head == "xargs":
            k = 1
            while k < len(words) and words[k].startswith("-"):
                if words[k] in ("-I", "-n", "-P", "-L", "-d", "-E", "-s", "-a") and k + 1 < len(words):
                    k += 1
                k += 1
            if k < len(words):
                inner = Simple()
                inner.run_by_other = True
                inner.words = words[k:]
                self.simple(inner, depth + 1)

        # -- writes into approved material ------------------------------
        self.writes(head, args, words)

    def python(self, args: list[str], cmd: Simple) -> None:
        k = 0
        while k < len(args):
            a = args[k]
            if a == "-m" or (a.startswith("-m") and len(a) > 2 and not a.startswith("--")):
                module = args[k + 1] if a == "-m" and k + 1 < len(args) else a[2:]
                rest = args[k + 2:] if a == "-m" else args[k + 1:]
                if module.split(".")[0] == "bookfactory":
                    self.note(*analyze_bookfactory_args(rest))
                elif module == "runpy" or module == "pdb":
                    self.note(*analyze_bookfactory_args(rest[1:]) if rest and
                              rest[0].startswith("bookfactory") else (ALLOW, ""))
                return
            if a == "-c" or (a.startswith("-c") and len(a) > 2 and not a.startswith("--")):
                code = args[k + 1] if a == "-c" and k + 1 < len(args) else a[2:]
                self.code(code)
                return
            if a in ("-W", "-X", "--check-hash-based-pycs"):
                k += 2
                continue
            if a.startswith("-") and a != "-":
                k += 1
                continue
            # a script path, or `-` meaning stdin
            if a == "-":
                self.stdin_code(cmd)
            elif is_bookfactory_word(a):
                self.note(*analyze_bookfactory_args(args[k + 1:]))
            return
        self.stdin_code(cmd)  # plain `python3` reads its program from stdin

    def stdin_code(self, cmd: Simple) -> None:
        if cmd.stdin_text is not None:
            self.code(cmd.stdin_text)
        elif cmd.piped_in:
            # text piped in from an earlier command: judge the whole command line
            self.code(self.raw)

    def code(self, code: str) -> None:
        if code_calls_authority(code):
            self.note(ASK, ("This runs Python that imports Book Factory and mentions an "
                            "authority action (approve, lock, reject, revise, policy, advance, "
                            "assemble, preflight, finalize), which only the operator may decide "
                            "(AGENTS.md section 3). Kieran must confirm."))
        if code_writes_protected(code):
            self.note(DENY, APPROVED_REASON)
        if code_writes_config(code):
            self.note(DENY, CONFIG_REASON)

    def shell_program(self, args: list[str], cmd: Simple, depth: int) -> None:
        k = 0
        while k < len(args):
            a = args[k]
            if a in ("-c",) or (a.startswith("-") and not a.startswith("--") and "c" in a[1:]):
                if k + 1 < len(args):
                    self.shell(args[k + 1], depth + 1)
                return
            if a in ("-o", "+o", "-O", "+O"):
                k += 2
                continue
            if a.startswith(("-", "+")):
                k += 1
                continue
            return  # a script file: the guard can't see inside it (known gap)
        if cmd.stdin_text is not None:
            self.shell(cmd.stdin_text, depth + 1)
        elif cmd.piped_in and _LOOSE_BF_RE.search(self.raw):
            self.note(ASK, ("This pipes text into a shell and mentions a Book Factory "
                            "authority command. Kieran must confirm."))

    def writes(self, head: str, args: list[str], words: list[str]) -> None:
        plain = _args(args)
        if head in ("cd", "pushd"):
            self.change_dir(plain[0] if plain else None)
            return
        if head == "popd":
            self.change_dir("-")
            return
        if head in ("rm", "rmdir", "unlink", "chmod", "chown", "chgrp", "shred", "chattr",
                    "setfacl", "srm", "wipe"):
            for a in plain:
                self.deny_if_destroyed(a)
            return
        if head in ("touch", "truncate", "tee"):
            for a in plain:
                self.deny_if(a)
            return
        if head == "mv":
            for a in plain[:-1]:
                self.deny_if_destroyed(a)
            if plain:
                self.deny_if(plain[-1])
            if len(plain) > 1:
                self.deny_config_landing(plain[-1], plain[:-1], recursive=False)
            return
        if head in ("cp", "rsync", "install", "ln", "scp", "link", "ditto", "gcp"):
            target = None
            for k, a in enumerate(args):
                if a in ("-t", "--target-directory") and k + 1 < len(args):
                    target = args[k + 1]
                elif a.startswith("--target-directory="):
                    target = a.split("=", 1)[1]
            recursive = head in ("rsync", "ditto") or any(
                a in ("--recursive", "--archive") or (a.startswith("-") and not a.startswith("--")
                                                      and any(f in a[1:] for f in "rRa"))
                for a in args)
            if target is not None:
                self.deny_if(target)
                self.deny_config_landing(target, plain, recursive)
            elif plain:
                self.deny_if(plain[-1])
                self.deny_config_landing(plain[-1], plain[:-1], recursive)
            if head == "rsync" and any(a.startswith("--remove-source") for a in args):
                for a in plain:
                    self.deny_if(a)
            return
        if head in ("sed", "gsed", "perl"):
            inplace = any(a == "--in-place" or a.startswith("--in-place=")
                          or (a.startswith("-") and not a.startswith("--") and "i" in a[1:])
                          for a in args)
            if inplace:
                for a in plain:
                    self.deny_if(a)
            return
        if head in ("awk", "gawk", "mawk", "nawk"):
            inplace = any(a == "inplace" for a in args)
            for k, a in enumerate(args):
                if a in ("-f", "-v", "-F", "-i", "-l", "-e", "--file", "--source"):
                    continue
                if inplace:
                    self.deny_if(a)
            program = next((a for k, a in enumerate(args) if not a.startswith("-")
                            and (k == 0 or args[k - 1] not in ("-f", "-v", "-F", "-i", "-l"))),
                           "")
            self.code(program)
            return
        if head in ("sort", "shuf", "uniq"):
            for k, a in enumerate(args):
                if a == "-o" and k + 1 < len(args):
                    self.deny_if(args[k + 1])
                elif a.startswith("--output="):
                    self.deny_if(a.split("=", 1)[1])
                elif a.startswith("-o") and len(a) > 2 and not a.startswith("--"):
                    self.deny_if(a[2:])
            if head == "uniq" and len(plain) > 1:
                self.deny_if(plain[-1])
            return
        if head in ("split", "csplit"):
            if len(plain) > 1:
                self.deny_if(plain[-1])
            return
        if head in ("vi", "vim", "nvim", "ex", "ed", "view", "nano", "emacs", "pico", "joe",
                    "micro", "kak", "hx"):
            # an editor opening (or `-c 'w! path'` writing) a protected file
            for a in args:
                for piece in re.split(r"[\s|]+", a):
                    self.deny_if(piece.lstrip("+"))
            return
        if head == "patch" and not any(a in ("--dry-run", "-C", "--check") for a in args):
            self.note(DENY, PATCH_REASON)
            return
        if head == "dd":
            for a in args:
                if a.startswith("of="):
                    self.deny_if(a[3:])
            return
        if head == "git" and args:
            sub_k = 0
            while sub_k < len(args) and args[sub_k].startswith("-"):
                sub_k += 2 if args[sub_k] in ("-C", "-c") else 1
            if sub_k < len(args) and args[sub_k] in ("checkout", "restore", "rm", "mv", "clean",
                                                     "reset", "switch", "apply", "stash"):
                for a in _args(args[sub_k + 1:]):
                    self.deny_if(a)
            if sub_k < len(args) and args[sub_k] in ("apply", "am") and not any(
                    a in ("--check", "--stat", "--numstat", "--summary") for a in args):
                self.note(DENY, PATCH_REASON)
            return
        if head == "find" and any(a == "-delete" or a in ("-exec", "-execdir", "-ok", "-okdir")
                                  and k + 1 < len(args) and basename(args[k + 1]) in FIND_WRITERS
                                  for k, a in enumerate(args)):
            if any("approved" in a or "cover/drafts" in a for a in args):
                self.note(DENY, APPROVED_REASON)
            if any(self.is_config(a) or is_config_parent(a) for a in _args(args)[:1]) \
                    or any(_CONFIG_TEXT_RE.search(a) for a in args):
                self.note(DENY, CONFIG_REASON)
            return
        if head in ("unzip", "tar", "bsdtar", "7z", "7za", "gtar", "cpio", "wget", "curl"):
            # extracting / downloading into a protected directory
            destination = None
            for k, a in enumerate(args):
                if a in ("-d", "-C", "--directory", "-o", "-O", "--output", "-P") \
                        and k + 1 < len(args):
                    destination = args[k + 1]
                    self.deny_if(args[k + 1])
                elif a.startswith(("--directory=", "--output=", "-o")) and len(a) > 2 \
                        and "=" in a:
                    destination = a.split("=", 1)[1]
                    self.deny_if(destination)
            extracting = head in ("unzip", "cpio") or (head in ("7z", "7za") and args[:1] == ["x"]) \
                or (head in ("tar", "bsdtar", "gtar") and args and (
                    "--extract" in args or "--get" in args
                    or any(a.startswith("-") and not a.startswith("--") and "x" in a[1:]
                           for a in args)
                    or (not args[0].startswith("-") and "x" in args[0])))
            if extracting:
                # an archive can hold `.claude/hooks/...`: not into the project root,
                # home or `.claude` (nor anywhere the guard can't place)
                if destination is None:
                    if self.in_config_parent():
                        self.note(DENY, CONFIG_REASON)
                else:
                    resolved = self._resolve(destination)
                    if is_config_parent(resolved if resolved is not None else destination) \
                            or self.is_config(destination):
                        self.note(DENY, CONFIG_REASON)


def decide(payload) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return ASK, UNREADABLE_REASON
    tool = payload.get("tool_name")
    if tool is not None and tool != "Bash":
        return ALLOW, ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ASK, UNREADABLE_REASON
    command = tool_input.get("command")
    if not isinstance(command, str):
        return ASK, UNREADABLE_REASON
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else None
    transcript = payload.get("transcript_path")
    config_dirs = (os.path.dirname(transcript),) \
        if isinstance(transcript, str) and transcript.startswith("/") else ()
    analyzer = Analyzer(command, cwd, config_dirs)
    analyzer.shell(command)
    if analyzer.decision == ASK:
        # Only an ask can become a go-ahead; a deny never does.
        message = operator_message(payload)
        if message is not None and go_ahead_line(command, message):
            return ALLOW, f"Kieran typed the go-ahead this turn: '{_quote(message)}'"
    return analyzer.decision, analyzer.reason


def emit(decision: str, reason: str, mode=None) -> None:
    if decision == ALLOW:
        if reason:  # let through on Kieran's go-ahead: say so, in every mode
            _write_decision(ALLOW, reason)
        return
    if decision == ASK and mode not in ASK_MODES:
        decision, reason = DENY, reason + BLOCKED_SUFFIX
    _write(decision, reason)


def _write(decision: str, reason: str) -> None:
    if decision == ALLOW:
        return
    _write_decision(decision, reason)


def _write_decision(decision: str, reason: str) -> None:
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    sys.stdout.write("\n")


def main() -> int:
    try:
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            emit(ASK, UNREADABLE_REASON)
            return 0
        decision, reason = decide(payload)
        mode = payload.get("permission_mode") if isinstance(payload, dict) else None
        emit(decision, reason, mode)
    except Exception:  # never crash: fail safe by asking
        try:
            emit(ASK, UNREADABLE_REASON)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
