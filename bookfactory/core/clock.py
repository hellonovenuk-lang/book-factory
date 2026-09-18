"""Single source of 'now'.

Isolated so tests can freeze time and so timestamps are always UTC ISO-8601.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone


def now() -> datetime:
    override = os.environ.get("BOOKFACTORY_FAKE_NOW")
    if override:
        return datetime.fromisoformat(override.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def timestamp() -> str:
    return now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact_timestamp() -> str:
    return now().strftime("%Y%m%dT%H%M%SZ")
