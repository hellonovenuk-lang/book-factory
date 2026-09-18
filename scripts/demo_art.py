"""Placeholder artwork generator for the synthetic demo book.

This is NOT part of Book Factory. It exists so the demo fixture has real image
files with real pixels and real checksums without shipping binary artwork in
the repository, and without pretending an image model ran.

Real books get their artwork from an image-generating agent, submitted as
drafts through `bookfactory submit`.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

PAPER = (251, 248, 241)
INK = (28, 26, 23)
PALETTE = [
    (140, 59, 46),    # accent
    (230, 215, 195),  # accent soft
    (96, 110, 84),    # sage
    (201, 189, 168),  # rule
    (74, 69, 62),     # soft ink
]


def _blob(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float,
          rng: random.Random, fill, outline=None, width: int = 0) -> None:
    points = []
    steps = rng.randint(7, 11)
    for index in range(steps):
        angle = (2 * math.pi * index) / steps
        wobble = radius * rng.uniform(0.72, 1.28)
        points.append((cx + math.cos(angle) * wobble, cy + math.sin(angle) * wobble * 0.86))
    draw.polygon(points, fill=fill, outline=outline, width=width)


def generate(path: str | Path, *, width: int, height: int, seed: str,
             shapes: int = 8) -> Path:
    """Deterministic abstract illustration. Same seed, same pixels, same checksum."""
    rng = random.Random(seed)
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)

    #: soft ground wash
    for _ in range(3):
        colour = PALETTE[rng.randrange(len(PALETTE))]
        tinted = tuple(int(c * 0.12 + p * 0.88) for c, p in zip(colour, PAPER))
        _blob(draw, rng.uniform(0, width), rng.uniform(0, height),
              max(width, height) * rng.uniform(0.35, 0.6), rng, tinted)
    image = image.filter(ImageFilter.GaussianBlur(radius=max(width, height) / 90))
    draw = ImageDraw.Draw(image)

    stroke = max(2, int(min(width, height) / 220))
    for _ in range(shapes):
        colour = PALETTE[rng.randrange(len(PALETTE))]
        _blob(draw,
              rng.uniform(width * 0.22, width * 0.78),
              rng.uniform(height * 0.22, height * 0.78),
              min(width, height) * rng.uniform(0.07, 0.17),
              rng, colour, outline=INK, width=stroke)

    #: a few ink strokes, so it reads as drawn rather than generated noise
    for _ in range(rng.randint(5, 9)):
        x1 = rng.uniform(width * 0.1, width * 0.9)
        y1 = rng.uniform(height * 0.1, height * 0.9)
        length = min(width, height) * rng.uniform(0.08, 0.22)
        angle = rng.uniform(0, math.pi)
        draw.line([(x1, y1), (x1 + math.cos(angle) * length, y1 + math.sin(angle) * length)],
                  fill=INK, width=max(1, stroke // 2))

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)
    return path


if __name__ == "__main__":  # pragma: no cover
    import sys

    generate(sys.argv[1], width=1800, height=1350, seed=sys.argv[2] if len(sys.argv) > 2 else "x")
