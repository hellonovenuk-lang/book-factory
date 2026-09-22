"""Tests for the quick-check PostToolUse hook (.claude/hooks/quick-check.py).

The hook is a standalone script invoked by Claude Code with a JSON event on
stdin. These tests run it as a subprocess, exactly the way Claude Code would,
so they exercise the real contract: exit 0 with no output when the file is
fine or there's nothing to check, exit 2 with a stderr message when a .py or
.json/.jsonl file is broken.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "quick-check.py"


def run_hook(event, cwd=None):
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else str(REPO_ROOT),
    )


def event_for(file_path, tool_name="Write", cwd=None):
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path)},
        "tool_response": {},
        "cwd": str(cwd) if cwd else str(REPO_ROOT),
    }


def test_good_python_passes(tmp_path):
    f = tmp_path / "good.py"
    f.write_text("def foo():\n    return 1\n")
    result = run_hook(event_for(f))
    assert result.returncode == 0
    assert result.stderr == ""


def test_bad_python_fails(tmp_path):
    f = tmp_path / "bad.py"
    f.write_text("def foo(:\n    return 1\n")
    result = run_hook(event_for(f))
    assert result.returncode == 2
    assert str(f) in result.stderr
    assert "line" in result.stderr


def test_good_json_passes(tmp_path):
    f = tmp_path / "good.json"
    f.write_text(json.dumps({"a": 1}))
    result = run_hook(event_for(f))
    assert result.returncode == 0
    assert result.stderr == ""


def test_bad_json_fails(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text('{"a": 1,}')
    result = run_hook(event_for(f))
    assert result.returncode == 2
    assert str(f) in result.stderr


def test_good_jsonl_passes(tmp_path):
    f = tmp_path / "good.jsonl"
    f.write_text('{"a": 1}\n{"b": 2}\n\n{"c": 3}\n')
    result = run_hook(event_for(f))
    assert result.returncode == 0
    assert result.stderr == ""


def test_bad_jsonl_reports_first_bad_line(tmp_path):
    f = tmp_path / "bad.jsonl"
    f.write_text('{"a": 1}\nnot json\n{"c": 3}\n')
    result = run_hook(event_for(f))
    assert result.returncode == 2
    assert "line 2" in result.stderr


def test_markdown_file_ignored(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("# not checked (( unbalanced")
    result = run_hook(event_for(f))
    assert result.returncode == 0
    assert result.stderr == ""


def test_missing_file_exits_zero(tmp_path):
    f = tmp_path / "missing.py"
    result = run_hook(event_for(f))
    assert result.returncode == 0
    assert result.stderr == ""


def test_invalid_stdin_exits_zero():
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="not json at all",
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0
    assert result.stderr == ""


def test_relative_path_resolved_via_cwd(tmp_path):
    f = tmp_path / "bad_relative.py"
    f.write_text("def foo(:\n    pass\n")
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": "bad_relative.py"},
        "tool_response": {},
        "cwd": str(tmp_path),
    }
    result = run_hook(event, cwd=tmp_path)
    assert result.returncode == 2
    assert "bad_relative.py" in result.stderr
