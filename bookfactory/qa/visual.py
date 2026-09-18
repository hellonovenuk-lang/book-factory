"""Visual QA - the pictures.

Machine-checkable: the artwork exists, is approved, is intact, and is big
enough to print. Everything else - drift, composition, repetition - is a human
judgement and is reported as such.
"""

from __future__ import annotations

from bookfactory.core import checksums
from bookfactory.qa.findings import Finding, INFO, LayerResult

#: Placement to the fraction of the page width the artwork will occupy. Shared
#: with the submit-time constraint check, so a draft cannot clear one and fail
#: the other.
from bookfactory.core.constraints import PLACEMENT_COVERAGE  # noqa: E402  (re-export)


def check(book) -> LayerResult:
    result = LayerResult("visual")
    from bookfactory.kdp import profiles

    profile = profiles.load_profile(book.state.format.kdp_profile)
    min_dpi = int(profile["images"]["min_dpi"])
    trim_w, _trim_h = profiles.trim_inches(book.state.format.trim,
                                           book.state.format.kdp_profile)

    seen_artwork: dict[str, str] = {}

    for asset in book.registry:
        if not asset.is_approved:
            if asset.status != "planned":
                result.warn("visual.unapproved_asset",
                            f"Asset '{asset.asset_id}' is {asset.status}, not approved",
                            asset_id=asset.asset_id)
            continue
        approved = asset.approved
        path = book.paths.resolve(approved.path)
        if not path.exists():
            result.error("visual.missing_file",
                         f"Approved artwork for '{asset.asset_id}' is missing: {approved.path}",
                         asset_id=asset.asset_id,
                         remedy="Restore it from git history. Never re-generate an approved asset.")
            continue
        if not checksums.matches(path, approved.sha256):
            result.error("visual.checksum_mismatch",
                         f"Approved artwork for '{asset.asset_id}' no longer matches its checksum",
                         asset_id=asset.asset_id,
                         remedy="The file was modified outside Book Factory. Restore it, or open a revision.")
            continue
        if approved.sha256 in seen_artwork and seen_artwork[approved.sha256] != asset.asset_id:
            result.warn("visual.duplicate_artwork",
                        f"'{asset.asset_id}' is byte-identical to '{seen_artwork[approved.sha256]}'",
                        asset_id=asset.asset_id,
                        remedy="The same picture used twice is usually an accident.")
        seen_artwork.setdefault(approved.sha256, asset.asset_id)

        if approved.width and approved.height:
            if approved.width < 64 or approved.height < 64:
                result.error("visual.tiny_image",
                             f"'{asset.asset_id}' is {approved.width}x{approved.height}px",
                             asset_id=asset.asset_id)
        elif path.suffix.lower() in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
            result.warn("visual.unknown_dimensions",
                        f"Could not read dimensions of '{asset.asset_id}'",
                        asset_id=asset.asset_id)

    for page in book.manifest:
        if not page.spec:
            continue
        try:
            spec = book.read_page_spec(page.page_id)
        except Exception:  # noqa: BLE001 - content QA reports unreadable specs
            continue
        illustration = spec.get("illustration") or {}
        asset_id = illustration.get("asset_id")
        if not asset_id:
            continue

        if asset_id not in page.required_assets:
            result.warn("visual.spec_manifest_mismatch",
                        f"{page.page_id} specifies artwork '{asset_id}' but the manifest does not "
                        "list it in required_assets",
                        page_id=page.page_id, asset_id=asset_id,
                        remedy="The manifest is what production follows; keep the two in step.")

        asset = book.registry.find(asset_id)
        if asset is None:
            result.error("visual.unregistered_asset",
                         f"{page.page_id} references unregistered asset '{asset_id}'",
                         page_id=page.page_id, asset_id=asset_id)
            continue
        if not asset.is_approved:
            result.error("visual.asset_not_approved",
                         f"{page.page_id} needs '{asset_id}', which is not approved",
                         page_id=page.page_id, asset_id=asset_id)
            continue

        if illustration.get("embedded_text"):
            result.warn("visual.embedded_text",
                        f"{page.page_id} allows embedded text in generated artwork",
                        page_id=page.page_id, asset_id=asset_id,
                        remedy="Generated type misspells words. Set the text with the renderer instead.")

        width = asset.approved.width
        if width:
            coverage = PLACEMENT_COVERAGE.get(illustration.get("placement", "full_page"), 0.85)
            printed_in = trim_w * coverage
            effective_dpi = width / printed_in if printed_in else 0
            if effective_dpi < min_dpi:
                result.error("visual.low_resolution",
                             f"{page.page_id}: '{asset_id}' is {width}px wide, about "
                             f"{effective_dpi:.0f} DPI at its printed size "
                             f"({printed_in:.2f} in). Minimum is {min_dpi} DPI.",
                             page_id=page.page_id, asset_id=asset_id,
                             remedy=f"Re-generate at least {int(printed_in * min_dpi)}px wide and "
                                    "submit as a new draft.")

    if len(book.registry):
        result.findings.append(Finding(
            INFO, "visual.human_review",
            "Character drift, style drift, composition and visual repetition cannot be "
            "machine-checked. Compare the contact sheet against the locked references.",
            needs_human=True,
            remedy="Run `bookfactory review <book>` and compare with style/references/."))
    return result
