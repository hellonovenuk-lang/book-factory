"""The approval guard hook (.claude/hooks/guard-authority.py).

The hook is run exactly as Claude Code runs it: a subprocess with the
PreToolUse JSON on stdin. It must ask before any operator-authority
bookfactory command, deny Bash writes into approved material, and stay quiet
for ordinary read-only commands. Outside the "default" permission mode an ask
would never reach the operator, so it must become a deny.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / ".claude" / "hooks" / "guard-authority.py"


def run_hook(stdin: str) -> tuple[str, dict | None, subprocess.CompletedProcess]:
    proc = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True,
                          text=True, timeout=30)
    out = proc.stdout.strip()
    if not out:
        return "allow", None, proc
    data = json.loads(out)
    spec = data["hookSpecificOutput"]
    return spec["permissionDecision"], spec, proc


def decide(command: str, *, tool: str = "Bash", cwd: str | None = None,
           mode: str | None = "default") -> str:
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool,
               "tool_input": {"command": command}}
    if mode is not None:
        payload["permission_mode"] = mode
    if cwd is not None:
        payload["cwd"] = cwd
    decision, spec, proc = run_hook(json.dumps(payload))
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == "", proc.stderr
    if spec is not None:
        assert spec["hookEventName"] == "PreToolUse"
        assert spec["permissionDecisionReason"]
    return decision


ASKS = [
    # every operator-authority command
    "bookfactory approve demo-book p001",
    "bookfactory approve demo-book --all-passing --by kieran",
    "bookfactory approve demo-book --all-passing --by agent --autonomous",
    "bookfactory lock visual demo-book --by kieran",
    "bookfactory reject demo-book p001 --reason blurry",
    "bookfactory revise demo-book p058 --reason typo",
    "bookfactory policy set demo-book autonomous --by kieran",
    "bookfactory pictures set demo-book unlimited --by kieran",
    "bookfactory --root . pictures set demo-book limit --count 20 --by kieran",
    "bookfactory cover approve demo-book --draft v1 --by kieran",
    "bookfactory cover finalize demo-book --draft v1",
    "bookfactory cover preflight demo-book",
    "bookfactory advance demo-book --force",
    "bookfactory advance demo-book --forc",   # argparse accepts abbreviations
    "bookfactory advance demo-book",
    "bookfactory assemble demo-book",
    "bookfactory preflight demo-book",
    # global flags before the subcommand
    "bookfactory --json approve demo-book p001",
    "bookfactory --root /tmp/repo lock manuscript demo-book",
    "bookfactory --root=/tmp/repo --json cover --json approve demo-book --draft v2 --by k",
    # other ways of invoking the program
    "python -m bookfactory approve demo-book p001",
    "python3 -m bookfactory.cli.main approve demo-book p001",
    "python3.11 -m bookfactory.cli.main --json lock visual demo-book",
    "/usr/local/bin/bookfactory approve demo-book p001",
    ".venv/bin/bookfactory approve demo-book p001",
    "python3 bookfactory/cli/main.py approve demo-book p001",
    "uv run bookfactory approve demo-book p001",
    # chains, pipes, subshells
    "bookfactory status demo-book && bookfactory approve demo-book p001",
    "bookfactory status demo-book; bookfactory lock visual demo-book",
    "false || bookfactory approve demo-book p001",
    "echo yes | bookfactory approve demo-book p001",
    "echo $(bookfactory approve demo-book p001)",
    "echo `bookfactory approve demo-book p001`",
    "echo \"result: $(bookfactory revise demo-book p001)\"",
    "(cd books && bookfactory approve demo-book p001)",
    "bash -c \"bookfactory approve demo-book p001\"",
    "sh -c 'bookfactory policy set demo-book autonomous --by x'",
    "bash -lc 'cd /repo && bookfactory approve demo-book p001'",
    "eval \"bookfactory approve demo-book p001\"",
    "env X=1 bookfactory approve demo-book p001",
    "X=1 Y=2 bookfactory approve demo-book p001",
    "sudo -u root bookfactory approve demo-book p001",
    "timeout 30 bookfactory approve demo-book p001",
    "command -p bookfactory approve demo-book p001",
    "nohup bookfactory lock visual demo-book &",
    "B=bookfactory; $B approve demo-book p001",
    "echo p001 | xargs bookfactory approve demo-book",
    "bookfactory \\\n  approve demo-book p001",
    "bookfactory status demo-book\nbookfactory approve demo-book p001",
    "'bookfactory' 'approve' demo-book p001",
    "book\\factory appr\\ove demo-book p001",
    "bookfactory $CMD demo-book p001",
    "echo 'bookfactory approve demo-book p001' | bash",
    "bash <<'EOF'\nbookfactory approve demo-book p001\nEOF",
    # Python that calls the API directly
    "python3 -c \"from bookfactory.core import api; api.approve('demo-book', 'p001')\"",
    "python -c 'import bookfactory.core.api as a; a.lock(\"demo-book\", \"visual\")'",
    "python3 -c \"from bookfactory.cli.main import main; main(['approve','demo-book','p001'])\"",
    "python3 - <<'EOF'\nfrom bookfactory.core import api\napi.revise('demo-book', 'p001')\nEOF",
    "python3 <<< \"from bookfactory.core import api; api.set_policy('demo-book', 'autonomous', by='x')\"",
]

DENIES = [
    "echo hi > books/demo-book/pages/approved/p001.pdf",
    "echo hi >> books/demo-book/assets/approved/hero/hero-v1.png",
    "echo hi >& books/demo-book/pages/approved/p001.pdf",
    "echo hi | tee books/demo-book/pages/approved/p001.pdf",
    "cp /tmp/new.pdf books/demo-book/pages/approved/p001.pdf",
    "cp -t books/demo-book/pages/approved /tmp/new.pdf",
    "mv /tmp/new.pdf books/demo-book/assets/approved/",
    "mv books/demo-book/pages/approved/p001.pdf /tmp/",
    "rsync -a /tmp/x/ books/demo-book/pages/approved/",
    "install -m 644 /tmp/x.pdf books/demo-book/pages/approved/p001.pdf",
    "rm books/demo-book/pages/approved/p001.pdf",
    "rm -rf books/demo-book/assets/approved",
    "chmod u+w books/demo-book/pages/approved/p001.pdf",
    "chown me books/demo-book/pages/approved/p001.pdf",
    "touch books/demo-book/pages/approved/p001.pdf",
    "sed -i 's/a/b/' books/demo-book/pages/approved/p001.json",
    "sed -i.bak -e 's/a/b/' books/demo-book/pages/approved/p001.json",
    "truncate -s 0 books/demo-book/pages/approved/p001.pdf",
    "dd if=/dev/zero of=books/demo-book/pages/approved/p001.pdf bs=1 count=1",
    "ln -sf /tmp/x.pdf books/demo-book/pages/approved/p001.pdf",
    "python3 -c \"open('books/demo-book/pages/approved/p001.pdf', 'w').write('x')\"",
    "python3 -c \"import pathlib; pathlib.Path('books/d/assets/approved/a.png').write_bytes(b'')\"",
    "git checkout -- books/demo-book/pages/approved/p001.pdf",
    "git restore books/demo-book/pages/approved/p001.pdf",
    "cp /tmp/cover.pdf books/demo-book/cover/drafts/cover-v2.pdf",
    "rm books/demo-book/cover/drafts/cover-v1.pdf",
    "chmod 644 books/demo-book/cover/drafts/*.pdf",
    "cd books/demo-book/pages && rm approved/p001.pdf",
    "cd books/demo-book/pages/approved && rm p001.pdf",
    "bash -c 'echo x > books/demo-book/pages/approved/p001.pdf'",
    "find books/demo-book/pages/approved -name '*.pdf' -delete",
    "find books -name p001.pdf -exec rm {} \\; -path '*approved*'",
    "sudo rm books/demo-book/pages/approved/p001.pdf",
    # deny outranks ask when both happen
    "bookfactory approve demo-book p001 > books/demo-book/pages/approved/log.txt",
]

ALLOWS = [
    "bookfactory status demo-book",
    "bookfactory next demo-book --json",
    "bookfactory --json task demo-book",
    "bookfactory validate demo-book",
    "bookfactory list",
    "bookfactory policy show demo-book --json",
    "bookfactory pictures show demo-book --json",
    "bookfactory questionnaire --json",
    "bookfactory qa demo-book --json",
    "bookfactory render demo-book --page p001 --submit",
    "bookfactory submit demo-book hero --kind asset --file /tmp/hero.png",
    "bookfactory cover dimensions demo-book",
    "bookfactory history demo-book",
    "python3 -m bookfactory.cli.main status demo-book",
    "grep approve AGENTS.md",
    "grep -rn 'bookfactory approve' docs/",
    "git log --oneline -5",
    "git status",
    "git diff books/demo-book/pages/approved/",
    "cat books/demo-book/pages/approved/p001.pdf",
    "ls -la books/demo-book/pages/approved/",
    "sha256sum books/demo-book/pages/approved/p001.pdf",
    "cp books/demo-book/pages/approved/p001.pdf /tmp/review.pdf",
    "cat books/demo-book/cover/drafts/cover-v1.pdf > /tmp/cover-copy.pdf",
    "python3 -m pytest tests/test_approval.py -q",
    "python3 -c \"import bookfactory; print(bookfactory.__version__)\"",
    "python3 -c \"print(open('books/demo-book/pages/approved/p001.json').read())\"",
    "echo 'remember to ask Kieran to approve' 2>/dev/null",
    "ls books >&2",
    "cp /tmp/draft.pdf books/demo-book/pages/drafts/p001/p001-v2.pdf",
    "bookfactory render demo-book --page p001 > /tmp/render.log 2>&1",
    "git commit -m \"approve flow\"",
    "bookfactory status demo-book | grep approve",
    "python3 scripts/build_demo_book.py",
]


@pytest.mark.parametrize("command", ASKS)
def test_asks_before_authority_commands(command):
    assert decide(command) == "ask"


@pytest.mark.parametrize("command", DENIES)
def test_denies_writes_into_approved_material(command):
    assert decide(command) == "deny"


@pytest.mark.parametrize("command", ALLOWS)
def test_stays_quiet_for_ordinary_commands(command):
    assert decide(command) == "allow"


def test_ask_reason_is_plain_english():
    _, spec, _ = run_hook(json.dumps({"tool_name": "Bash", "permission_mode": "default",
                                      "tool_input": {"command": "bookfactory approve b p1"}}))
    reason = spec["permissionDecisionReason"]
    assert "`bookfactory approve`" in reason
    assert "only the operator may decide" in reason
    assert "Kieran must confirm" in reason


def test_deny_reason_points_at_revise():
    _, spec, _ = run_hook(json.dumps({"tool_name": "Bash", "tool_input": {
        "command": "rm books/b/pages/approved/p1.pdf"}}))
    assert "AGENTS.md section 4" in spec["permissionDecisionReason"]
    assert "bookfactory revise" in spec["permissionDecisionReason"]


def test_writes_are_denied_when_the_session_is_inside_an_approved_folder():
    assert decide("rm p001.pdf", cwd="/repo/books/demo-book/pages/approved") == "deny"
    assert decide("cat p001.pdf", cwd="/repo/books/demo-book/pages/approved") == "allow"


@pytest.mark.parametrize("tool", ["Edit", "Write", "Read", "Grep"])
def test_other_tools_are_left_alone(tool):
    assert decide("bookfactory approve demo-book p001", tool=tool) == "allow"


@pytest.mark.parametrize("stdin", [
    "not json at all",
    "",
    "[1, 2, 3]",
    json.dumps({"tool_name": "Bash", "tool_input": {}}),
    json.dumps({"tool_name": "Bash", "tool_input": {"command": 42}}),
    json.dumps({"tool_name": "Bash"}),
])
def test_unreadable_input_blocks_instead_of_crashing(stdin):
    decision, spec, proc = run_hook(stdin)
    assert proc.returncode == 0
    assert proc.stderr == ""
    assert decision == "deny"
    assert "couldn't read" in spec["permissionDecisionReason"]


@pytest.mark.parametrize("mode", ["auto", "bypassPermissions", "dontAsk", "acceptEdits",
                                  "plan", "something-new", None])
def test_asks_become_blocks_where_the_question_would_not_reach_kieran(mode):
    # Live trial 2026-09-23: in auto mode an "ask" ran `bookfactory approve`
    # without Kieran ever seeing a question.
    assert decide("bookfactory approve demo-book p001", mode=mode) == "deny"
    assert decide("python -m bookfactory lock visual demo-book", mode=mode) == "deny"
    assert decide("bookfactory status demo-book", mode=mode) == "allow"


def test_block_reason_says_to_ask_kieran_in_the_chat():
    _, spec, _ = run_hook(json.dumps({"tool_name": "Bash", "permission_mode": "auto",
                                      "tool_input": {"command": "bookfactory approve b p1"}}))
    reason = spec["permissionDecisionReason"]
    assert "`bookfactory approve`" in reason
    assert "ask Kieran in the chat" in reason
