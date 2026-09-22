#!/usr/bin/env python3
"""PostToolUse hook: quick syntax check for .py/.json/.jsonl files just saved.

Reads a Claude Code PostToolUse event on stdin, looks at the file path in
``tool_input.file_path``, and checks that file's syntax. It never runs or
imports the file - it only parses it.

Exit codes:
- 0: nothing wrong (or nothing to check, or the input couldn't be read).
- 2: the file has a syntax error. A short message is printed to stderr so
  Claude Code can show it and fix the file.

This hook must never get in the way: any unexpected condition (missing
file, bad stdin, unreadable file, unsupported extension) is treated as
"nothing to check" and it exits 0 silently.
"""

import ast
import json
import os
import sys


def check_python(path, text):
    try:
        ast.parse(text, filename=path)
    except SyntaxError as exc:
        line = exc.lineno if exc.lineno is not None else "?"
        return f"quick-check: {path} line {line} won't parse: {exc.msg}. Fix it before going on."
    return None


def check_json(path, text):
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        return f"quick-check: {path} line {exc.lineno} won't parse: {exc.msg}. Fix it before going on."
    return None


def check_jsonl(path, text):
    for i, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            return f"quick-check: {path} line {i} won't parse: {exc.msg}. Fix it before going on."
    return None


def main():
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except Exception:
        return 0

    if not isinstance(event, dict):
        return 0

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0

    if not os.path.isabs(file_path):
        cwd = event.get("cwd")
        if isinstance(cwd, str) and cwd:
            file_path = os.path.join(cwd, file_path)

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".py", ".json", ".jsonl"):
        return 0

    if not os.path.isfile(file_path):
        return 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return 0

    if ext == ".py":
        error = check_python(file_path, text)
    elif ext == ".json":
        error = check_json(file_path, text)
    else:
        error = check_jsonl(file_path, text)

    if error:
        print(error, file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
