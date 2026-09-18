"""Typed views over the state files.

These dataclasses are a convenience for Python callers; the JSON on disk is the
real thing. Every model round-trips exactly (`from_dict(x.to_dict()) == x`) so
no information is invented or lost by passing through Python.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from bookfactory import SCHEMA_VERSION
from bookfactory.core import clock, ids, stages
from bookfactory.core.errors import ValidationError

# --------------------------------------------------------------------------
# Book state
# --------------------------------------------------------------------------


@dataclass
class BookFormat:
    trim: str = "6x9"
    colour: bool = True
    bleed: bool = False
    dpi: int = 300
    kdp_profile: str = "kdp-default"
    target_page_count: int | None = None


@dataclass
class LockState:
    """A generic 'this is frozen' marker with a checksum of what was frozen."""

    locked: bool = False
    locked_at: str | None = None
    sha256: str | None = None


@dataclass
class ManuscriptState:
    version: str = "v0"
    locked: bool = False
    locked_at: str | None = None
    sha256: str | None = None
    path: str | None = None


@dataclass
class StyleState:
    visual_version: str = "v0"
    visual_locked: bool = False
    visual_locked_at: str | None = None
    visual_sha256: str | None = None
    voice_version: str = "v0"
    voice_locked: bool = False
    voice_locked_at: str | None = None
    voice_sha256: str | None = None


@dataclass
class PagePlanState:
    planned: bool = False
    page_count: int = 0
    planned_at: str | None = None


@dataclass
class BookState:
    book_id: str
    title: str
    stage: str = stages.IDEA
    subtitle: str | None = None
    series: str | None = None
    format: BookFormat = field(default_factory=BookFormat)
    concept: LockState = field(default_factory=LockState)
    manuscript: ManuscriptState = field(default_factory=ManuscriptState)
    style: StyleState = field(default_factory=StyleState)
    page_plan: PagePlanState = field(default_factory=PagePlanState)
    blocked: dict | None = None
    next_action: dict | None = None
    last_transition: dict | None = None
    created_at: str = field(default_factory=clock.timestamp)
    updated_at: str = field(default_factory=clock.timestamp)
    schema_version: str = SCHEMA_VERSION

    # -- serialisation ----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "book_id": self.book_id,
            "title": self.title,
            "subtitle": self.subtitle,
            "series": self.series,
            "stage": self.stage,
            "format": asdict(self.format),
            "concept": asdict(self.concept),
            "manuscript": asdict(self.manuscript),
            "style": asdict(self.style),
            "page_plan": asdict(self.page_plan),
            "blocked": self.blocked,
            "next_action": self.next_action,
            "last_transition": self.last_transition,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BookState":
        try:
            return cls(
                schema_version=data.get("schema_version", SCHEMA_VERSION),
                book_id=ids.validate_book_id(data["book_id"]),
                title=data["title"],
                subtitle=data.get("subtitle"),
                series=data.get("series"),
                stage=stages.get(data.get("stage", stages.IDEA)).key,
                format=BookFormat(**data.get("format", {})),
                concept=LockState(**data.get("concept", {})),
                manuscript=ManuscriptState(**data.get("manuscript", {})),
                style=StyleState(**data.get("style", {})),
                page_plan=PagePlanState(**data.get("page_plan", {})),
                blocked=data.get("blocked"),
                next_action=data.get("next_action"),
                last_transition=data.get("last_transition"),
                created_at=data.get("created_at", clock.timestamp()),
                updated_at=data.get("updated_at", clock.timestamp()),
            )
        except KeyError as exc:
            raise ValidationError(f"book.json is missing required field {exc}") from exc
        except TypeError as exc:
            raise ValidationError(f"book.json has an unexpected field: {exc}") from exc

    # -- convenience ------------------------------------------------------
    @property
    def stage_number(self) -> int:
        return stages.get(self.stage).number

    @property
    def stage_label(self) -> str:
        return stages.label(self.stage)

    def at_least(self, target: str) -> bool:
        return stages.is_at_least(self.stage, target)

    def touch(self) -> None:
        self.updated_at = clock.timestamp()


# --------------------------------------------------------------------------
# Draft / approval records - shared by pages and assets
# --------------------------------------------------------------------------


@dataclass
class DraftRecord:
    revision: str
    path: str
    sha256: str
    submitted_at: str
    source: str | None = None
    status: str = "draft"
    note: str | None = None
    width: int | None = None
    height: int | None = None

    def to_dict(self, *, with_dimensions: bool = False) -> dict:
        data = {
            "revision": self.revision,
            "path": self.path,
            "sha256": self.sha256,
            "submitted_at": self.submitted_at,
            "source": self.source,
            "status": self.status,
            "note": self.note,
        }
        if with_dimensions:
            data["width"] = self.width
            data["height"] = self.height
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "DraftRecord":
        return cls(**data)


@dataclass
class ApprovalRecord:
    revision: str
    path: str
    sha256: str
    approved_at: str
    approved_by: str | None = None
    source_draft: str | None = None
    note: str | None = None
    width: int | None = None
    height: int | None = None
    superseded_at: str | None = None
    superseded_reason: str | None = None

    def to_dict(self, *, with_dimensions: bool = False) -> dict:
        data = {
            "revision": self.revision,
            "path": self.path,
            "sha256": self.sha256,
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "source_draft": self.source_draft,
            "note": self.note,
            "superseded_at": self.superseded_at,
            "superseded_reason": self.superseded_reason,
        }
        if with_dimensions:
            data["width"] = self.width
            data["height"] = self.height
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalRecord":
        return cls(**data)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

PAGE_STATUS = ("planned", "spec_ready", "in_production", "draft_submitted", "approved", "rejected")


@dataclass
class PageRecord:
    page_id: str
    sequence: int
    title: str
    type: str
    chapter: int | None = None
    printed_number: int | None = None
    spec: str | None = None
    required_assets: list[str] = field(default_factory=list)
    status: str = "planned"
    revision_open: bool = False
    drafts: list[DraftRecord] = field(default_factory=list)
    approved: ApprovalRecord | None = None
    approval_history: list[ApprovalRecord] = field(default_factory=list)
    qa: dict = field(default_factory=lambda: {"content": "pending", "visual": "pending",
                                              "technical": "pending"})
    depends_on: list[str] = field(default_factory=list)
    notes: str | None = None

    def to_dict(self) -> dict:
        return {
            "page_id": self.page_id,
            "sequence": self.sequence,
            "printed_number": self.printed_number,
            "chapter": self.chapter,
            "title": self.title,
            "type": self.type,
            "spec": self.spec,
            "required_assets": list(self.required_assets),
            "status": self.status,
            "revision_open": self.revision_open,
            "drafts": [d.to_dict() for d in self.drafts],
            "approved": self.approved.to_dict() if self.approved else None,
            "approval_history": [a.to_dict() for a in self.approval_history],
            "qa": dict(self.qa),
            "depends_on": list(self.depends_on),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PageRecord":
        approved = data.get("approved")
        return cls(
            page_id=ids.validate_page_id(data["page_id"]),
            sequence=int(data["sequence"]),
            title=data.get("title", ""),
            type=data["type"],
            chapter=data.get("chapter"),
            printed_number=data.get("printed_number"),
            spec=data.get("spec"),
            required_assets=list(data.get("required_assets", [])),
            status=data.get("status", "planned"),
            revision_open=bool(data.get("revision_open", False)),
            drafts=[DraftRecord.from_dict(d) for d in data.get("drafts", [])],
            approved=ApprovalRecord.from_dict(approved) if approved else None,
            approval_history=[ApprovalRecord.from_dict(a) for a in data.get("approval_history", [])],
            qa=dict(data.get("qa") or {"content": "pending", "visual": "pending",
                                       "technical": "pending"}),
            depends_on=list(data.get("depends_on", [])),
            notes=data.get("notes"),
        )

    def draft(self, revision: str) -> DraftRecord | None:
        for draft in self.drafts:
            if draft.revision == revision:
                return draft
        return None

    def latest_draft(self) -> DraftRecord | None:
        candidates = [d for d in self.drafts if d.status in ("draft", "approved")]
        if not candidates:
            return None
        return max(candidates, key=lambda d: ids.revision_number(d.revision))

    @property
    def is_approved(self) -> bool:
        return self.approved is not None


# --------------------------------------------------------------------------
# Assets
# --------------------------------------------------------------------------

ASSET_KINDS = ("illustration", "character_reference", "layout_reference", "page_reference",
               "palette_reference", "decoration")
REFERENCE_KINDS = ("character_reference", "layout_reference", "page_reference", "palette_reference")


@dataclass
class AssetRecord:
    asset_id: str
    kind: str
    title: str | None = None
    description: str | None = None
    page_id: str | None = None
    characters: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    status: str = "planned"
    revision_open: bool = False
    locked: bool = False
    drafts: list[DraftRecord] = field(default_factory=list)
    approved: ApprovalRecord | None = None
    approval_history: list[ApprovalRecord] = field(default_factory=list)
    notes: str | None = None

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "kind": self.kind,
            "title": self.title,
            "description": self.description,
            "page_id": self.page_id,
            "characters": list(self.characters),
            "references": list(self.references),
            "status": self.status,
            "revision_open": self.revision_open,
            "locked": self.locked,
            "drafts": [d.to_dict(with_dimensions=True) for d in self.drafts],
            "approved": self.approved.to_dict(with_dimensions=True) if self.approved else None,
            "approval_history": [a.to_dict(with_dimensions=True) for a in self.approval_history],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AssetRecord":
        approved = data.get("approved")
        kind = data.get("kind", "illustration")
        if kind not in ASSET_KINDS:
            raise ValidationError(
                f"Unknown asset kind {kind!r} for {data.get('asset_id')}",
                remedy="Valid kinds: " + ", ".join(ASSET_KINDS),
            )
        return cls(
            asset_id=ids.validate_asset_id(data["asset_id"]),
            kind=kind,
            title=data.get("title"),
            description=data.get("description"),
            page_id=data.get("page_id"),
            characters=list(data.get("characters", [])),
            references=list(data.get("references", [])),
            status=data.get("status", "planned"),
            revision_open=bool(data.get("revision_open", False)),
            locked=bool(data.get("locked", False)),
            drafts=[DraftRecord.from_dict(d) for d in data.get("drafts", [])],
            approved=ApprovalRecord.from_dict(approved) if approved else None,
            approval_history=[ApprovalRecord.from_dict(a) for a in data.get("approval_history", [])],
            notes=data.get("notes"),
        )

    def draft(self, revision: str) -> DraftRecord | None:
        for draft in self.drafts:
            if draft.revision == revision:
                return draft
        return None

    def latest_draft(self) -> DraftRecord | None:
        candidates = [d for d in self.drafts if d.status in ("draft", "approved")]
        if not candidates:
            return None
        return max(candidates, key=lambda d: ids.revision_number(d.revision))

    @property
    def is_reference(self) -> bool:
        return self.kind in REFERENCE_KINDS

    @property
    def is_approved(self) -> bool:
        return self.approved is not None


# --------------------------------------------------------------------------
# Tasks
# --------------------------------------------------------------------------


@dataclass
class Task:
    task_id: str
    book_id: str
    type: str
    summary: str
    stage: str = ""
    instructions: str | None = None
    page_id: str | None = None
    asset_id: str | None = None
    scene: str | None = None
    characters: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    output: dict = field(default_factory=dict)
    approval_required: bool = False
    status: str = "open"
    created_at: str = field(default_factory=clock.timestamp)
    closed_at: str | None = None
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "book_id": self.book_id,
            "type": self.type,
            "stage": self.stage,
            "summary": self.summary,
            "instructions": self.instructions,
            "page_id": self.page_id,
            "asset_id": self.asset_id,
            "scene": self.scene,
            "characters": list(self.characters),
            "references": list(self.references),
            "required_inputs": list(self.required_inputs),
            "constraints": dict(self.constraints),
            "output": dict(self.output),
            "approval_required": self.approval_required,
            "status": self.status,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        payload = dict(data)
        payload.pop("schema_version", None)
        return cls(schema_version=data.get("schema_version", SCHEMA_VERSION), **payload)

    def summary_dict(self) -> dict:
        """The compact form cached in book.json's next_action."""
        return {
            "task_id": self.task_id,
            "type": self.type,
            "summary": self.summary,
            "page_id": self.page_id,
            "asset_id": self.asset_id,
            "approval_required": self.approval_required,
        }


__all__ = [
    "BookFormat", "LockState", "ManuscriptState", "StyleState", "PagePlanState", "BookState",
    "DraftRecord", "ApprovalRecord", "PageRecord", "AssetRecord", "Task",
    "PAGE_STATUS", "ASSET_KINDS", "REFERENCE_KINDS",
]
