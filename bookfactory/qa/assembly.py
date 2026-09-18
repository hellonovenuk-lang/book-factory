"""Assembly QA - the gate immediately before the PDF is built.

This layer is the fail-closed one. It never approves a near-enough file.
"""

from __future__ import annotations

from bookfactory.core import checksums
from bookfactory.qa.findings import LayerResult

APPROVED_PREFIXES = ("pages/approved/",)


def check(book) -> LayerResult:
    result = LayerResult("assembly")

    if len(book.manifest) == 0:
        result.error("assembly.empty_manifest", "The page manifest is empty",
                     remedy="Run `bookfactory plan <book>`.")
        return result

    for page in book.manifest:
        if not page.approved:
            result.error("assembly.unapproved_page",
                         f"{page.page_id} ({page.title}) is not approved - status {page.status}",
                         page_id=page.page_id,
                         remedy="Approve it, or remove it from the manifest.")
            continue

        path_str = page.approved.path.replace("\\", "/")
        if not path_str.startswith(APPROVED_PREFIXES):
            result.error("assembly.draft_substitution",
                         f"{page.page_id} points at {path_str}, which is not inside "
                         "pages/approved/",
                         page_id=page.page_id,
                         remedy="Assembly reads approved artefacts only. Re-approve the page.")
            continue

        path = book.paths.resolve(page.approved.path)
        if not path.exists():
            result.error("assembly.missing_file",
                         f"{page.page_id}: approved file missing ({page.approved.path})",
                         page_id=page.page_id)
            continue
        if not checksums.matches(path, page.approved.sha256):
            result.error("assembly.checksum_mismatch",
                         f"{page.page_id}: approved file does not match its recorded checksum",
                         page_id=page.page_id,
                         remedy="Assembly will not use a file it cannot verify.")

        if page.revision_open:
            result.warn("assembly.open_revision",
                        f"{page.page_id} has an open revision; assembly will use the currently "
                        f"approved version ({page.approved.revision})",
                        page_id=page.page_id,
                        remedy="Finish the revision, or close it, before producing final files.")

    for problem in book.manifest.problems():
        result.error("assembly.manifest", f"Page manifest: {problem}")

    return result
