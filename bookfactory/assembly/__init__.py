"""Assembly and review output.

Assembly is mechanical. It reads the page manifest, verifies every approved
artefact against its checksum, and concatenates them in order. It never
generates, rewrites, reinterprets or substitutes anything, and it fails rather
than guessing.
"""

from bookfactory.assembly.assemble import assemble  # noqa: F401  (re-export)
from bookfactory.assembly.review import generate_review  # noqa: F401  (re-export)
