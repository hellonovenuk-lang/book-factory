"""Hard constraints on submitted artwork.

A task tells an agent what its output must satisfy. Some of those requirements
are judgements a machine cannot make - does the character match, is the style
right - and those stay with the operator. Others are measurable facts, and a
draft that fails one of those is not a candidate for approval at all: it is
work that has to be redone.

This module is the single place where those measurable requirements are
derived, so the task an agent receives and the check applied to what it submits
can never disagree. Adding a new hard constraint means adding one entry to
`HARD_CHECKS` and one key to `expected_constraints`.

Soft constraints are carried in the same dictionary but are never enforced
here; they are instructions to the agent and prompts for the human reviewer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp")

#: How much of the page width an illustration occupies at each placement.
#: Visual QA measures effective DPI against the same table, so the requirement
#: stated in a task is exactly the one QA will later enforce.
PLACEMENT_COVERAGE = {
    "full_bleed": 1.0,
    "full_page": 0.85,
    "top": 0.85,
    "bottom": 0.85,
    "left": 0.5,
    "right": 0.5,
    "inline": 0.6,
    "spot": 0.35,
}
DEFAULT_PLACEMENT = "full_page"


@dataclass
class ConstraintFailure:
    """A measurable requirement the submitted file does not meet."""

    constraint: str
    expected: Any
    actual: Any
    message: str
    remedy: str

    def to_dict(self) -> dict:
        return {
            "constraint": self.constraint,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
            "remedy": self.remedy,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConstraintFailure":
        return cls(**data)


# ----------------------------------------------------------------------
# What a task requires
# ----------------------------------------------------------------------


def minimum_width_px(book, placement: str | None) -> int:
    """Pixels of width needed to print at 300 DPI at this artwork's size."""
    from bookfactory.kdp import profiles

    profile_id = book.state.format.kdp_profile
    trim_width, _height = profiles.trim_inches(book.state.format.trim, profile_id)
    coverage = PLACEMENT_COVERAGE.get(placement or DEFAULT_PLACEMENT,
                                      PLACEMENT_COVERAGE[DEFAULT_PLACEMENT])
    required_dpi = int(profiles.load_profile(profile_id)["images"]["min_dpi"])
    return int(math.ceil(trim_width * coverage * required_dpi))


def expected_constraints(book, asset, *, placement: str | None = None) -> dict:
    """The constraint block published in a task for this asset.

    Hard entries - the ones named in HARD_CHECKS - are enforced on submission
    and again on approval. The rest are instructions.
    """
    #: A reference sheet is never printed, so "DPI at printed size" does not
    #: apply to it directly. It is still held to the full-page bar, because no
    #: generator produces 1530px of detail from a 600px reference - the artwork
    #: made from it inherits the reference's resolution.
    if placement is None and asset is not None and asset.is_reference:
        coverage_placement = DEFAULT_PLACEMENT
    else:
        coverage_placement = placement
    return {
        "embedded_text": False,
        "maintain_character_identity": True,
        "maintain_style": True,
        "colour": book.state.format.colour,
        "readable_image": True,
        "min_pixels": minimum_width_px(book, coverage_placement),
    }


def hard_constraints(expected: dict) -> dict:
    return {name: value for name, value in expected.items() if name in HARD_CHECKS}


# ----------------------------------------------------------------------
# The checks
# ----------------------------------------------------------------------


def _image_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.width, image.height
    except Exception:  # noqa: BLE001 - an unreadable file is the finding
        return None


def _check_readable_image(path: Path, expected: Any, context: dict) -> ConstraintFailure | None:
    if not expected or path.suffix.lower() not in IMAGE_SUFFIXES:
        return None
    if _image_size(path) is not None:
        return None
    return ConstraintFailure(
        constraint="readable_image",
        expected=True,
        actual=False,
        message=f"{path.name} is not a readable image file.",
        remedy="Re-export the artwork and submit it again.",
    )


def _check_min_pixels(path: Path, expected: Any, context: dict) -> ConstraintFailure | None:
    if not expected or path.suffix.lower() not in IMAGE_SUFFIXES:
        return None
    size = _image_size(path)
    if size is None:
        #: readable_image reports this; do not report it twice.
        return None
    width, height = size
    if width >= int(expected):
        return None
    placement = context.get("placement") or DEFAULT_PLACEMENT
    return ConstraintFailure(
        constraint="min_pixels",
        expected=int(expected),
        actual=width,
        message=(
            f"Artwork is {width}x{height}px. At its printed size "
            f"({placement.replace('_', ' ')}) it needs to be at least {int(expected)}px "
            f"wide to reach 300 DPI."
        ),
        remedy=(
            f"Generate the same picture at {int(expected)}px wide or more and submit it "
            "as a new draft. Do not upscale the existing file - it adds pixels, not detail."
        ),
    )


#: constraint name -> check. A constraint is hard exactly when it appears here.
HARD_CHECKS: dict[str, Callable[[Path, Any, dict], ConstraintFailure | None]] = {
    "readable_image": _check_readable_image,
    "min_pixels": _check_min_pixels,
}


def evaluate(path: str | Path, expected: dict, *, context: dict | None = None
             ) -> list[ConstraintFailure]:
    """Check a file against the hard constraints in `expected`."""
    path = Path(path)
    context = context or {}
    failures = []
    for name, value in expected.items():
        check = HARD_CHECKS.get(name)
        if check is None:
            continue
        failure = check(path, value, context)
        if failure is not None:
            failures.append(failure)
    return failures


def describe(failures: list[dict] | list[ConstraintFailure]) -> str:
    """One readable line per failure, for an error message or a task."""
    lines = []
    for failure in failures:
        data = failure if isinstance(failure, dict) else failure.to_dict()
        lines.append(f"{data['constraint']}: {data['message']}")
    return "\n  - ".join(lines)
