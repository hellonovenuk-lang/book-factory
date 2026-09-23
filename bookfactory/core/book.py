"""The Book aggregate - the only object that writes to a book project.

Everything the CLI, QA, assembly and any future MCP server does goes through
here, so the rules about immutability, locks and gates are enforced in exactly
one place.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from bookfactory import SCHEMA_VERSION
from bookfactory.core import audit, checksums, clock, gates, ids, production, schema, stages
from bookfactory.core.errors import (
    BookAlreadyExists,
    BookNotFound,
    GateBlocked,
    HardConstraintViolation,
    ImmutableAssetError,
    ValidationError,
)
from bookfactory.core.jsonio import read_json, write_json
from bookfactory.core.manifest import PageManifest
from bookfactory.core.models import (
    ApprovalRecord,
    AssetRecord,
    BookFormat,
    BookState,
    DraftRecord,
    PageRecord,
    effective_reference_role,
)
from bookfactory.core.paths import BookPaths, books_dir
from bookfactory.core.registry import AssetRegistry

PAGE = "page"
ASSET = "asset"
KINDS = (PAGE, ASSET)


class Book:
    """One book project on disk."""

    def __init__(self, paths: BookPaths, state: BookState, manifest: PageManifest,
                 registry: AssetRegistry) -> None:
        self.paths = paths
        self.state = state
        self.manifest = manifest
        self.registry = registry

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, book_id: str, root: str | Path | None = None) -> "Book":
        paths = BookPaths.for_book(book_id, root)
        if not paths.exists():
            available = sorted(p.name for p in books_dir(root).glob("*") if (p / "book.json").is_file())
            raise BookNotFound(
                f"No book '{book_id}' in {books_dir(root)}",
                remedy=("Available books: " + ", ".join(available)) if available
                else "Create one with `bookfactory create \"<Title>\" --policy <choice>`.",
            )
        data = read_json(paths.state_file)
        schema.validate("book", data, context=str(paths.state_file))
        state = BookState.from_dict(data)
        manifest = (PageManifest.load(paths.manifest_file)
                    if paths.manifest_file.is_file() else PageManifest.empty(book_id))
        registry = (AssetRegistry.load(paths.asset_registry)
                    if paths.asset_registry.is_file() else AssetRegistry.empty(book_id))
        book = cls(paths, state, manifest, registry)
        #: Per-page QA verdicts mirror qa/latest.json. `bookfactory qa` writes
        #: only its report, so they are applied here and persisted by the next
        #: command that saves the book.
        from bookfactory.qa.runner import apply_latest_verdicts
        apply_latest_verdicts(book)
        return book

    @classmethod
    def exists(cls, book_id: str, root: str | Path | None = None) -> bool:
        return BookPaths.for_book(book_id, root).exists()

    @classmethod
    def create(cls, title: str, *, book_id: str | None = None,
               root: str | Path | None = None, trim: str = "6x9", colour: bool = True,
               bleed: bool = False, dpi: int = 300, kdp_profile: str = "kdp-default",
               target_page_count: int | None = None, subtitle: str | None = None,
               series: str | None = None, idea: str | None = None) -> "Book":
        book_id = ids.validate_book_id(book_id or ids.make_book_id(title))
        paths = BookPaths.for_book(book_id, root)
        if paths.exists():
            raise BookAlreadyExists(
                f"Book '{book_id}' already exists at {paths.root}",
                remedy="Pick a different id with --id, or continue the existing book.",
            )
        paths.create_skeleton()

        state = BookState(
            book_id=book_id,
            title=title,
            subtitle=subtitle,
            series=series,
            stage=stages.IDEA,
            format=BookFormat(trim=trim, colour=colour, bleed=bleed, dpi=dpi,
                              kdp_profile=kdp_profile, target_page_count=target_page_count),
        )
        book = cls(paths, state, PageManifest.empty(book_id), AssetRegistry.empty(book_id))
        book._scaffold_documents(idea=idea)
        from bookfactory.core import cover
        cover.initialize(book)
        book.save()
        audit.record(paths.audit_log, "book_created", book_id=book_id, title=title,
                     trim=trim, colour=colour)
        return book

    def _scaffold_documents(self, *, idea: str | None) -> None:
        """Copy the project templates in, rendered with this book's details."""
        from bookfactory.render.templates import render_project_template, project_template_names

        context = {
            "book_id": self.state.book_id,
            "title": self.state.title,
            "subtitle": self.state.subtitle or "",
            "idea": idea or "TODO: one sentence describing the book.",
            "trim": self.state.format.trim,
            "colour": self.state.format.colour,
            "target_page_count": self.state.format.target_page_count or "TODO",
            "created_at": self.state.created_at,
        }
        targets = {
            "brief.md": self.paths.brief_file,
            "concept.md": self.paths.concept_file,
            "audience.md": self.paths.audience_file,
            "outline.md": self.paths.outline_file,
            "voice-bible.md": self.paths.voice_bible,
            "visual-bible.md": self.paths.visual_bible,
            "writing-sample.md": self.paths.writing_sample_file,
            "manuscript.md": self.paths.manuscript_file,
            "README.md": self.paths.readme,
        }
        for name, destination in targets.items():
            if name in project_template_names():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(render_project_template(name, context), encoding="utf-8")

        write_json(self.paths.design_tokens, _default_design_tokens(self.state))
        write_json(self.paths.reference_set, _default_reference_set())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, *, recompute_next: bool = True) -> None:
        self.autoadvance()
        if recompute_next:
            try:
                from bookfactory.core.tasks import next_task

                task = next_task(self)
                self.state.next_action = task.summary_dict() if task else None
                self.state.production_mode = task.mode if task else production.COMPLETE
            except Exception:  # noqa: BLE001 - a broken derivation must never block a save
                self.state.next_action = None
                self.state.production_mode = production.COMPLETE
        self.state.touch()
        data = self.state.to_dict()
        schema.validate("book", data, context=str(self.paths.state_file))
        write_json(self.paths.state_file, data)
        self.manifest.save(self.paths.manifest_file)
        self.registry.save(self.paths.asset_registry)

    def log(self, event: str, /, **fields) -> None:
        audit.record(self.paths.audit_log, event, **fields)

    def refresh_view(self) -> None:
        """Bring the in-memory state up to date with the repository, writing nothing.

        Read-only commands (`status`, `next`, `task`) call this instead of
        `save()`: the stage the evidence on disk supports, the next action and
        the production mode are recomputed in memory only. The stage
        transitions themselves are recorded - with their audit entries - by
        the next command that changes the book. Never call `save()` after this
        on the same object; it would skip those audit entries.
        """
        self.state.stage = self.derived_stage()
        from bookfactory.core.tasks import next_task

        task = next_task(self)
        self.state.next_action = task.summary_dict() if task else None
        self.state.production_mode = task.mode if task else production.COMPLETE

    # ------------------------------------------------------------------
    # Reference set / style config
    # ------------------------------------------------------------------
    def reference_set(self) -> dict:
        if not self.paths.reference_set.is_file():
            return _default_reference_set()
        return read_json(self.paths.reference_set)

    def required_reference_ids(self) -> list[str]:
        return [item["asset_id"] for item in self.reference_set().get("required", [])]

    def design_tokens(self) -> dict:
        if not self.paths.design_tokens.is_file():
            return _default_design_tokens(self.state)
        return read_json(self.paths.design_tokens)

    # ------------------------------------------------------------------
    # Locks
    # ------------------------------------------------------------------
    def _require_gate(self, name: str) -> None:
        result = getattr(gates, name)(self)
        if not result.ok:
            raise GateBlocked(result.gate, result.reasons)

    def _lock_authorization(self, what: str, autonomous: bool) -> str | None:
        """The audit marker for a lock, refusing `autonomous` unless it is on record.

        Uses the same marker as an autonomous approval, so the audit log shows
        every lock an agent made under the recorded policy as exactly that -
        never as an ordinary operator lock.
        """
        if not autonomous:
            return None
        result = gates.autonomous_lock_authorized(self, what)
        if not result.ok:
            raise ValidationError(
                f"This book's production_policy does not authorize an autonomous {what} lock",
                problems=result.reasons,
                remedy=("Ask the operator to lock it explicitly (without --autonomous). "
                        "Autonomous locks need FULL AUTONOMOUS or VISUAL CHECKPOINT recorded "
                        "at intake, and never cover a lock the policy keeps as a checkpoint."),
            )
        return f"autonomous_production_policy:{self.state.production_policy.mode}"

    def lock_concept(self, *, by: str | None = None, note: str | None = None,
                     autonomous: bool = False) -> None:
        self._require_gate("concept_lock")
        authorization = self._lock_authorization("concept", autonomous)
        digest = checksums.sha256_file(self.paths.brief_file)
        self.state.concept.locked = True
        self.state.concept.locked_at = clock.timestamp()
        self.state.concept.sha256 = digest
        self._set_stage_at_least(stages.CONCEPT_LOCK, by=by, note=note)
        self.log("concept_locked", sha256=digest, by=by, note=note,
                 authorization=authorization)
        self.save()

    def lock_voice(self, *, version: str | None = None, by: str | None = None,
                   note: str | None = None, autonomous: bool = False) -> None:
        self._require_gate("voice_lock")
        authorization = self._lock_authorization("voice", autonomous)
        digest = checksums.sha256_file(self.paths.voice_bible)
        self.state.style.voice_version = version or _bump(self.state.style.voice_version)
        self.state.style.voice_locked = True
        self.state.style.voice_locked_at = clock.timestamp()
        self.state.style.voice_sha256 = digest
        self._set_stage_at_least(stages.VOICE_LOCK, by=by, note=note)
        self.log("voice_locked", version=self.state.style.voice_version, sha256=digest,
                 by=by, note=note, authorization=authorization)
        self.save()

    def lock_manuscript(self, *, version: str | None = None, by: str | None = None,
                        note: str | None = None, autonomous: bool = False) -> None:
        self._require_gate("manuscript_lock")
        authorization = self._lock_authorization("manuscript", autonomous)
        version = version or _bump(self.state.manuscript.version)
        ids.validate_revision(version)
        snapshot = self.paths.manuscript_version_file(version)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        if snapshot.exists():
            raise ImmutableAssetError(
                f"Manuscript snapshot {snapshot.name} already exists",
                remedy="Locked manuscript versions are immutable. Lock as a new version instead.",
            )
        shutil.copy2(self.paths.manuscript_file, snapshot)
        checksums.make_immutable(snapshot)
        digest = checksums.sha256_file(snapshot)
        self.state.manuscript.version = version
        self.state.manuscript.locked = True
        self.state.manuscript.locked_at = clock.timestamp()
        self.state.manuscript.sha256 = digest
        self.state.manuscript.path = self.paths.relative(snapshot)
        self._set_stage_at_least(stages.MANUSCRIPT_LOCK, by=by, note=note)
        self.log("manuscript_locked", version=version, sha256=digest, by=by, note=note,
                 authorization=authorization)
        self.save()

    def lock_visual(self, *, version: str | None = None, by: str | None = None,
                    note: str | None = None, autonomous: bool = False) -> None:
        self._require_gate("visual_lock")
        authorization = self._lock_authorization("visual", autonomous)
        version = version or _bump(self.state.style.visual_version)
        ids.validate_revision(version)
        digest = checksums.sha256_file(self.paths.visual_bible)
        for asset_id in self.required_reference_ids():
            asset = self.registry.get(asset_id)
            asset.locked = True
        self.state.style.visual_version = version
        self.state.style.visual_locked = True
        self.state.style.visual_locked_at = clock.timestamp()
        self.state.style.visual_sha256 = digest
        self._set_stage_at_least(stages.VISUAL_LOCK, by=by, note=note)
        self.log("visual_locked", version=version, sha256=digest,
                 references=self.required_reference_ids(), by=by, note=note,
                 authorization=authorization)
        self.save()

    # ------------------------------------------------------------------
    # Stage movement
    # ------------------------------------------------------------------
    def _set_stage_at_least(self, target: str, *, by: str | None, note: str | None) -> None:
        if stages.is_at_least(self.state.stage, target):
            return
        self._transition(target, by=by, note=note)

    def _transition(self, target: str, *, by: str | None, note: str | None) -> None:
        previous = self.state.stage
        self.state.stage = stages.get(target).key
        self.state.last_transition = {
            "from": previous, "to": self.state.stage, "at": clock.timestamp(),
            "by": by, "note": note,
        }
        self.log("stage_advanced", **{"from": previous, "to": self.state.stage,
                                      "by": by, "note": note})

    #: Stages entered only by an explicit lock command.
    _LOCK_STAGES = {
        stages.CONCEPT_LOCK: lambda s: s.concept.locked,
        stages.VOICE_LOCK: lambda s: s.style.voice_locked,
        stages.MANUSCRIPT_LOCK: lambda s: s.manuscript.locked,
        stages.VISUAL_LOCK: lambda s: s.style.visual_locked,
    }

    def autoadvance(self) -> str:
        """Move the stage forward to match reality.

        The stage is a description of where the book actually is, not a flag
        somebody has to remember to set. It is derived from evidence on disk.

        Two kinds of stage are never entered this way: the four lock stages,
        which need an explicit `bookfactory lock` command, and release ready,
        which is the operator's call.
        """
        if getattr(self, "_advancing", False):
            return self.state.stage
        self._advancing = True
        try:
            for target in self._derivable_stages():
                self._transition(target, by="system", note="stage derived from repository state")
        finally:
            self._advancing = False
        return self.state.stage

    def derived_stage(self) -> str:
        """The stage the evidence on disk supports. Pure: moves and writes nothing."""
        reachable = self._derivable_stages()
        return reachable[-1] if reachable else self.state.stage

    def _derivable_stages(self) -> list[str]:
        """The stages `autoadvance` would enter from here, in order. Gates and
        stage evidence only read the repository, so this changes nothing."""
        reachable = []
        stage = self.state.stage
        while True:
            target = stages.next_stage(stage)
            if target is None or target == stages.RELEASE_READY:
                break
            lock_check = self._LOCK_STAGES.get(target)
            if lock_check and not lock_check(self.state):
                break
            result = gates.for_stage(self, target)
            if result is not None and not result.ok:
                break
            if not self._stage_evidence(target):
                break
            reachable.append(target)
            stage = target
        return reachable

    def _stage_evidence(self, stage_key: str) -> bool:
        """Is there something on disk showing this stage has actually begun?"""
        from bookfactory.core import cover
        if stage_key in self._LOCK_STAGES:
            return True

        def written(path) -> bool:
            if not path.is_file():
                return False
            text = path.read_text(encoding="utf-8").lower()
            return len(text.strip()) > 120 and not any(
                marker in text for marker in ("todo", "tbd", "<fill in>"))

        checks = {
            stages.BOOK_BRIEF: lambda: self.paths.brief_file.is_file(),
            stages.OUTLINE: lambda: written(self.paths.outline_file),
            stages.WRITING_SAMPLE: lambda: written(self.paths.writing_sample_file),
            stages.MANUSCRIPT: lambda: written(self.paths.manuscript_file),
            stages.VISUAL_DEVELOPMENT: lambda: written(self.paths.visual_bible),
            stages.PAGE_PLANNING: lambda: len(self.manifest) > 0,
            stages.PAGE_PRODUCTION: lambda: any(p.drafts or p.approved for p in self.manifest),
            stages.PAGE_APPROVAL: lambda: len(self.manifest) > 0 and all(
                p.is_approved for p in self.manifest),
            stages.CONTENT_QA: lambda: self.paths.qa_latest.is_file(),
            stages.VISUAL_QA: lambda: self.paths.qa_latest.is_file(),
            stages.TECHNICAL_QA: lambda: self.paths.qa_latest.is_file(),
            stages.ASSEMBLY: lambda: self.paths.interior_pdf.is_file(),
            stages.KDP_PREFLIGHT: lambda: (self.latest_preflight() or {}).get("status") in
                                          ("pass", "warn"),
            stages.COVER_PRODUCTION: lambda: self.paths.interior_pdf.is_file(),
            stages.COVER_PREFLIGHT: lambda: cover.preflight_current(self)
                if cover.required(self) else True,
        }
        check = checks.get(stage_key)
        return check() if check else True

    def advance(self, target: str | None = None, *, by: str | None = None,
                note: str | None = None, force: bool = False) -> str:
        """Move the book forward one stage (or to `target`), honouring gates."""
        target = target or stages.next_stage(self.state.stage)
        if target is None:
            return self.state.stage
        target = stages.get(target).key
        if stages.index(target) <= stages.index(self.state.stage):
            raise ValidationError(
                f"Book is already at stage '{self.state.stage}'; cannot move back to '{target}'",
                remedy="Stages only move forward. Open a revision instead of rewinding.",
            )
        if not force:
            for step in stages.ORDER[stages.index(self.state.stage) + 1: stages.index(target) + 1]:
                result = gates.for_stage(self, step)
                if result and not result.ok:
                    raise GateBlocked(
                        result.gate, result.reasons,
                        remedy="Resolve the above, then re-run. "
                               "Use `--force` only with a very good reason.",
                    )
        self._transition(target, by=by, note=note)
        self.save()
        return self.state.stage

    def block(self, reason: str, *, needs: str | None = None) -> None:
        self.state.blocked = {"reason": reason, "since": clock.timestamp(), "needs": needs}
        self.log("blocked", reason=reason, needs=needs)
        self.save()

    def unblock(self) -> None:
        if self.state.blocked:
            self.log("unblocked", was=self.state.blocked.get("reason"))
        self.state.blocked = None
        self.save()

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------
    def add_page(self, *, title: str, type: str, chapter: int | None = None,
                 sequence: int | None = None, page_id: str | None = None,
                 required_assets: list[str] | None = None,
                 notes: str | None = None) -> PageRecord:
        sequence = sequence or self.manifest.next_sequence()
        page_id = page_id or ids.page_id(sequence)
        record = PageRecord(
            page_id=ids.validate_page_id(page_id),
            sequence=sequence,
            title=title,
            type=type,
            chapter=chapter,
            required_assets=list(required_assets or []),
            notes=notes,
        )
        self.manifest.add(record)
        self.state.page_plan.planned = True
        self.state.page_plan.page_count = len(self.manifest)
        self.state.page_plan.planned_at = clock.timestamp()
        return record

    def write_page_spec(self, page_id: str, spec: dict) -> Path:
        page = self.manifest.get(page_id)
        spec = self.prepare_page_spec(page_id, spec)
        path = self.paths.spec_file(page_id)
        write_json(path, spec)
        page.spec = self.paths.relative(path)
        if page.status == "planned":
            page.status = "spec_ready"
        self.register_spec_artwork(page_id, spec)
        return path

    def prepare_page_spec(self, page_id: str, spec: dict) -> dict:
        """The spec as it will be written, with defaults filled in. Writes nothing.

        Raises ValidationError if it does not match the page-spec schema, so a
        caller writing many specs can check them all before writing any.
        """
        page = self.manifest.get(page_id)
        spec = dict(spec)
        spec.setdefault("schema_version", SCHEMA_VERSION)
        spec.setdefault("book_id", self.state.book_id)
        spec["page_id"] = page_id
        spec.setdefault("type", page.type)
        spec.setdefault("title", page.title)
        spec.setdefault("chapter", page.chapter)
        spec.setdefault("source", {
            "manuscript_version": self.state.manuscript.version,
            "visual_style_version": self.state.style.visual_version,
        })
        schema.validate("page-spec", spec, context=f"page spec {page_id}")
        return spec

    def register_spec_artwork(self, page_id: str, spec: dict) -> str | None:
        """Make the artwork a spec names part of its page.

        The asset is added to the page's required assets and, if it is not in
        the registry yet, registered as an illustration for this page from the
        spec's own description of it - so nobody has to run `asset add` for
        page artwork. An asset that is already registered is left as it is.
        Returns the asset id if it was newly registered.
        """
        illustration = spec.get("illustration") or {}
        asset_id = illustration.get("asset_id")
        if not asset_id:
            return None
        page = self.manifest.get(page_id)
        if asset_id not in page.required_assets:
            page.required_assets.append(asset_id)
        if self.registry.find(asset_id) is not None:
            return None
        self.register_asset(
            asset_id,
            kind="illustration",
            title=page.title,
            description=illustration.get("concept"),
            page_id=page_id,
            characters=illustration.get("characters"),
            references=illustration.get("references"),
        )
        return asset_id

    def read_page_spec(self, page_id: str) -> dict:
        page = self.manifest.get(page_id)
        if not page.spec:
            raise ValidationError(
                f"Page {page_id} has no spec",
                remedy=f"Write one to pages/specs/{page_id}.json before producing the page.",
            )
        data = read_json(self.paths.resolve(page.spec))
        schema.validate("page-spec", data, context=page.spec)
        return data

    def register_asset(self, asset_id: str, *, kind: str = "illustration",
                       title: str | None = None, description: str | None = None,
                       page_id: str | None = None, characters: list[str] | None = None,
                       references: list[str] | None = None,
                       reference_role: str | None = None,
                       notes: str | None = None) -> AssetRecord:
        from bookfactory.core.models import REFERENCE_ROLES

        if reference_role is not None and reference_role not in REFERENCE_ROLES:
            raise ValidationError(
                f"Unknown reference_role {reference_role!r}",
                remedy="Valid roles: " + ", ".join(REFERENCE_ROLES),
            )
        record = AssetRecord(
            asset_id=ids.validate_asset_id(asset_id),
            kind=kind,
            title=title,
            description=description,
            page_id=page_id,
            characters=list(characters or []),
            references=list(references or []),
            reference_role=reference_role,
            notes=notes,
        )
        return self.registry.add(record)

    # ------------------------------------------------------------------
    # Draft / approval engine (shared by pages and assets)
    # ------------------------------------------------------------------
    def asset_placement(self, asset) -> str | None:
        """Where this artwork sits on its page, which decides how big it must be."""
        if not asset.page_id:
            return None
        page = self.manifest.find(asset.page_id)
        if page is None or not page.spec:
            return None
        try:
            spec = self.read_page_spec(asset.page_id)
        except Exception:  # noqa: BLE001 - a bad spec is reported by QA
            return None
        illustration = spec.get("illustration") or {}
        if illustration.get("asset_id") != asset.asset_id:
            return None
        return illustration.get("placement")

    def asset_constraints(self, asset) -> dict:
        """The constraint block published in this asset's task."""
        from bookfactory.core import constraints

        from bookfactory.core import cover
        if asset.asset_id == cover.ART_ID and cover.required(self):
            return cover.artwork_constraints(self)
        return constraints.expected_constraints(
            self, asset, placement=self.asset_placement(asset))

    def check_asset_constraints(self, asset, path: str | Path) -> list[dict]:
        """Measure a file against the hard constraints of the asset's task."""
        from bookfactory.core import constraints

        expected = constraints.hard_constraints(self.asset_constraints(asset))
        failures = constraints.evaluate(
            path, expected, context={"placement": self.asset_placement(asset)})
        from bookfactory.core import cover
        height = (cover.artwork_failures(self, path)
                  if asset.asset_id == cover.ART_ID and cover.required(self) else [])
        return [failure.to_dict() for failure in failures] + height

    def _target(self, kind: str, identifier: str):
        if kind == PAGE:
            return self.manifest.get(identifier)
        if kind == ASSET:
            return self.registry.get(identifier)
        raise ValidationError(f"Unknown artefact kind {kind!r}", remedy="Use 'page' or 'asset'.")

    def _draft_dir(self, kind: str, identifier: str) -> Path:
        base = self.paths.page_drafts_dir if kind == PAGE else self.paths.asset_drafts_dir
        return base / identifier

    def _approved_dir(self, kind: str) -> Path:
        return self.paths.page_approved_dir if kind == PAGE else self.paths.asset_approved_dir

    def _history_dir(self, kind: str) -> Path:
        return self.paths.page_history_dir if kind == PAGE else self.paths.asset_history_dir

    def submit(self, kind: str, identifier: str, source_file: str | Path, *,
               revision: str | None = None, note: str | None = None,
               source: str | None = None) -> DraftRecord:
        """Register a draft. Drafts are cheap, plentiful and never overwritten."""
        source_file = Path(source_file)
        if not source_file.is_file():
            raise ValidationError(
                f"No such file: {source_file}",
                remedy="Point --file at the artwork or rendered page you want to submit.",
            )
        record = self._target(kind, identifier)
        if record.is_approved and not record.revision_open:
            raise ImmutableAssetError(
                f"{kind} {identifier} is already approved",
                remedy=(
                    f"Approved work is immutable. Run `bookfactory revise {self.state.book_id} "
                    f"{identifier}` to open a revision, then submit again."
                ),
            )
        revision = revision or ids.next_revision([d.revision for d in record.drafts])
        ids.validate_revision(revision)
        if record.draft(revision):
            raise ValidationError(
                f"Draft {revision} of {identifier} already exists",
                remedy="Draft revisions are never overwritten. Submit without --revision to get the next one.",
            )
        draft_dir = self._draft_dir(kind, identifier)
        draft_dir.mkdir(parents=True, exist_ok=True)
        destination = draft_dir / f"{identifier}-{revision}{source_file.suffix.lower()}"
        shutil.copy2(source_file, destination)
        digest = checksums.sha256_file(destination)
        width = height = None
        if kind == ASSET:
            width, height = _image_size(destination)

        failures = self.check_asset_constraints(record, destination) if kind == ASSET else []

        draft = DraftRecord(
            revision=revision,
            path=self.paths.relative(destination),
            sha256=digest,
            submitted_at=clock.timestamp(),
            source=source,
            status="draft",
            note=note,
            width=width,
            height=height,
            constraint_failures=failures,
        )
        record.drafts.append(draft)
        record.refresh_status()
        self.log("draft_submitted", kind=kind, id=identifier, revision=revision,
                 path=draft.path, sha256=digest, source=source, note=note)
        if failures:
            #: The draft is kept - it is evidence, and the next attempt is judged
            #: against it - but it will not be offered for approval.
            self.log("constraints_failed", kind=kind, id=identifier, revision=revision,
                     failed=[f["constraint"] for f in failures])
        self.save()
        return draft

    def approve(self, kind: str, identifier: str, *, revision: str | None = None,
                by: str | None = None, note: str | None = None,
                autonomous: bool = False) -> ApprovalRecord:
        """Promote a draft to the approved tree. The only way anything becomes canonical.

        `autonomous=True` records that this approval was granted under the
        book's recorded autonomous-production authorization rather than an
        explicit, in-the-moment operator decision. It only works if the
        operator actually recorded that authorization at intake - it is never
        inferred from silence, and never available in checkpointed mode.
        """
        if autonomous and not gates.autonomous_approval_authorized(self).ok:
            raise ValidationError(
                "This book's production_policy does not authorize autonomous approval",
                remedy=("Answer the intake questionnaire's production policy question with "
                        "FULL AUTONOMOUS or VISUAL CHECKPOINT, or approve explicitly without "
                        "--autonomous."),
            )
        record = self._target(kind, identifier)
        if not record.drafts:
            raise ValidationError(
                f"{kind} {identifier} has no drafts to approve",
                remedy=f"Submit one first: `bookfactory submit {self.state.book_id} {identifier} --file <path>`.",
            )
        if revision is None:
            latest = record.latest_draft()
            if latest is None:
                raise ValidationError(f"{kind} {identifier} has no approvable draft")
            revision = latest.revision
        ids.validate_revision(revision)
        draft = record.draft(revision)
        if draft is None:
            available = ", ".join(d.revision for d in record.drafts)
            raise ValidationError(
                f"{kind} {identifier} has no draft {revision}",
                remedy=f"Available drafts: {available}",
            )
        if draft.status == "rejected":
            raise ValidationError(
                f"Draft {revision} of {identifier} was rejected",
                remedy="Approve a different revision, or submit a new one.",
            )
        draft_path = self.paths.resolve(draft.path)
        checksums.verify(draft_path, draft.sha256)

        failures = self.check_asset_constraints(record, draft_path) if kind == ASSET else []
        if failures or draft.constraint_failures:
            from bookfactory.core import constraints

            #: Prefer what the file says now over what the registry remembers.
            failures = failures or list(draft.constraint_failures)
            draft.constraint_failures = failures
            record.refresh_status()
            self.save()
            raise HardConstraintViolation(
                f"Draft {revision} of {identifier} fails a hard constraint of its task:\n  - "
                + constraints.describe(failures),
                failures,
                remedy=(
                    "This is not a judgement call - the artwork cannot be used as it is. "
                    f"Submit a corrected draft: `bookfactory submit {self.state.book_id} "
                    f"{identifier} --kind {kind} --file <path>`."
                ),
            )

        replacing = record.is_approved
        if replacing and not record.revision_open:
            raise ImmutableAssetError(
                f"{kind} {identifier} is already approved and no revision is open",
                remedy=f"Run `bookfactory revise {self.state.book_id} {identifier}` first.",
            )

        if replacing:
            self._archive_approved(kind, record, reason=f"superseded by {revision}")

        approved_name = ids.canonical_filename(
            identifier, getattr(record, "title", None), draft_path.suffix)
        destination = self._approved_dir(kind) / approved_name
        digest = checksums.copy_into_approved(draft_path, destination, allow_replace=replacing)

        authorization = (f"autonomous_production_policy:{self.state.production_policy.mode}"
                        if autonomous else None)
        approval = ApprovalRecord(
            revision=revision,
            path=self.paths.relative(destination),
            sha256=digest,
            approved_at=clock.timestamp(),
            approved_by=by,
            source_draft=draft.path,
            note=note,
            width=draft.width,
            height=draft.height,
            authorization=authorization,
        )
        record.approved = approval
        record.revision_open = False
        draft.status = "approved"
        record.refresh_status()
        self.log("approved", kind=kind, id=identifier, revision=revision,
                 path=approval.path, sha256=digest, by=by, note=note,
                 authorization=authorization)

        if kind == ASSET and replacing:
            self._reopen_pages_using(identifier, revision)

        self.save()
        return approval

    def _reopen_pages_using(self, asset_id: str, revision: str) -> list[str]:
        """New artwork means the pages that use it are out of date.

        An approved page is a render of particular artwork. Replacing the
        artwork without re-rendering would leave the book showing the old
        picture while the registry claims the new one is canonical, which is
        exactly the kind of quiet drift this system exists to prevent. So the
        affected pages go back into revision and must be re-rendered and
        re-approved.
        """
        reopened = []
        for page in self.manifest:
            if asset_id not in page.required_assets:
                continue
            if not page.is_approved or page.revision_open:
                continue
            page.revision_open = True
            page.refresh_status()
            reopened.append(page.page_id)
            self.log("revision_opened", kind=PAGE, id=page.page_id,
                     reason=f"artwork {asset_id} replaced by {revision}",
                     current_revision=page.approved.revision,
                     next_revision=ids.next_revision([d.revision for d in page.drafts]))
        return reopened

    def _archive_approved(self, kind: str, record, *, reason: str) -> None:
        """Move the currently approved artefact into _history. Never deletes."""
        current = record.approved
        if current is None:
            return
        current_path = self.paths.resolve(current.path)
        history_dir = self._history_dir(kind)
        history_dir.mkdir(parents=True, exist_ok=True)
        identifier = getattr(record, "page_id", None) or record.asset_id
        archived = history_dir / f"{identifier}-{current.revision}{current_path.suffix}"
        counter = 1
        while archived.exists():
            archived = history_dir / f"{identifier}-{current.revision}-{counter}{current_path.suffix}"
            counter += 1
        if current_path.exists():
            checksums.unlock_for_system(current_path)
            shutil.move(str(current_path), str(archived))
            checksums.make_immutable(archived)
        current.path = self.paths.relative(archived)
        current.superseded_at = clock.timestamp()
        current.superseded_reason = reason
        record.approval_history.append(current)
        record.approved = None

    def reject(self, kind: str, identifier: str, *, revision: str | None = None,
               reason: str | None = None, by: str | None = None) -> DraftRecord:
        """Mark a draft rejected. The file stays on disk - rejected work is history,
        not rubbish, and re-generating something we already rejected is a real failure mode."""
        record = self._target(kind, identifier)
        if revision is None:
            latest = record.latest_draft()
            if latest is None:
                raise ValidationError(f"{kind} {identifier} has no draft to reject")
            revision = latest.revision
        draft = record.draft(ids.validate_revision(revision))
        if draft is None:
            raise ValidationError(f"{kind} {identifier} has no draft {revision}")
        if draft.status == "approved":
            raise ImmutableAssetError(
                f"Draft {revision} of {identifier} is the approved artefact",
                remedy=f"Open a revision with `bookfactory revise {self.state.book_id} {identifier}`.",
            )
        draft.status = "rejected"
        draft.note = reason or draft.note
        #: Rejecting the replacement does not un-approve what is already
        #: canonical, and it does not close the revision - another attempt is
        #: still expected. The status has to say so.
        record.refresh_status()
        self.log("rejected", kind=kind, id=identifier, revision=revision, reason=reason, by=by)
        self.save()
        return draft

    def revise(self, kind: str, identifier: str, *, reason: str | None = None,
               by: str | None = None) -> dict:
        """Open a revision on approved work.

        The currently approved artefact stays canonical and untouched until a
        replacement is explicitly approved, so the book never becomes
        un-assemblable just because someone started a fix.
        """
        record = self._target(kind, identifier)
        if not record.is_approved:
            raise ValidationError(
                f"{kind} {identifier} is not approved, so there is nothing to revise",
                remedy="Submit a new draft instead.",
            )
        if record.revision_open:
            return {"already_open": True, "next_revision":
                    ids.next_revision([d.revision for d in record.drafts])}
        record.revision_open = True
        record.refresh_status()
        next_rev = ids.next_revision([d.revision for d in record.drafts])
        self.log("revision_opened", kind=kind, id=identifier, reason=reason,
                 current_revision=record.approved.revision, next_revision=next_rev, by=by)
        self.save()
        return {"already_open": False, "next_revision": next_rev,
                "current_revision": record.approved.revision}

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------
    def approved_artefacts(self) -> list[tuple[str, str, ApprovalRecord]]:
        items: list[tuple[str, str, ApprovalRecord]] = []
        for page in self.manifest:
            if page.approved:
                items.append((PAGE, page.page_id, page.approved))
        for asset in self.registry:
            if asset.approved:
                items.append((ASSET, asset.asset_id, asset.approved))
        return items

    def verify_approved(self) -> list[str]:
        """Recompute every approved checksum. Returns human-readable problems."""
        problems: list[str] = []
        for kind, identifier, approval in self.approved_artefacts():
            path = self.paths.resolve(approval.path)
            if not path.exists():
                problems.append(f"approved {kind} {identifier}: file missing ({approval.path})")
                continue
            actual = checksums.sha256_file(path)
            if actual != approval.sha256:
                problems.append(
                    f"approved {kind} {identifier}: checksum mismatch for {approval.path} "
                    f"(expected {approval.sha256[:12]}..., found {actual[:12]}...)"
                )
        return problems

    def relock_approved(self) -> int:
        """Re-apply read-only permissions to every approved artefact.

        Useful after a `git checkout`, which restores file contents but not modes.
        """
        count = 0
        for _kind, _id, approval in self.approved_artefacts():
            path = self.paths.resolve(approval.path)
            if path.exists() and not checksums.is_immutable(path):
                checksums.make_immutable(path)
                count += 1
        return count

    def latest_preflight(self) -> dict | None:
        if not self.paths.preflight_report.is_file():
            return None
        return read_json(self.paths.preflight_report)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def reference_paths(self, asset_ids: list[str], *, generative_only: bool = False) -> list[str]:
        """Book-relative paths to approved reference artwork, for visual tasks.

        `generative_only` excludes anything tagged (or defaulted to)
        `deterministic_layout` - a fixture built to test renderer geometry must
        never reach an image-generation task as a style example. Every visual
        task that hands references to an agent for actual generation sets this.
        """
        paths = []
        for asset_id in asset_ids:
            asset = self.registry.find(asset_id)
            if asset and asset.approved:
                if generative_only and effective_reference_role(asset) == "deterministic_layout":
                    continue
                paths.append(asset.approved.path)
        return paths

    def summary(self) -> dict:
        from dataclasses import asdict as _asdict

        page_counts = self.manifest.counts()
        return {
            "book_id": self.state.book_id,
            "title": self.state.title,
            "stage": self.state.stage,
            "stage_label": self.state.stage_label,
            "stage_number": self.state.stage_number,
            "mode": self.state.production_mode,
            "intake": {"required": self.state.intake.required,
                       "completed": self.state.intake.completed,
                       "draft_waiting": bool(self.state.intake.draft)},
            "production_policy": _asdict(self.state.production_policy),
            "format": {
                "trim": self.state.format.trim,
                "colour": self.state.format.colour,
                "bleed": self.state.format.bleed,
                "dpi": self.state.format.dpi,
            },
            "manuscript": {"version": self.state.manuscript.version,
                           "locked": self.state.manuscript.locked},
            "style": {"visual_version": self.state.style.visual_version,
                      "visual_locked": self.state.style.visual_locked,
                      "voice_version": self.state.style.voice_version,
                      "voice_locked": self.state.style.voice_locked},
            "pages": page_counts,
            "assets": self.registry.counts(),
            "blocked": self.state.blocked,
            "next_action": self.state.next_action,
            "manifest_problems": self.manifest.problems(),
        }


# ----------------------------------------------------------------------
# Defaults
# ----------------------------------------------------------------------


def _bump(version: str) -> str:
    try:
        return f"v{ids.revision_number(version) + 1}"
    except ValidationError:
        return "v1"


def _image_size(path: Path) -> tuple[int | None, int | None]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.width, image.height
    except Exception:  # noqa: BLE001 - non-image drafts (PDF pages) are fine
        return None, None


def _default_design_tokens(state: BookState) -> dict:
    """The book's typographic and colour system.

    Deliberately a small, editable file: this is the thing that stops chapter
    headings quietly changing style halfway through a book.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "trim": state.format.trim,
        "bleed_in": 0.125 if state.format.bleed else 0.0,
        "margins_in": {"top": 0.75, "outer": 0.625, "bottom": 0.75, "inner": 0.875},
        "fonts": {
            "display": "\"Bitstream Charter\", \"Charter\", \"DejaVu Serif\", Georgia, serif",
            "body": "\"Bitstream Charter\", \"Charter\", \"DejaVu Serif\", Georgia, serif",
            "accent": "\"DejaVu Sans\", \"Liberation Sans\", Helvetica, Arial, sans-serif",
            "mono": "\"DejaVu Sans Mono\", \"Liberation Mono\", monospace"
        },
        "type_scale_pt": {
            "chapter_number": 64,
            "chapter_title": 30,
            "heading": 17,
            "subheading": 12,
            "body": 10.5,
            "caption": 8.5,
            "folio": 8.5,
            "running_head": 7.5
        },
        "leading": {"body": 1.44, "heading": 1.15, "caption": 1.35},
        "palette": {
            "ink": "#1c1a17",
            "ink_soft": "#4a453e",
            "paper": "#fbf8f1",
            "accent": "#8c3b2e",
            "accent_soft": "#e6d7c3",
            "rule": "#c9bda8"
        },
        "rules": {
            "chapter_opener_starts_recto": True,
            "running_head_on_chapter_openers": False,
            "folio_on_full_bleed_pages": False
        }
    }


def _default_reference_set() -> dict:
    """The minimum visual reference set required before mass page production.

    Edit this per book - a book with no recurring animal sidekick should delete
    that entry rather than generate a pointless reference.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "description": (
            "Every entry here must be approved before `bookfactory lock visual` will pass. "
            "This is the set that later illustration tasks are generated against."
        ),
        "required": [
            {"asset_id": "ref-character-main", "kind": "character_reference",
             "title": "Main character reference",
             "description": "Front and three-quarter view, neutral and one signature expression."},
            {"asset_id": "ref-character-support", "kind": "character_reference",
             "title": "Supporting character reference",
             "description": "The recurring partner/friend/pet. Delete this entry if the book has none."},
            {"asset_id": "ref-layout-chapter-opener", "kind": "layout_reference",
             "title": "Chapter opener example",
             "description": "Approved example of how every chapter opener looks."},
            {"asset_id": "ref-page-editorial", "kind": "page_reference",
             "title": "Normal internal editorial page example",
             "description": "The most common page in the book."},
            {"asset_id": "ref-page-diagnostic", "kind": "page_reference",
             "title": "Diagram / checklist / test page example",
             "description": "The structured-content page family."},
            {"asset_id": "ref-palette", "kind": "palette_reference",
             "title": "Palette, type and layout rules",
             "description": "One sheet showing the palette swatches and type hierarchy."}
        ]
    }
