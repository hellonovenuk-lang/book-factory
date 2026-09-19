"""Production stages and the gates between them.

A book always has exactly one current stage. Stages are ordered. Moving
forward past a gate requires the gate's conditions to be satisfied; the system
reports precisely which condition failed rather than refusing vaguely.

Stages are deliberately named after what a human is *doing*, not after
internal state.
"""

from __future__ import annotations

from dataclasses import dataclass

IDEA = "idea"
BOOK_BRIEF = "book_brief"
CONCEPT_LOCK = "concept_lock"
OUTLINE = "outline"
WRITING_SAMPLE = "writing_sample"
VOICE_LOCK = "voice_lock"
MANUSCRIPT = "manuscript"
MANUSCRIPT_LOCK = "manuscript_lock"
VISUAL_DEVELOPMENT = "visual_development"
VISUAL_LOCK = "visual_lock"
PAGE_PLANNING = "page_planning"
PAGE_PRODUCTION = "page_production"
PAGE_APPROVAL = "page_approval"
CONTENT_QA = "content_qa"
VISUAL_QA = "visual_qa"
TECHNICAL_QA = "technical_qa"
ASSEMBLY = "assembly"
KDP_PREFLIGHT = "kdp_preflight"
COVER_PRODUCTION = "cover_production"
COVER_PREFLIGHT = "cover_preflight"
RELEASE_READY = "release_ready"


@dataclass(frozen=True)
class Stage:
    key: str
    number: int
    label: str
    summary: str
    #: True when leaving this stage needs an explicit human approval operation.
    approval_gate: bool = False


STAGES: tuple[Stage, ...] = (
    Stage(IDEA, 1, "Idea", "A one-line book idea exists and nothing else."),
    Stage(BOOK_BRIEF, 2, "Book Brief",
          "Buyer, recipient, recognition trigger, humour angle and commercial rationale are written down."),
    Stage(CONCEPT_LOCK, 3, "Concept Lock",
          "The operator has approved the concept. Later stages may not renegotiate it.", True),
    Stage(OUTLINE, 4, "Outline", "Chapters and their jobs are listed."),
    Stage(WRITING_SAMPLE, 5, "Writing Sample",
          "A representative sample exists so voice can be judged before the whole manuscript is written."),
    Stage(VOICE_LOCK, 6, "Humour / Voice Lock",
          "The operator has approved the voice bible. All later writing references it.", True),
    Stage(MANUSCRIPT, 7, "Manuscript", "Full manuscript drafted against the locked voice."),
    Stage(MANUSCRIPT_LOCK, 8, "Manuscript Lock",
          "Manuscript version frozen and checksummed. Page copy comes from here.", True),
    Stage(VISUAL_DEVELOPMENT, 9, "Visual Development",
          "The required reference set is being generated and reviewed."),
    Stage(VISUAL_LOCK, 10, "Visual Lock",
          "Reference set approved and checksummed. Mass page production may now begin.", True),
    Stage(PAGE_PLANNING, 11, "Page Planning",
          "Every planned page exists in the page manifest with a spec."),
    Stage(PAGE_PRODUCTION, 12, "Page Production",
          "Illustrations generated and pages rendered deterministically."),
    Stage(PAGE_APPROVAL, 13, "Page Approval",
          "Every page has been explicitly approved by the operator.", True),
    Stage(CONTENT_QA, 14, "Content QA", "Copy checks."),
    Stage(VISUAL_QA, 15, "Visual QA", "Artwork checks."),
    Stage(TECHNICAL_QA, 16, "Technical QA", "Dimensions, sequence, checksums, resolution."),
    Stage(ASSEMBLY, 17, "Assembly", "Deterministic, non-creative PDF assembly."),
    Stage(KDP_PREFLIGHT, 18, "KDP Preflight", "Checked against the configured KDP profile."),
    Stage(COVER_PRODUCTION, 19, "Cover Production", "Cover artwork and typeset full wrap under review."),
    Stage(COVER_PREFLIGHT, 20, "Cover Preflight", "Approved cover checked for KDP upload."),
    Stage(RELEASE_READY, 21, "Release Ready", "Interior and required cover are complete and valid."),
)

BY_KEY = {stage.key: stage for stage in STAGES}
ORDER = [stage.key for stage in STAGES]


def get(key: str) -> Stage:
    from bookfactory.core.errors import ValidationError

    if key not in BY_KEY:
        raise ValidationError(
            f"Unknown stage {key!r}",
            remedy="Valid stages: " + ", ".join(ORDER),
        )
    return BY_KEY[key]


def index(key: str) -> int:
    return ORDER.index(get(key).key)


def is_at_least(current: str, target: str) -> bool:
    return index(current) >= index(target)


def next_stage(key: str) -> str | None:
    i = index(key)
    return ORDER[i + 1] if i + 1 < len(ORDER) else None


def label(key: str) -> str:
    return get(key).label
