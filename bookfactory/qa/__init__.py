"""Quality assurance.

Four layers, run together but reported separately, because they fail for
different reasons and are fixed by different people:

* content   - words
* visual    - pictures
* technical - dimensions, checksums, sequence, print compliance
* assembly  - is this book safe to assemble at all

Anything a machine cannot decide (is this joke landing? has the character
drifted?) is reported as `needs_human` rather than silently passed.
"""

from bookfactory.qa.findings import Finding, LayerResult  # noqa: F401  (re-export)
from bookfactory.qa.runner import run_qa  # noqa: F401  (re-export)
