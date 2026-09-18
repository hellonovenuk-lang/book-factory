"""Stable identifiers.

Filenames in the old workflow collided because they were derived from titles
("early_signs_of_progress.png" appearing in two chapters). In Book Factory the
ID is canonical identity and the title is only decoration.
"""

from __future__ import annotations

import re

from bookfactory.core.errors import ValidationError

BOOK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PAGE_ID_RE = re.compile(r"^p\d{3,4}$")
ASSET_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REVISION_RE = re.compile(r"^v\d+$")


def slugify(text: str) -> str:
    """Lower-case, hyphenated, ASCII-safe slug. Never used as canonical identity
    on its own - only as a readable suffix after an ID."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "untitled"


def make_book_id(title: str) -> str:
    return slugify(title)


def page_id(sequence: int) -> str:
    if sequence < 1:
        raise ValidationError(f"Page sequence must be >= 1, got {sequence}")
    return f"p{sequence:03d}"


def validate_book_id(value: str) -> str:
    if not BOOK_ID_RE.match(value or ""):
        raise ValidationError(
            f"Invalid book id {value!r}",
            remedy="Book ids are lower-case words joined by hyphens, e.g. 'golf-addict'.",
        )
    return value


def validate_page_id(value: str) -> str:
    if not PAGE_ID_RE.match(value or ""):
        raise ValidationError(
            f"Invalid page id {value!r}",
            remedy="Page ids look like 'p001' or 'p058'.",
        )
    return value


def validate_asset_id(value: str) -> str:
    if not ASSET_ID_RE.match(value or ""):
        raise ValidationError(
            f"Invalid asset id {value!r}",
            remedy="Asset ids are lower-case words joined by hyphens, e.g. 'p058-mate-taxonomy'.",
        )
    return value


def validate_revision(value: str) -> str:
    if not REVISION_RE.match(value or ""):
        raise ValidationError(
            f"Invalid revision {value!r}",
            remedy="Revisions look like 'v1', 'v2', 'v3'.",
        )
    return value


def revision_number(value: str) -> int:
    return int(validate_revision(value)[1:])


def next_revision(existing: list[str]) -> str:
    """Next free draft revision label given the revisions already on disk."""
    highest = 0
    for rev in existing:
        try:
            highest = max(highest, revision_number(rev))
        except ValidationError:
            continue
    return f"v{highest + 1}"


def canonical_filename(identifier: str, title: str | None, suffix: str) -> str:
    """ID-first filename. Collisions are structurally impossible because the ID
    is unique within the book and always leads."""
    suffix = suffix if suffix.startswith(".") else f".{suffix}"
    if title:
        return f"{identifier}-{slugify(title)}{suffix}"
    return f"{identifier}{suffix}"
