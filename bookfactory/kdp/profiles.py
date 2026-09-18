"""Loading and querying KDP profiles."""

from __future__ import annotations

import functools
from pathlib import Path

from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import read_json

PROFILE_DIR = Path(__file__).resolve().parent / "profiles"
POINTS_PER_INCH = 72.0


def available_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILE_DIR.glob("*.json"))


@functools.lru_cache(maxsize=8)
def load_profile(profile_id: str = "kdp-default") -> dict:
    path = PROFILE_DIR / f"{profile_id}.json"
    if not path.is_file():
        raise ValidationError(
            f"Unknown KDP profile {profile_id!r}",
            remedy="Available profiles: " + ", ".join(available_profiles()),
        )
    return read_json(path)


def trim_inches(trim: str, profile_id: str = "kdp-default") -> tuple[float, float]:
    profile = load_profile(profile_id)
    sizes = profile["trim_sizes"]
    if trim not in sizes:
        raise ValidationError(
            f"Trim size {trim!r} is not in profile {profile_id}",
            remedy="Available trims: " + ", ".join(sorted(sizes)),
        )
    size = sizes[trim]
    return float(size["width_in"]), float(size["height_in"])


def trim_points(trim: str, profile_id: str = "kdp-default") -> tuple[float, float]:
    width, height = trim_inches(trim, profile_id)
    return width * POINTS_PER_INCH, height * POINTS_PER_INCH


def bleed_inches(profile_id: str = "kdp-default") -> float:
    return float(load_profile(profile_id)["bleed"]["edge_in"])


def required_gutter_in(page_count: int, profile_id: str = "kdp-default") -> float:
    bands = load_profile(profile_id)["margins"]["gutter_by_page_count_in"]
    for band in bands:
        if page_count <= band["max_pages"]:
            return float(band["gutter_in"])
    return float(bands[-1]["gutter_in"])


def min_outside_margin_in(*, bleed: bool, profile_id: str = "kdp-default") -> float:
    margins = load_profile(profile_id)["margins"]
    key = "outside_min_with_bleed_in" if bleed else "outside_min_in"
    return float(margins[key])
