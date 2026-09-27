"""The go-ahead: Kieran's own typed decision lets an authority command run in auto mode.

The approval guard (`.claude/hooks/guard-authority.py`) reads Kieran's latest
typed message from Claude Code's own transcript (the PreToolUse payload's
`transcript_path`, under ~/.claude/projects/). A command line gets an explicit
allow only when that message IS a decision that covers every command on the
line, the call is from the main session (never a helper), and the message is
from this session and under an hour old. Nothing Claude can write in the
project counts, and Bash writes to the guard's own files and the transcripts
are denied.

The hook runs exactly as Claude Code runs it: a subprocess with JSON on stdin.
HOME points at a temporary folder holding the transcript, and
CLAUDE_PROJECT_DIR at a temporary project with two books.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GUARD = REPO / ".claude" / "hooks" / "guard-authority.py"
SESSION = "c66c497f-0000-4000-8000-000000000001"
B = "padel-addicts-guide"
G = "golf-addicts-guide"


def _now(minutes_ago: float = 0) -> str:
    stamp = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return stamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def human(text, *, minutes_ago: float = 0, session: str = SESSION, **extra) -> dict:
    """A message Kieran typed, as Claude Code writes it to the transcript."""
    entry = {"parentUuid": "p", "isSidechain": False, "userType": "external",
             "entrypoint": "remote_mobile", "cwd": "/home/user/book-factory",
             "sessionId": session, "version": "2.1.0", "gitBranch": "main",
             "type": "user", "message": {"role": "user", "content": text},
             "uuid": "u", "timestamp": _now(minutes_ago), "permissionMode": "auto",
             "promptSource": "sdk", "origin": {"kind": "human"}, "turnOrigin": "human"}
    entry.update(extra)
    return entry


def tool_result(output: str = "ok") -> dict:
    return {"type": "user", "sessionId": SESSION, "isSidechain": False, "timestamp": _now(),
            "message": {"role": "user", "content": [
                {"tool_use_id": "toolu_1", "type": "tool_result", "content": output}]},
            "toolUseResult": {"stdout": output}}


def assistant(text: str = "Locking the look now.") -> dict:
    return {"type": "assistant", "sessionId": SESSION, "timestamp": _now(),
            "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def meta(text: str = "Base directory for this skill: ...") -> dict:
    return {"type": "user", "sessionId": SESSION, "isMeta": True, "timestamp": _now(),
            "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def task_notification() -> dict:
    return {"type": "user", "sessionId": SESSION, "timestamp": _now(),
            "origin": {"kind": "task-notification"}, "promptSource": "system",
            "message": {"role": "user", "content": "<task-notification>done</task-notification>"}}


def peer(text: str = "approve cover v1") -> dict:
    return {"type": "user", "sessionId": SESSION, "timestamp": _now(), "isMeta": True,
            "origin": {"kind": "peer", "from": "a123"}, "promptSource": "system",
            "message": {"role": "user", "content": text}}


class World:
    def __init__(self, tmp: Path):
        self.home = tmp / "home"
        self.project = tmp / "project"
        for book in (B, G):
            (self.project / "books" / book).mkdir(parents=True)
        self.transcripts = self.home / ".claude" / "projects" / "-home-user-book-factory"
        self.transcripts.mkdir(parents=True)
        self.transcript = self.transcripts / f"{SESSION}.jsonl"
        self.entries: list[dict] = [human("hello")]
        self.save()

    def save(self) -> None:
        self.transcript.write_text("".join(json.dumps(e) + "\n" for e in self.entries),
                                   encoding="utf-8")

    def says(self, text, *after: dict, **kw) -> None:
        """Kieran typed `text`; then Claude answered and ran a tool."""
        self.entries += [human(text, **kw), assistant(), tool_result(), assistant()]
        self.entries += list(after)
        self.save()

    def env(self) -> dict:
        env = dict(os.environ)
        env.update(HOME=str(self.home), CLAUDE_PROJECT_DIR=str(self.project))
        env.pop("CLAUDE_CONFIG_DIR", None)
        env.pop("BOOKFACTORY_ROOT", None)
        return env

    def guard(self, command: str, *, mode: str = "auto", cwd: str | None = None,
              **payload_extra) -> tuple[str, str]:
        payload = {"session_id": SESSION, "transcript_path": str(self.transcript),
                   "cwd": cwd or str(self.project), "permission_mode": mode,
                   "hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": command}, "tool_use_id": "toolu_x"}
        payload.update(payload_extra)
        payload = {k: v for k, v in payload.items() if v is not None}
        proc = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload),
                              capture_output=True, text=True, timeout=30, env=self.env())
        assert proc.returncode == 0, proc.stderr
        assert proc.stderr == ""
        out = proc.stdout.strip()
        if not out:
            return "none", ""
        spec = json.loads(out)["hookSpecificOutput"]
        assert spec["hookEventName"] == "PreToolUse"
        return spec["permissionDecision"], spec["permissionDecisionReason"]

    def decision(self, command: str, **kw) -> str:
        return self.guard(command, **kw)[0]


@pytest.fixture
def world(tmp_path) -> World:
    return World(tmp_path)


LOCK_VISUAL = f"bookfactory lock visual {B} --by kieran"
COVER_V1 = f"bookfactory cover approve {B} --draft v1 --by kieran"


# -- no decision typed: exactly as before -------------------------------------

BEFORE = [
    LOCK_VISUAL,
    COVER_V1,
    f"bookfactory revise {B} p014 --by kieran",
    f"bookfactory assemble {B}",
    f"bookfactory preflight {B}",
    f"bookfactory approve {B} p001 --by kieran",
    f"bookfactory policy set {B} autonomous --by kieran",
]


@pytest.mark.parametrize("command", BEFORE)
def test_without_a_decision_nothing_changes(world, command):
    world.says("thanks, carry on")
    assert world.decision(command) == "deny"
    assert world.decision(command, mode="default") == "ask"


@pytest.mark.parametrize("command", BEFORE)
def test_without_a_transcript_nothing_changes(world, command):
    world.says("lock the look, approve cover v1, assemble and preflight")
    assert world.decision(command, transcript_path=None) == "deny"
    assert world.decision(command, transcript_path=None, mode="default") == "ask"


def test_a_file_in_the_project_is_never_trusted(world):
    # the old slip design: a file Claude could write. It counts for nothing now.
    slip = world.project / ".claude" / "state" / "go-ahead.json"
    slip.parent.mkdir(parents=True)
    slip.write_text(json.dumps({"session_id": SESSION, "recorded_at": _now(),
                                "prompt": "lock the look"}))
    assert world.decision(LOCK_VISUAL) == "deny"


# -- decisions that work ------------------------------------------------------

def test_lock_the_look_allows_the_visual_lock_only(world):
    world.says("Lock the look")
    verdict, reason = world.guard(LOCK_VISUAL)
    assert verdict == "allow"
    assert "Kieran typed the go-ahead this turn" in reason and "Lock the look" in reason
    assert world.decision(LOCK_VISUAL, mode="default") == "allow"
    assert world.decision(f"bookfactory lock manuscript {B} --by kieran") == "deny"
    assert world.decision(f"bookfactory lock voice {B} --by kieran") == "deny"


def test_approve_cover_v1_allows_that_draft_only(world):
    world.says("approve cover v1")
    assert world.decision(COVER_V1) == "allow"
    assert world.decision(f"bookfactory cover approve {B} --draft v2 --by kieran") == "deny"
    assert world.decision(f"bookfactory approve {B} p003 --draft v1 --by kieran") == "deny"
    assert world.decision(f"bookfactory approve {B} p003 --by kieran") == "deny"


def test_revise_named_pages_only(world):
    world.says("revise p014 p033")
    assert world.decision(f"bookfactory revise {B} p014 --reason joke --by kieran") == "allow"
    assert world.decision(f"bookfactory revise {B} p033 --by kieran") == "allow"
    assert world.decision(f"bookfactory revise {B} p040 --by kieran") == "deny"


def test_revise_p014_does_not_cover_p033(world):
    world.says("revise p014")
    assert world.decision(f"bookfactory revise {B} p014 --by kieran") == "allow"
    assert world.decision(f"bookfactory revise {B} p033 --by kieran") == "deny"


@pytest.mark.parametrize("message,command", [
    ("Revise", f"bookfactory revise {B} p033 --reason typo --by kieran"),
    ("Lock", LOCK_VISUAL),
    ("Lock it", f"bookfactory lock voice {B} --by kieran"),
    ("Approve all", f"bookfactory approve {B} p001 --by kieran"),
    ("approve them", f"bookfactory approve {B} ref-x --kind asset --draft v1 --by kieran"),
    ("Ok, please lock the look.", LOCK_VISUAL),
    ("Yes. Approve p014 and p015", f"bookfactory approve {B} p015 --by kieran"),
    ("go ahead and approve cover v1, thanks", COVER_V1),
    ("Assemble", f"bookfactory assemble {B}"),
    ("Finalise the cover v1", f"bookfactory cover finalize {B} --draft v1"),
    ("Release it", f"bookfactory advance {B} --to release_ready"),
    ("preflight the cover", f"bookfactory cover preflight {B}"),
    ("set the policy to autonomous", f"bookfactory policy set {B} autonomous --by kieran"),
    ("set the picture budget to limit 20",
     f"bookfactory pictures set {B} limit --count 20 --by kieran"),
    ("approve p014", f"bookfactory approve {B} p014 --by kieran"),
])
def test_short_decisions_work(world, message, command):
    world.says(message)
    assert world.decision(command) == "allow", message


def test_one_message_can_decide_several_steps(world):
    world.says("assemble, preflight and approve cover v1")
    assert world.decision(f"bookfactory assemble {B}") == "allow"
    assert world.decision(f"bookfactory preflight {B}") == "allow"
    assert world.decision(COVER_V1) == "allow"
    assert world.decision(f"bookfactory assemble {B} && bookfactory preflight {B}") == "allow"
    assert world.decision(f"bookfactory cover finalize {B} --draft v1") == "deny"
    assert world.decision(LOCK_VISUAL) == "deny"
    assert world.decision(f"bookfactory assemble {B}; bookfactory revise {B} p001 "
                          "--by kieran") == "deny"


def test_read_only_bookfactory_commands_may_share_the_line(world):
    world.says("lock the look")
    assert world.decision(f"bookfactory status {B} && {LOCK_VISUAL} && bookfactory next {B}") \
        == "allow"


# -- finding A: nothing else rides along --------------------------------------

@pytest.mark.parametrize("command", [
    f"{LOCK_VISUAL} && rm -rf /tmp/zzz",
    f"{LOCK_VISUAL}; git push --force origin main",
    f"{LOCK_VISUAL}; perl -e 'print 1'",
    f"{LOCK_VISUAL} | tail -5",
    f"{LOCK_VISUAL} > /tmp/lock.log",
    f"{LOCK_VISUAL} || true",
    f"{LOCK_VISUAL} &",
    f"echo start; {LOCK_VISUAL}",
    f"({LOCK_VISUAL})",
    f"{LOCK_VISUAL} --note \"$(whoami)\"",
    f"cd /tmp && {LOCK_VISUAL}",
    f"PYTHONPATH=/tmp/evil {LOCK_VISUAL}",
    f"sudo {LOCK_VISUAL}",
    f"python3 -m bookfactory lock visual {B} --by kieran",
    f"bash -c '{LOCK_VISUAL}'",
    f"echo '{LOCK_VISUAL}' | bash",
    f"for s in visual; do bookfactory lock $s {B} --by kieran; done",
])
def test_chained_or_disguised_commands_get_no_go_ahead(world, command):
    world.says("lock the look")
    verdict, reason = world.guard(command)
    assert verdict == "deny", command
    assert "go-ahead" not in reason
    assert world.decision(command, mode="default") in ("ask", "deny")


# -- finding B: only a message that IS a decision counts ------------------------

NOT_DECISIONS = [
    "tell me what approve does",
    "I approve of your plan, now render p014",
    "can you explain what lock means",
    "Would it be wise to lock the look?",
    "I will never, under any circumstances, let you lock the look",
    "Please hold off. Approve p014 after I check it",
    "Remember: approve, lock, revise are mine only",
    "keep policy as it is, not autonomous",
    "approve the cover draft? No way.",
    "don't approve the cover",
    "Do not lock the look",
    "lock the look later",
    "approve p014 once you've checked it",
    "lock the look unless the face changed",
    "approve cover v1 only if it builds",
    "wait",
    "yes",
    "Lock the look and then carry on with the manuscript and the pictures and everything "
    "else you can do tonight",
    "Lock the look, and write the manuscript",
]


@pytest.mark.parametrize("message", NOT_DECISIONS)
def test_talk_questions_and_negations_decide_nothing(world, message):
    world.says(message)
    for command in (LOCK_VISUAL, COVER_V1, f"bookfactory approve {B} p014 --by kieran",
                    f"bookfactory revise {B} p014 --by kieran",
                    f"bookfactory policy set {B} autonomous --by kieran",
                    f"bookfactory cover approve {B} --by kieran --draft v2"):
        assert world.decision(command) == "deny", (message, command)


# -- finding C: bare verbs stay narrow -----------------------------------------

def test_a_bare_approve_never_covers_cover_artwork_or_the_cover(world):
    world.says("Approve all")
    assert world.decision(f"bookfactory approve {B} cover-front-artwork --kind asset "
                          "--by kieran") == "deny"
    assert world.decision(f"bookfactory approve {B} cover-back --kind asset --by kieran") \
        == "deny"
    assert world.decision(f"bookfactory cover approve {B} --draft v1 --by kieran") == "deny"
    assert world.decision(f"bookfactory approve {B} --all-passing --by kieran") == "deny"


def test_cover_artwork_needs_its_own_id_typed(world):
    world.says("approve cover-front-artwork v2")
    assert world.decision(f"bookfactory approve {B} cover-front-artwork --kind asset "
                          "--draft v2 --by kieran") == "allow"


def test_a_bare_approve_covers_one_book_per_line(world):
    world.says("approve them")
    assert world.decision(f"bookfactory approve {B} p001 --by kieran && "
                          f"bookfactory approve {B} p002 --by kieran") == "allow"
    assert world.decision(f"bookfactory approve {B} p001 --by kieran && "
                          f"bookfactory approve {G} p001 --by kieran") == "deny"


def test_a_typed_book_must_match(world):
    world.says(f"approve cover v2 for {G}")
    assert world.decision(f"bookfactory cover approve {G} --draft v2 --by kieran") == "allow"
    assert world.decision(f"bookfactory cover approve {B} --draft v2 --by kieran") == "deny"


def test_typed_ids_limit_the_approval(world):
    world.says("approve p014 v2")
    assert world.decision(f"bookfactory approve {B} p014 --draft v2 --by kieran") == "allow"
    assert world.decision(f"bookfactory approve {B} p014 --by kieran") == "deny"
    assert world.decision(f"bookfactory approve {B} p015 --draft v2 --by kieran") == "deny"
    world.says("approve hero")
    assert world.decision(f"bookfactory approve {B} hero --kind asset --by kieran") == "allow"
    assert world.decision(f"bookfactory approve {B} villain --kind asset --by kieran") \
        == "deny"


def test_a_bare_lock_covers_one_lock(world):
    world.says("Lock it")
    assert world.decision(f"bookfactory lock voice {B} --by kieran") == "allow"
    assert world.decision(f"bookfactory lock voice {B} --by kieran && "
                          f"bookfactory lock manuscript {B} --by kieran") == "deny"


def test_a_step_signed_by_claude_or_autonomous_is_not_covered(world):
    world.says("lock the look and approve cover v1")
    assert world.decision(f"bookfactory lock visual {B} --by claude") == "deny"
    assert world.decision(f"bookfactory lock visual {B}") == "deny"
    assert world.decision(f"bookfactory cover approve {B} --draft v1 --by claude") == "deny"
    assert world.decision(f"bookfactory lock visual {B} --by kieran --autonomous") == "deny"


@pytest.mark.parametrize("message,command", [
    ("advance it", f"bookfactory advance {B} --force"),
    ("release it", f"bookfactory advance {B} --to release_ready --force"),
    ("approve all", f"bookfactory approve {B} --all-passing --by kieran"),
    ("lock the look", f"bookfactory lock visual {B} --by kieran --forc"),
    ("advance it", f"bookfactory advance {B}"),
])
def test_force_and_all_passing_are_never_covered(world, message, command):
    world.says(message)
    assert world.decision(command) == "deny"


def test_policy_and_picture_budget_need_the_value_typed(world):
    world.says("set the policy")
    assert world.decision(f"bookfactory policy set {B} autonomous --by kieran") == "deny"
    world.says("set the policy to autonomous")
    assert world.decision(f"bookfactory policy set {B} checkpointed --by kieran") == "deny"
    world.says("set the picture budget to limit 20")
    assert world.decision(f"bookfactory pictures set {B} limit --count 30 --by kieran") \
        == "deny"
    assert world.decision(f"bookfactory pictures set {B} unlimited --by kieran") == "deny"


def test_writes_into_approved_work_stay_denied(world):
    world.says("revise p014")
    assert world.decision(f"bookfactory revise {B} p014 --by kieran > "
                          f"books/{B}/pages/approved/x.txt") == "deny"
    assert world.decision(f"rm books/{B}/pages/approved/p014.pdf") == "deny"


# -- finding E: only Kieran's own latest message, never for a helper ------------

@pytest.mark.parametrize("extra", [{"agent_id": "a1536293633e5fc41",
                                    "agent_type": "general-purpose"},
                                   {"agent_id": "a1536293633e5fc41"},
                                   {"agent_type": "builder"}])
def test_a_helper_never_gets_a_go_ahead(world, extra):
    world.says("lock the look")
    assert world.decision(LOCK_VISUAL, **extra) == "deny"


@pytest.mark.parametrize("after", [task_notification(), peer(), peer("lock the look"),
                                   human("lock the look", isSidechain=True, agentId="a1")])
def test_a_later_message_not_from_kieran_cancels_it(world, after):
    world.says("lock the look", after)
    assert world.decision(LOCK_VISUAL) == "deny"


def test_harness_notes_and_tool_results_in_the_turn_are_skipped(world):
    world.says("lock the look", meta(), tool_result(), assistant(), tool_result())
    assert world.decision(LOCK_VISUAL) == "allow"


def test_a_message_with_an_image_still_counts(world):
    world.says([{"type": "image", "source": {"type": "base64", "data": ""}},
                {"type": "text", "text": "approve cover v1"}])
    assert world.decision(COVER_V1) == "allow"


def test_a_message_from_another_session_is_ignored(world):
    world.says("lock the look", session="another-session")
    assert world.decision(LOCK_VISUAL) == "deny"


@pytest.mark.parametrize("minutes,expected", [(59, "allow"), (61, "deny"), (-30, "deny")])
def test_a_message_older_than_an_hour_is_ignored(world, minutes, expected):
    world.says("lock the look", minutes_ago=minutes)
    assert world.decision(LOCK_VISUAL) == expected


def test_a_transcript_outside_claude_projects_is_ignored(world, tmp_path):
    world.says("lock the look")
    elsewhere = tmp_path / "fake.jsonl"
    elsewhere.write_text(world.transcript.read_text())
    assert world.decision(LOCK_VISUAL, transcript_path=str(elsewhere)) == "deny"
    link = world.transcripts / "link.jsonl"
    link.symlink_to(elsewhere)
    assert world.decision(LOCK_VISUAL, transcript_path=str(link)) == "deny"


def test_a_big_transcript_is_read_from_the_end(world):
    world.entries = [human("hello")] + [tool_result("x" * 5000) for _ in range(400)]
    world.says("lock the look", *[tool_result("y" * 5000) for _ in range(50)])
    assert world.transcript.stat().st_size > 2_000_000
    assert world.decision(LOCK_VISUAL) == "allow"


# -- findings D and F: the guard's own files and the transcripts ---------------

def _config_writes(world: World) -> list[str]:
    t = world.transcript
    return [
        "echo '{}' > .claude/state/go-ahead.json",
        "printf x | tee .claude/settings.json",
        "echo x > .claude/hooks/guard-authority.py",
        "mv .claude/hooks/guard-authority.py /tmp/g.py",
        "mv .claude .claude-old",
        "rm .claude/settings.json",
        "rm -rf .claude",
        "echo '{}' > .claude/settings.local.json",
        "cp /tmp/settings.json .claude/",
        "ln -sf /tmp/x .claude/hooks/guard-authority.py",
        "chmod -x .claude/hooks/guard-authority.py",
        f"echo '{{}}' >> {t}",
        f"sed -i 's/a/b/' {t}",
        "rm -rf ~/.claude/projects",
        f"cp /tmp/x.jsonl {t.parent}/",
        f"python3 -c \"open('{t}', 'a').write('x')\"",
        "python3 -c \"import os;p=os.path.join('.claude',chr(115)+'tate','slip');"
        "f=open(p,'w')\"",
        "perl -e 'open(F,\">.claude/state/go-ahead.json\")'",
        "awk 'BEGIN{print \"x\" > \".claude/settings.json\"}'",
        "sort -o .claude/settings.json /tmp/x",
        "split -b 10 /tmp/x .claude/hooks/x",
        "vim -c 'w! .claude/settings.json' -c q",
        "ex -sc 'w! .claude/hooks/guard-authority.py|q'",
        "tar -xf /tmp/x.tar",
        "tar -xf /tmp/x.tar -C .claude",
        "tar xf /tmp/x.tar -C .",
        "unzip -o /tmp/x.zip -d .",
        "unzip -o /tmp/x.zip",
        "cp -r /tmp/fake/. .",
        "cp -rT /tmp/fake .",
        "rsync -a /tmp/fake/ ./",
        "mv /tmp/fake/.claude .",
        "git apply /tmp/p.patch",
        "patch -p0 < /tmp/p.patch",
        "cd .claude && echo x > settings.json",
        "cd .claude/hooks && rm guard-authority.py",
        "find .claude -name '*.py' -delete",
        "bash -c \"echo x > .claude/settings.json\"",
    ]


def test_claude_can_never_change_the_guard_or_the_transcript(world):
    for command in _config_writes(world):
        verdict, reason = world.guard(command, mode="default")
        assert verdict == "deny", command
        assert "Claude never does that" in reason or "patch" in reason, command


def test_reading_them_and_ordinary_work_is_fine(world):
    t = world.transcript
    for command in (f"tail -5 {t}", "cat .claude/settings.json", "ls -la .claude/hooks",
                    "git diff .claude/settings.json", "grep -n allow .claude/settings.json",
                    "cp .claude/settings.json /tmp/settings-copy.json",
                    "cp /tmp/x.png .", "tar -tf /tmp/x.tar",
                    "tar -xf /tmp/x.tar -C /tmp/out", "unzip -o /tmp/x.zip -d /tmp/out",
                    "git apply --check /tmp/p.patch", "cp -r /tmp/fake /tmp/fake2",
                    "python3 -m pytest -q tests/test_hook_go_ahead.py"):
        assert world.decision(command, mode="default") == "none", command


def test_settings_deny_edits_to_the_guard_and_transcripts():
    settings = json.loads((REPO / ".claude" / "settings.json").read_text())
    deny = settings["permissions"]["deny"]
    for tool in ("Edit", "Write"):
        for path in (".claude/state/**", ".claude/hooks/**", ".claude/settings.json",
                     ".claude/settings.local.json", "~/.claude/projects/**"):
            assert f"{tool}({path})" in deny
    # no slip recorder: the guard trusts only the transcript
    assert "UserPromptSubmit" not in settings["hooks"]
