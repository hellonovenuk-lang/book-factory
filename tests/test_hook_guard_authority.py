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


def run_hook(stdin: str, env: dict | None = None
             ) -> tuple[str, dict | None, subprocess.CompletedProcess]:
    proc = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True,
                          text=True, timeout=30, env=env)
    out = proc.stdout.strip()
    if not out:
        return "allow", None, proc
    data = json.loads(out)
    spec = data["hookSpecificOutput"]
    return spec["permissionDecision"], spec, proc


def decide(command: str, *, tool: str = "Bash", cwd: str | None = None,
           mode: str | None = "default", env: dict | None = None) -> str:
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool,
               "tool_input": {"command": command}}
    if mode is not None:
        payload["permission_mode"] = mode
    if cwd is not None:
        payload["cwd"] = cwd
    decision, spec, proc = run_hook(json.dumps(payload), env)
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


# `--autonomous` steps an agent may run itself: Book Factory refuses them
# unless the book's recorded production policy authorizes them (AGENTS.md
# section 3), so the guard leaves that judgement to Book Factory.
AUTONOMOUS_ALLOWS = [
    "bookfactory approve demo-book --all-passing --by agent --autonomous",
    "bookfactory approve demo-book p001 --autonomous --by claude",
    "bookfactory lock concept demo-book --by claude --autonomous",
    "bookfactory lock manuscript demo-book --autonomous",
    "bookfactory --json lock voice demo-book --autonomous --by=claude",
    "bookfactory cover approve demo-book --draft v2 --by claude --autonomous",
    "python3 -m bookfactory.cli.main lock visual demo-book --autonomous --by claude",
]

# Still the operator's, with or without `--autonomous`.
AUTONOMOUS_ASKS = [
    "bookfactory lock concept demo-book --by kieran --autonomous",
    "bookfactory approve demo-book p001 --autonomous --by Kieran",
    "bookfactory lock concept demo-book --note --autonomous",
    "bookfactory lock concept demo-book --by --autonomous",
    "bookfactory lock concept demo-book $(echo --autonomous)",
    "bookfactory lock concept demo-book --autonomous --note \"$(whoami)\"",
    "bookfactory reject demo-book p001 --autonomous --reason blurry",
    "bookfactory revise demo-book p058 --autonomous --reason typo",
    "bookfactory policy set demo-book autonomous --by claude --autonomous",
    "bookfactory pictures set demo-book unlimited --by claude --autonomous",
    "bookfactory advance demo-book --autonomous",
    "bookfactory assemble demo-book --autonomous",
    "bookfactory preflight demo-book --autonomous",
    "bookfactory cover finalize demo-book --draft v1 --autonomous",
    "bookfactory cover preflight demo-book --autonomous",
    "bookfactory lock concept demo-book --autonomous; bookfactory revise demo-book p001",
]


@pytest.mark.parametrize("command", AUTONOMOUS_ALLOWS)
def test_allows_autonomous_steps_book_factory_checks_itself(command):
    assert decide(command) == "allow"
    assert decide(command, mode="auto") == "allow"


@pytest.mark.parametrize("command", AUTONOMOUS_ASKS)
def test_autonomous_never_unlocks_operator_only_commands(command):
    assert decide(command) == "ask"


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


# ----------------------------------------------------------------------
# The last release steps, when the book's own next task asks for them
# ----------------------------------------------------------------------
#
# `advance <book> --to release_ready`, `cover finalize` and `cover preflight`
# have no `--autonomous` flag, so the guard reads the book's next task itself
# and lets the step through only when that task is exactly this step with mode
# `continue_automatically` (which already encodes the recorded policy).

import importlib.util  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402

RB = "test-book"
RELEASE_STAGES = ("finalize", "cover_preflight", "release")


def _clean_env() -> dict:
    env = dict(os.environ)
    env.pop("BOOKFACTORY_ROOT", None)
    return env


def _pdf_pages(path: Path, pages: int) -> None:
    from reportlab.pdfgen import canvas

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(432, 648))
    for _ in range(pages):
        pdf.showPage()
    pdf.save()


def _text_only_wrap(book, folder: Path) -> Path:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    from bookfactory.core import cover

    dim = cover.dimensions(book)
    wrap = folder / "wrap.pdf"
    pdfmetrics.registerFont(TTFont("GuardCoverTest",
                                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdf = canvas.Canvas(str(wrap), pagesize=(dim["width_in"] * 72, dim["height_in"] * 72))
    pdf.setFont("GuardCoverTest", 18)
    pdf.drawString(6.6 * 72, 8 * 72, "Test Book")
    pdf.drawString(6.6 * 72, .5 * 72, "A Writer")
    pdf.drawString(.5 * 72, 5 * 72, "Gift for runners")
    pdf.save()
    return wrap


@pytest.fixture(scope="module")
def release_books(tmp_path_factory) -> dict[str, Path]:
    """One real book, snapshotted at each release step (built once: rendering is slow).

    Interior preflight needs a KDP-length book, so the test writes an 80-page
    interior and a passing interior preflight report; everything else - the
    text-only cover draft, its provisional review approval, finalize and the
    cover preflight - goes through Book Factory itself.
    """
    from bookfactory.core import api, checksums, cover
    from bookfactory.core.book import ASSET, PAGE, Book
    from bookfactory.core.jsonio import write_json
    from tests.conftest import (BRIEF, MANUSCRIPT, PAGE_PLAN, SAMPLE, VISUAL, VOICE,
                                make_image)

    ws = tmp_path_factory.mktemp("guard-release") / "work"
    (ws / "books").mkdir(parents=True)
    staging = ws / "staging"
    api.create_book("Test Book", policy="visual_checkpoint", book_id=RB, root=ws,
                    idea="A small book used to prove the production system works.")
    book = Book.load(RB, ws)
    book.paths.brief_file.write_text(BRIEF, encoding="utf-8")
    book.paths.voice_bible.write_text(VOICE, encoding="utf-8")
    book.paths.writing_sample_file.write_text(SAMPLE, encoding="utf-8")
    book.paths.manuscript_file.write_text(MANUSCRIPT, encoding="utf-8")
    book.paths.visual_bible.write_text(VISUAL, encoding="utf-8")
    book.save()
    for stage in ("concept", "voice", "manuscript"):
        api.lock(RB, stage, root=ws, by="tester")
    book = Book.load(RB, ws)
    for index, item in enumerate(book.reference_set()["required"]):
        asset_id = item["asset_id"]
        api.register_asset(RB, asset_id, root=ws, kind=item["kind"], title=item["title"],
                           description=item["description"])
        art = make_image(staging / f"{asset_id}.png", (1800, 1800), seed=index)
        api.submit_asset(RB, asset_id, art, kind=ASSET, root=ws)
        api.approve(RB, asset_id, kind=ASSET, root=ws, by="tester")
    api.lock(RB, "visual", root=ws, by="tester")
    api.set_pictures(RB, "unlimited", by="tester", root=ws)
    api.plan_pages(RB, [{k: v for k, v in p.items() if k != "spec"} for p in PAGE_PLAN],
                   root=ws)
    book = Book.load(RB, ws)
    for index, page in enumerate(PAGE_PLAN, start=1):
        book.write_page_spec(f"p{index:03d}", page["spec"])
    book.save()
    art = make_image(staging / "fig-scope.png", (1800, 1350), seed=9)
    api.submit_asset(RB, "fig-scope", art, kind=ASSET, root=ws)
    api.approve(RB, "fig-scope", kind=ASSET, root=ws, by="tester")
    for index in range(1, len(PAGE_PLAN) + 1):
        api.render(RB, page_id=f"p{index:03d}", submit=True, root=ws)
        api.approve(RB, f"p{index:03d}", kind=PAGE, root=ws, by="tester")
    api.qa(RB, root=ws)

    book = Book.load(RB, ws)
    interior = book.paths.interior_pdf
    _pdf_pages(interior, 80)
    write_json(book.paths.preflight_report, {"status": "pass", "checks": []})
    data = cover.load(book)
    data.update(direction="Type only", author="A Writer", back_copy="Gift for runners")
    cover.save(book, data)
    cover.set_artwork(book, cover.TEXT_ONLY, by="Test Operator", reason="Operator choice")

    # A provisional review approval, sized from a preserved interior, leaves
    # the finalize step next once the final interior is back.
    book = Book.load(RB, ws)
    preserved = book.paths.root / "releases" / "preserved.pdf"
    preserved.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(interior, preserved)
    interior.unlink()
    data = cover.load(book)
    data["preview_interior"] = {"path": "releases/preserved.pdf",
                                "sha256": checksums.sha256_file(preserved)}
    cover.save(book, data)
    draft = cover.submit(book, _text_only_wrap(book, ws))
    assert cover.approve(Book.load(RB, ws), draft["revision"], by="Operator")["status"] \
        == "review_approved"
    shutil.copy(preserved, interior)

    base = tmp_path_factory.mktemp("guard-release-snapshots")
    snapshots = {}

    def snap(name, task_id):
        assert api.next_task(RB, root=ws)["task_id"] == f"{RB}-{task_id}"
        snapshots[name] = base / name
        shutil.copytree(ws / "books", snapshots[name] / "books")

    snap("finalize", "cover-finalize")
    cover.finalize(Book.load(RB, ws), draft["revision"])
    snap("cover_preflight", "cover-preflight")
    assert cover.preflight(Book.load(RB, ws))["status"] == "pass"
    snap("release", "release")
    return snapshots


@pytest.fixture
def release_ws(release_books, tmp_path):
    """A fresh copy of the book at a release step, with a chosen policy."""
    from bookfactory.core import production
    from bookfactory.core.book import Book

    def make(stage: str, policy: str = "visual_checkpoint") -> Path:
        ws = tmp_path / stage
        shutil.copytree(release_books[stage], ws)
        book = Book.load(RB, ws)
        book.state.production_policy = production.policy_from_choice(policy)
        book.save()
        return ws
    return make


def _next(ws: Path) -> dict:
    from bookfactory.core import api
    return api.next_task(RB, root=ws)


RELEASE_COMMANDS = {
    "release": "bookfactory advance test-book --to release_ready",
    "finalize": "bookfactory cover finalize test-book --draft v1",
    "cover_preflight": "bookfactory cover preflight test-book",
}


@pytest.mark.parametrize("stage", RELEASE_STAGES)
def test_a_release_step_the_next_task_asks_for_is_let_through(release_ws, stage):
    ws = release_ws(stage)
    assert _next(ws)["mode"] == "continue_automatically"
    command = f"{RELEASE_COMMANDS[stage]} --root {ws}"
    env = _clean_env()
    assert decide(command, env=env) == "allow"
    assert decide(command, mode="auto", env=env) == "allow"


@pytest.mark.parametrize("command", [
    "bookfactory --root {ws} --json advance test-book --to=release_ready --by claude",
    "bookfactory advance test-book --to release_ready --json --note 'all passed' --root={ws}",
    "BOOKFACTORY_ROOT={ws} bookfactory advance test-book --to release_ready",
])
def test_release_allowed_in_every_plain_spelling(release_ws, command):
    ws = release_ws("release")
    assert decide(command.format(ws=ws), mode="auto", env=_clean_env()) == "allow"


def test_the_root_is_found_from_the_sessions_folder(release_ws):
    ws = release_ws("cover_preflight")
    assert decide("bookfactory cover preflight test-book", cwd=str(ws), mode="auto",
                  env=_clean_env()) == "allow"
    # ... and from BOOKFACTORY_ROOT in the environment, as the program would.
    assert decide("bookfactory cover preflight test-book", cwd="/", mode="auto",
                  env={**_clean_env(), "BOOKFACTORY_ROOT": str(ws)}) == "allow"


@pytest.mark.parametrize("stage", RELEASE_STAGES)
def test_a_checkpointed_book_still_asks(release_ws, stage):
    ws = release_ws(stage, "checkpointed")
    if stage != "release":
        # The cover steps wait under checkpointed when QA only warned.
        from bookfactory.core.book import Book
        from bookfactory.core.jsonio import read_json, write_json
        latest = Book.load(RB, ws).paths.qa_latest
        report = read_json(latest)
        report["summary"]["status"] = "warn"
        write_json(latest, report)
    assert _next(ws)["mode"] == "wait_for_operator"
    assert decide(f"{RELEASE_COMMANDS[stage]} --root {ws}", env=_clean_env()) == "ask"
    assert decide(f"{RELEASE_COMMANDS[stage]} --root {ws}", mode="auto",
                  env=_clean_env()) == "deny"


@pytest.mark.parametrize("stage,command", [
    (stage, command) for stage in RELEASE_STAGES
    for key, command in RELEASE_COMMANDS.items() if key != stage
])
def test_a_release_step_the_next_task_does_not_ask_for_still_asks(release_ws, stage, command):
    ws = release_ws(stage)
    assert decide(f"{command} --root {ws}", env=_clean_env()) == "ask"


@pytest.mark.parametrize("command", [
    "bookfactory advance test-book --to release_ready --force --root {ws}",
    "bookfactory advance test-book --to release_ready --forc --root {ws}",
    "bookfactory advance test-book --root {ws}",
    "bookfactory advance test-book --to cover_preflight --root {ws}",
    "bookfactory advance test-book --to release_ready --to release_ready --root {ws}",
    "bookfactory advance test-book --t release_ready --root {ws}",
    "bookfactory advance test-book --to release_ready --by kieran --root {ws}",
    "bookfactory advance test-book --to release_ready --autonomous --root {ws}",
    "bookfactory advance test-book other-book --to release_ready --root {ws}",
    "B=test-book; bookfactory advance $B --to release_ready --root {ws}",
    "bookfactory advance \"$(echo test-book)\" --to release_ready --root {ws}",
    "bookfactory advance test-bo* --to release_ready --root {ws}",
    "bookfactory advance test-book --to release_ready --note \"$(whoami)\" --root {ws}",
    "bookfactory advance no-such-book --to release_ready --root {ws}",
    "bookfactory advance test-book --to release_ready --root {ws}/nowhere",
    "bookfactory advance test-book --to release_ready --root {ws} --root /tmp",
    "cd {ws} && bookfactory advance test-book --to release_ready",
    "sudo bookfactory advance test-book --to release_ready --root {ws}",
    "timeout 30 bookfactory advance test-book --to release_ready --root {ws}",
    "echo test-book | xargs bookfactory advance --to release_ready --root {ws}",
    "python3 -m bookfactory advance test-book --to release_ready --root {ws}",
    "bookfactory advance test-book --to release_ready --root {ws}; bookfactory assemble test-book",
])
def test_release_advance_asks_unless_plain_and_asked_for(release_ws, command):
    ws = release_ws("release")
    assert decide(command.format(ws=ws), env=_clean_env()) == "ask"


@pytest.mark.parametrize("command", [
    "bookfactory cover finalize test-book --draft v2 --root {ws}",
    "bookfactory cover finalize test-book --draft $D --root {ws}",
    "bookfactory cover finalize $B --draft v1 --root {ws}",
    "bookfactory cover finalize test-book --draft v1 --autonomous --root {ws}",
    "bookfactory cover finalize test-book --draft v1 --force --root {ws}",
    "bookfactory cover finalize no-such-book --draft v1 --root {ws}",
    "find . -maxdepth 0 -exec bookfactory cover finalize test-book --draft v1 --root {ws} ;",
])
def test_cover_finalize_asks_unless_plain_and_asked_for(release_ws, command):
    ws = release_ws("finalize")
    assert decide(command.format(ws=ws), env=_clean_env()) == "ask"


@pytest.mark.parametrize("command", [
    "bookfactory cover preflight $B --root {ws}",
    "bookfactory cover preflight test-book --draft v1 --root {ws}",
    "bookfactory cover preflight test-book extra --root {ws}",
    "bookfactory cover preflight test-book --autonomous --root {ws}",
    "bookfactory cover preflight ../test-book --root {ws}",
    "env BOOKFACTORY_ROOT={ws} bookfactory cover preflight test-book",
])
def test_cover_preflight_asks_unless_plain_and_asked_for(release_ws, command):
    ws = release_ws("cover_preflight")
    assert decide(command.format(ws=ws), env=_clean_env()) == "ask"


def test_other_authority_commands_are_unchanged_when_a_release_step_is_next(release_ws):
    ws = release_ws("release", "autonomous")
    for command in ("bookfactory assemble test-book", "bookfactory preflight test-book",
                    "bookfactory reject test-book p001 --reason x",
                    "bookfactory revise test-book p001 --reason x",
                    "bookfactory policy set test-book autonomous --by claude",
                    "bookfactory pictures set test-book unlimited --by claude",
                    "bookfactory advance test-book --force"):
        assert decide(f"{command} --root {ws}", env=_clean_env()) == "ask", command


def test_an_unreadable_book_asks(release_ws):
    ws = release_ws("cover_preflight")
    (ws / "books" / RB / "book.json").write_text("{not json", encoding="utf-8")
    assert decide(f"bookfactory cover preflight test-book --root {ws}",
                  env=_clean_env()) == "ask"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_authority_under_test", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("failure", ["timeout", "crash", "garbage", "not_a_dict", "exit_1"])
def test_a_failed_lookup_asks(release_ws, monkeypatch, failure):
    ws = release_ws("cover_preflight")
    hook = _load_hook()
    command = f"bookfactory cover preflight test-book --root {ws}"
    assert hook.decide({"tool_name": "Bash", "tool_input": {"command": command}})[0] == "allow"

    def broken_run(*args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args[0], 10)
        if failure == "crash":
            raise OSError("no python")
        out = {"garbage": "not json", "not_a_dict": "[1, 2]", "exit_1": "{}"}[failure]
        return subprocess.CompletedProcess(args[0], 1 if failure == "exit_1" else 0, out, "")
    monkeypatch.setattr(hook.subprocess, "run", broken_run)
    decision, reason = hook.decide({"tool_name": "Bash", "tool_input": {"command": command}})
    assert decision == "ask"
    assert "`bookfactory cover preflight`" in reason


# -- options before a cover/policy/pictures operation (found in Phase 19) -----

@pytest.mark.parametrize("command", [
    "bookfactory cover --root /tmp/x finalize golf --draft v3",
    "bookfactory cover --root=/tmp/x preflight golf",
    "bookfactory policy --root /tmp/x set golf autonomous --by claude",
    "bookfactory pictures --root /tmp/x set golf unlimited --by claude",
    "bookfactory cover --weird finalize golf",
])
def test_an_option_before_the_operation_cannot_hide_it(command):
    assert decide(command) != "allow"


def test_a_read_only_cover_command_after_root_is_still_allowed():
    assert decide("bookfactory cover --root /tmp/x dimensions golf") == "allow"
