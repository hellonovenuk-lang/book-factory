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
              production policy authorizes them (AGENTS.md section 3).

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
import re
import sys

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
)


def code_writes_protected(code: str) -> bool:
    return bool(_PROTECTED_TEXT_RE.search(code) and _PY_WRITE_RE.search(code))


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


def analyze_bookfactory_args(args: list[str], shown: str = "bookfactory"):
    """Decision for the arguments that follow the bookfactory program."""
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
        return ASK, ask_reason("bookfactory advance", NEEDS_AUTHORITY["advance"])
    if sub in NEEDS_AUTHORITY:
        return ASK, ask_reason(f"bookfactory {sub}", NEEDS_AUTHORITY[sub])
    if sub in ("policy", "cover", "pictures"):
        op = next((r for r in rest if not r.startswith("-")), None)
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
            return ASK, reason
    return ALLOW, ""


class Analyzer:
    def __init__(self, raw: str, cwd: str | None):
        self.raw = raw
        self.decision = ALLOW
        self.reason = ""
        self.cwd_protected = bool(cwd and is_protected(cwd.rstrip("/") + "/"))

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
        for cmd in split_simple(toks, heredocs):
            self.simple(cmd, depth)

    def deny_if(self, path: str) -> None:
        if is_protected(path, self.cwd_protected):
            self.note(DENY, APPROVED_REASON)

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
            self.note(*analyze_bookfactory_args(args))
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
            if plain and is_protected(plain[0].rstrip("/") + "/"):
                self.cwd_protected = True
            return
        if head in ("rm", "rmdir", "unlink", "chmod", "chown", "chgrp", "touch", "truncate",
                    "shred", "chattr", "setfacl", "mv", "tee", "srm", "wipe"):
            for a in plain:
                self.deny_if(a)
            return
        if head in ("cp", "rsync", "install", "ln", "scp", "link", "ditto", "gcp"):
            target = None
            for k, a in enumerate(args):
                if a in ("-t", "--target-directory") and k + 1 < len(args):
                    target = args[k + 1]
                elif a.startswith("--target-directory="):
                    target = a.split("=", 1)[1]
            if target is not None:
                self.deny_if(target)
            elif plain:
                self.deny_if(plain[-1])
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
            return
        if head == "find" and any(a == "-delete" or a in ("-exec", "-execdir", "-ok", "-okdir")
                                  and k + 1 < len(args) and basename(args[k + 1]) in FIND_WRITERS
                                  for k, a in enumerate(args)):
            if any("approved" in a or "cover/drafts" in a for a in args):
                self.note(DENY, APPROVED_REASON)
            return
        if head in ("unzip", "tar", "bsdtar", "7z", "patch", "wget", "curl"):
            # extracting / downloading into a protected directory
            for k, a in enumerate(args):
                if a in ("-d", "-C", "--directory", "-o", "-O", "--output", "-P") \
                        and k + 1 < len(args):
                    self.deny_if(args[k + 1])
                elif a.startswith(("--directory=", "--output=", "-o")) and len(a) > 2 \
                        and "=" in a:
                    self.deny_if(a.split("=", 1)[1])


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
    analyzer = Analyzer(command, cwd)
    analyzer.shell(command)
    return analyzer.decision, analyzer.reason


def emit(decision: str, reason: str, mode=None) -> None:
    if decision == ALLOW:
        return
    if decision == ASK and mode not in ASK_MODES:
        decision, reason = DENY, reason + BLOCKED_SUFFIX
    _write(decision, reason)


def _write(decision: str, reason: str) -> None:
    if decision == ALLOW:
        return
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
