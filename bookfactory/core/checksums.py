"""SHA-256 checksums and approved-artefact immutability.

Approved artefacts are protected in two layers:

1.  *Convention and permissions* - the file is made read-only (0444) on
    promotion, so an accidental overwrite fails at the OS level.
2.  *Verification* - every approved artefact has a recorded SHA-256. Any QA
    run, assembly, or `validate` recomputes it. A mismatch is a hard failure.

Layer 2 is the one that matters: file permissions can be defeated, a checksum
cannot be quietly wrong.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
from pathlib import Path

from bookfactory.core.errors import ChecksumMismatch, ImmutableAssetError

READ_ONLY = 0o444
CHUNK = 1024 * 1024


def sha256_file(path: str | Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def verify(path: str | Path, expected: str) -> None:
    """Raise ChecksumMismatch if the file does not match. Never repairs."""
    path = Path(path)
    if not path.exists():
        raise ChecksumMismatch(str(path), expected, "<file missing>")
    actual = sha256_file(path)
    if actual != expected:
        raise ChecksumMismatch(str(path), expected, actual)


def matches(path: str | Path, expected: str) -> bool:
    try:
        verify(path, expected)
        return True
    except ChecksumMismatch:
        return False


def make_immutable(path: str | Path) -> None:
    """Mark an approved artefact read-only."""
    os.chmod(path, READ_ONLY)


def is_immutable(path: str | Path) -> bool:
    mode = os.stat(path).st_mode
    return not bool(mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def unlock_for_system(path: str | Path) -> None:
    """Only Book Factory's own approval machinery may unlock an approved file,
    and only to archive it during an explicit revision."""
    os.chmod(path, 0o644)


def copy_into_approved(source: str | Path, destination: str | Path,
                       *, allow_replace: bool = False) -> str:
    """Copy a draft into the approved tree and lock it. Returns the SHA-256.

    Refuses to clobber an existing approved artefact unless the caller has gone
    through the revision workflow (`allow_replace=True`).
    """
    source = Path(source)
    destination = Path(destination)
    if destination.exists() and not allow_replace:
        raise ImmutableAssetError(
            f"Approved artefact already exists: {destination}",
            remedy=(
                "Approved artefacts are immutable. Open an explicit revision with "
                "`bookfactory revise <book> <id>` before submitting a replacement."
            ),
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        unlock_for_system(destination)
        destination.unlink()
    shutil.copy2(source, destination)
    make_immutable(destination)
    return sha256_file(destination)
