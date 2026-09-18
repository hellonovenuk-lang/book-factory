"""Production gates.

Every gate answers one question: *may this book move on?* A blocked gate always
returns the exact list of unmet conditions, because "no" without a reason is
what made the old workflow miserable.

Gates never mutate anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from bookfactory.core import stages


@dataclass
class GateResult:
    gate: str
    ok: bool
    reasons: list[str]

    def to_dict(self) -> dict:
        return {"gate": self.gate, "ok": self.ok, "reasons": self.reasons}


def _placeholder_free(text: str) -> bool:
    lowered = text.lower()
    markers = ("todo", "tbd", "<fill in>", "lorem ipsum", "xxx")
    return not any(marker in lowered for marker in markers)


def concept_lock(book) -> GateResult:
    reasons = []
    if not book.paths.brief_file.is_file():
        reasons.append("brief/brief.md is missing")
    else:
        text = book.paths.brief_file.read_text(encoding="utf-8")
        if len(text.strip()) < 200:
            reasons.append("brief/brief.md is still essentially empty")
        elif not _placeholder_free(text):
            reasons.append("brief/brief.md still contains TODO/TBD placeholders")
    return GateResult("concept_lock", not reasons, reasons)


def voice_lock(book) -> GateResult:
    reasons = []
    if not book.state.concept.locked:
        reasons.append("concept is not locked (run `bookfactory lock concept`)")
    if not book.paths.voice_bible.is_file():
        reasons.append("style/voice-bible.md is missing")
    elif not _placeholder_free(book.paths.voice_bible.read_text(encoding="utf-8")):
        reasons.append("style/voice-bible.md still contains TODO/TBD placeholders")
    if not book.paths.writing_sample_file.is_file():
        reasons.append("manuscript/writing-sample.md is missing - voice must be judged on real prose")
    elif not _placeholder_free(book.paths.writing_sample_file.read_text(encoding="utf-8")):
        reasons.append("manuscript/writing-sample.md is still the scaffolded template - "
                       "voice must be judged on real prose")
    return GateResult("voice_lock", not reasons, reasons)


def manuscript_lock(book) -> GateResult:
    reasons = []
    if not book.state.style.voice_locked:
        reasons.append("voice is not locked (run `bookfactory lock voice`)")
    if not book.paths.manuscript_file.is_file():
        reasons.append("manuscript/manuscript.md is missing")
    else:
        text = book.paths.manuscript_file.read_text(encoding="utf-8")
        if len(text.strip()) < 500:
            reasons.append("manuscript/manuscript.md is too short to be a manuscript")
        elif not _placeholder_free(text):
            reasons.append("manuscript/manuscript.md still contains TODO/TBD placeholders")
    return GateResult("manuscript_lock", not reasons, reasons)


def visual_lock(book) -> GateResult:
    """The gate that the golf project most needed.

    Mass page production may not begin until the reference set is approved and
    checksummed, because every later illustration is generated against it.
    """
    reasons = []
    if not book.paths.visual_bible.is_file():
        reasons.append("style/visual-bible.md is missing")
    required = book.required_reference_ids()
    if not required:
        reasons.append("style/reference-set.json lists no required references")
    for asset_id in required:
        asset = book.registry.find(asset_id)
        if asset is None:
            reasons.append(f"required visual reference '{asset_id}' has not been registered")
        elif not asset.is_approved:
            reasons.append(
                f"required visual reference '{asset_id}' is not approved (status: {asset.status})"
            )
    return GateResult("visual_lock", not reasons, reasons)


def page_production(book) -> GateResult:
    reasons = []
    if not book.state.manuscript.locked:
        reasons.append("manuscript is not locked - page copy would drift")
    if not book.state.style.visual_locked:
        reasons.append("visual style is not locked - illustrations would drift")
    if len(book.manifest) == 0:
        reasons.append("page manifest is empty - run `bookfactory plan` first")
    problems = book.manifest.problems()
    reasons.extend(f"page manifest: {p}" for p in problems)
    return GateResult("page_production", not reasons, reasons)


def page_approval_complete(book) -> GateResult:
    reasons = []
    unapproved = [p.page_id for p in book.manifest if not p.is_approved]
    if unapproved:
        shown = ", ".join(unapproved[:12])
        more = f" (+{len(unapproved) - 12} more)" if len(unapproved) > 12 else ""
        reasons.append(f"{len(unapproved)} page(s) not approved: {shown}{more}")
    return GateResult("page_approval_complete", not reasons, reasons)


def assembly(book) -> GateResult:
    """Fail closed. Assembly never substitutes the closest available file."""
    reasons = []
    if len(book.manifest) == 0:
        reasons.append("page manifest is empty")
    reasons.extend(f"page manifest: {p}" for p in book.manifest.problems())
    reasons.extend(page_approval_complete(book).reasons)
    for finding in book.verify_approved():
        reasons.append(finding)
    return GateResult("assembly", not reasons, reasons)


def release_ready(book) -> GateResult:
    reasons = []
    if not book.paths.interior_pdf.is_file():
        reasons.append("output/interior.pdf has not been assembled")
    report = book.latest_preflight()
    if report is None:
        reasons.append("KDP preflight has not been run")
    elif report.get("status") == "fail":
        failed = [c["check"] for c in report.get("checks", []) if c.get("status") == "fail"]
        reasons.append("KDP preflight failed: " + ", ".join(failed))
    return GateResult("release_ready", not reasons, reasons)


#: Gates that must pass before the book may *enter* a given stage.
ENTRY_GATES = {
    stages.CONCEPT_LOCK: concept_lock,
    stages.VOICE_LOCK: voice_lock,
    stages.MANUSCRIPT_LOCK: manuscript_lock,
    stages.VISUAL_LOCK: visual_lock,
    stages.PAGE_PRODUCTION: page_production,
    stages.CONTENT_QA: page_approval_complete,
    stages.ASSEMBLY: assembly,
    stages.RELEASE_READY: release_ready,
}


def for_stage(book, stage_key: str) -> GateResult | None:
    check = ENTRY_GATES.get(stage_key)
    return check(book) if check else None
