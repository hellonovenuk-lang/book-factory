"""Deterministic JSON reading and writing.

Every state file is written the same way every time: 2-space indent, sorted
nothing (key order is authored order), trailing newline, UTF-8. Writes are
atomic so a crash never leaves half a state file behind.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from bookfactory.core.errors import ValidationError


def read_json(path: str | Path) -> Any:
    path = Path(path)
    if not path.exists():
        raise ValidationError(
            f"Missing state file: {path}",
            remedy="Run `bookfactory validate <book>` to see what is missing.",
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"{path} is not valid JSON: {exc}",
            remedy="Fix the file by hand or restore it from git history.",
        ) from exc


def dumps(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def write_json(path: str | Path, data: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dumps(data)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".bf-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path


def append_jsonl(path: str | Path, record: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def read_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{path}:{line_no} is not valid JSON: {exc}") from exc
    return records
