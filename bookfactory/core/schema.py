"""JSON Schema validation.

Schemas live in `schemas/` at the repository root so that ChatGPT, a future MCP
server, or any other tool can read them without importing Python. They are the
published contract; this module is just the Python-side validator.

Validation is applied when state files are written and when they are read back
by `validate`/`qa`, so a hand-edited file that breaks the contract is caught at
the next command rather than three stages later.
"""

from __future__ import annotations

import functools
from pathlib import Path

from bookfactory.core.errors import ValidationError

SCHEMA_FILES = {
    "book": "book.schema.json",
    "page-manifest": "page-manifest.schema.json",
    "page-spec": "page-spec.schema.json",
    "asset": "asset.schema.json",
    "task": "task.schema.json",
    "qa-report": "qa-report.schema.json",
    "cover": "cover.schema.json",
}


@functools.lru_cache(maxsize=1)
def schema_dir() -> Path | None:
    """Find `schemas/`. Works from a repo checkout and from an installed copy."""
    candidates = []
    from bookfactory.core.paths import repo_root

    candidates.append(repo_root() / "schemas")
    here = Path(__file__).resolve()
    candidates.extend(parent / "schemas" for parent in here.parents[:4])
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "book.schema.json").is_file():
            return candidate
    return None


@functools.lru_cache(maxsize=16)
def load_schema(name: str) -> dict | None:
    directory = schema_dir()
    if directory is None:
        return None
    filename = SCHEMA_FILES.get(name)
    if not filename:
        raise ValidationError(f"Unknown schema {name!r}")
    path = directory / filename
    if not path.is_file():
        return None
    import json

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(name: str, data: dict, *, context: str = "") -> None:
    """Validate `data` against the named schema.

    If jsonschema or the schema file is unavailable the call is a no-op - the
    dataclass layer still enforces the important invariants, so a missing
    optional dependency degrades checking rather than breaking production.
    """
    schema = load_schema(name)
    if schema is None:
        return
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - optional dependency
        return

    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    if errors:
        problems = []
        for error in errors[:20]:
            location = "/".join(str(part) for part in error.path) or "<root>"
            problems.append(f"{location}: {error.message}")
        where = f" in {context}" if context else ""
        raise ValidationError(
            f"{name} state{where} does not match schemas/{SCHEMA_FILES[name]}",
            problems=problems,
            remedy="Fix the file by hand or restore it from git history.",
        )
