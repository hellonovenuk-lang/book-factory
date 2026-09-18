"""The `next` engine.

Given nothing but the repository, produce the single next thing that should
happen. This is what makes fresh-session operation possible: an agent that has
never seen this book before runs `bookfactory next` and knows what to do.

The derivation is pure and deterministic - the same repository always yields the
same next task.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import clock, gates, production, schema, stages
from bookfactory.core.jsonio import read_json, write_json
from bookfactory.core.models import Task

PLACEHOLDER_MARKERS = ("todo", "tbd", "<fill in>")


def _has_placeholders(path: Path) -> bool:
    if not path.is_file():
        return True
    text = path.read_text(encoding="utf-8").lower()
    return any(marker in text for marker in PLACEHOLDER_MARKERS)


def _task(book, task_id_suffix: str, **kwargs) -> Task:
    return Task(
        task_id=f"{book.state.book_id}-{task_id_suffix}",
        book_id=book.state.book_id,
        stage=book.state.stage,
        **kwargs,
    )


def _cmd(book, *parts: str) -> str:
    return " ".join(["bookfactory", *parts]).replace("<book>", book.state.book_id)


# ----------------------------------------------------------------------
# Derivation
# ----------------------------------------------------------------------


def next_task(book) -> Task | None:
    """The one thing to do next, or None when the book is finished."""
    task = None
    for derive in (
        _blocked_task,
        _intake_task,
        _brief_task,
        _voice_task,
        _manuscript_task,
        _visual_reference_task,
        _page_plan_task,
        _page_production_task,
        _qa_task,
        _assembly_task,
        _preflight_task,
        _release_task,
    ):
        task = derive(book)
        if task is not None:
            break
    task_mode = production.compute_mode(book, task)
    if task is not None:
        task.mode = task_mode
    return task


def _intake_task(book) -> Task | None:
    if not book.state.intake.required or book.state.intake.completed:
        return None
    from bookfactory.core import intake

    return _task(
        book, "intake",
        type="intake",
        summary="Complete the Book Factory intake questionnaire",
        instructions=(
            intake.questionnaire_text()
            + "\n\nAsk the user these questions once, in one compact exchange - not a "
            "forty-question creative brief. Then persist the answers:\n\n"
            f"  {_cmd(book, 'intake', '<book>', '--from-file <answers.json>')}\n\n"
            "This never needs asking again. A fresh session reads brief/intake.json "
            "and book.json's `intake` block instead of asking twice."
        ),
        output={"destination": "brief/intake.json", "expected_format": "json"},
        approval_required=True,
        gate="intake",
    )


def _blocked_task(book) -> Task | None:
    if not book.state.blocked:
        return None
    blocked = book.state.blocked
    return _task(
        book, "blocked",
        type="operator_decision",
        summary=f"Unblock the project: {blocked.get('reason')}",
        instructions=(
            f"The project was blocked on {blocked.get('since')}.\n"
            f"Reason: {blocked.get('reason')}\n"
            f"Needs: {blocked.get('needs') or 'an operator decision'}\n\n"
            f"Resolve it, then run `{_cmd(book, 'unblock', '<book>')}`."
        ),
        approval_required=True,
    )


def _brief_task(book) -> Task | None:
    if book.state.concept.locked:
        return None
    gate = gates.concept_lock(book)
    if not gate.ok:
        return _task(
            book, "brief",
            type="authoring",
            summary="Complete the book brief",
            instructions=(
                "Fill in brief/brief.md. Every TODO must be replaced with a real answer.\n"
                "The recognition triggers matter most - they are what the buyer is paying for.\n"
                "Also fill brief/concept.md and brief/audience.md.\n\n"
                "Blocking: " + "; ".join(gate.reasons)
            ),
            required_inputs=["brief/brief.md"],
            output={"destination": "brief/",
                    "submit_command": _cmd(book, "lock", "concept", "<book>"),
                    "expected_format": "markdown"},
            approval_required=True,
        )
    return _task(
        book, "lock-concept",
        type="operator_decision",
        summary="Approve and lock the concept",
        instructions=(
            "The brief is complete. Read it, and if you are happy, lock it.\n"
            "After the lock, later stages may not renegotiate the concept.\n\n"
            f"Run: {_cmd(book, 'lock', 'concept', '<book>')}"
        ),
        required_inputs=["brief/brief.md", "brief/concept.md"],
        approval_required=True,
        gate="concept_lock",
    )


def _voice_task(book) -> Task | None:
    if book.state.style.voice_locked:
        return None
    if not book.paths.writing_sample_file.is_file() or _has_placeholders(book.paths.writing_sample_file):
        return _task(
            book, "writing-sample",
            type="authoring",
            summary="Write the calibration writing sample",
            instructions=(
                "Write manuscript/writing-sample.md: one typical internal passage, one "
                "structured piece (checklist or test copy) and one chapter opener.\n"
                "This is written BEFORE the manuscript on purpose - the voice gets judged "
                "on real prose, and the whole manuscript is then written to match it.\n"
                "Follow style/voice-bible.md."
            ),
            required_inputs=["brief/brief.md", "style/voice-bible.md"],
            output={"destination": "manuscript/writing-sample.md",
                    "expected_format": "markdown"},
            approval_required=True,
        )
    if _has_placeholders(book.paths.voice_bible):
        return _task(
            book, "voice-bible",
            type="authoring",
            summary="Finish the humour / voice bible",
            instructions=(
                "Replace every TODO in style/voice-bible.md with real rules, drawn from what "
                "worked in the writing sample. Add anything grating you had to edit out to the "
                "banned phrases list - that list is how the same mistakes stop recurring."
            ),
            required_inputs=["manuscript/writing-sample.md"],
            output={"destination": "style/voice-bible.md", "expected_format": "markdown"},
            approval_required=True,
        )
    return _task(
        book, "lock-voice",
        type="operator_decision",
        summary="Approve the writing sample and lock the voice",
        instructions=(
            "Read manuscript/writing-sample.md. If it sounds right, lock the voice.\n"
            "Everything written afterwards references style/voice-bible.md.\n\n"
            f"Run: {_cmd(book, 'lock', 'voice', '<book>')}"
        ),
        required_inputs=["manuscript/writing-sample.md", "style/voice-bible.md"],
        approval_required=True,
        gate="voice_lock",
    )


def _manuscript_task(book) -> Task | None:
    if book.state.manuscript.locked:
        return None
    gate = gates.manuscript_lock(book)
    if not gate.ok:
        return _task(
            book, "manuscript",
            type="authoring",
            summary="Write the manuscript",
            instructions=(
                "Write manuscript/manuscript.md against the locked voice bible and the outline.\n"
                "Copy that will appear on a page must appear here first - page specs quote the "
                "locked manuscript, so nothing gets invented at layout time.\n\n"
                "Blocking: " + "; ".join(gate.reasons)
            ),
            required_inputs=["manuscript/outline.md", "style/voice-bible.md",
                             "manuscript/writing-sample.md"],
            output={"destination": "manuscript/manuscript.md", "expected_format": "markdown"},
            approval_required=True,
        )
    return _task(
        book, "lock-manuscript",
        type="operator_decision",
        summary="Approve and lock the manuscript",
        instructions=(
            "Read the manuscript. Locking snapshots it to manuscript/versions/ and checksums "
            "it, so page copy can never drift from an unlocked working file.\n\n"
            f"Run: {_cmd(book, 'lock', 'manuscript', '<book>')}"
        ),
        required_inputs=["manuscript/manuscript.md"],
        approval_required=True,
        gate="manuscript_lock",
    )


_REFERENCE_TASK_TYPE = {
    "character_reference": "character_reference",
    "layout_reference": "layout_reference",
    "page_reference": "layout_reference",
    "palette_reference": "layout_reference",
}


def _visual_reference_task(book) -> Task | None:
    if book.state.style.visual_locked:
        return None
    if _has_placeholders(book.paths.visual_bible):
        return _task(
            book, "visual-bible",
            type="authoring",
            summary="Finish the visual bible",
            instructions=(
                "Replace every TODO in style/visual-bible.md. Be concrete about character "
                "appearance, line style, medium, palette and edge treatment.\n"
                "A fresh agent with no chat history must be able to draw on-style from this file "
                "alone. Vague entries here are what caused the drift last time."
            ),
            required_inputs=["brief/brief.md", "style/design-tokens.json"],
            output={"destination": "style/visual-bible.md", "expected_format": "markdown"},
            approval_required=True,
        )

    for item in book.reference_set().get("required", []):
        asset_id = item["asset_id"]
        asset = book.registry.find(asset_id)
        if asset is None:
            return _task(
                book, f"{asset_id}-register",
                type="authoring",
                summary=f"Register required visual reference '{asset_id}'",
                instructions=(
                    f"The reference set requires '{asset_id}' ({item.get('title')}) but it is not "
                    "in the asset registry.\n\n"
                    f"Run: {_cmd(book, 'asset', 'add', '<book>', asset_id)} "
                    f"--kind {item.get('kind', 'character_reference')} "
                    f"--title {item.get('title', asset_id)!r}"
                ),
                asset_id=asset_id,
            )
        if asset.is_approved and not asset.revision_open:
            continue
        reviewable = asset.reviewable_draft()
        if reviewable is not None:
            return _approval_task(book, "asset", asset_id, reviewable.revision,
                                  f"Review reference artwork '{asset_id}'")
        return _task(
            book, f"{asset_id}-generate",
            type=_REFERENCE_TASK_TYPE.get(asset.kind, "illustration"),
            summary=f"Create visual reference: {asset.title or asset_id}",
            instructions=(
                f"{item.get('description', '')}\n\n"
                "Read style/visual-bible.md first and follow it exactly.\n"
                "No text of any kind inside the artwork - typography is set by the "
                "deterministic renderer, never generated.\n"
                "Save the result as a draft, then submit it."
            ).strip(),
            asset_id=asset_id,
            characters=asset.characters,
            references=book.reference_paths(asset.references, generative_only=True),
            required_inputs=["style/visual-bible.md", "style/design-tokens.json"],
            constraints=book.asset_constraints(asset),
            output={"destination": f"assets/drafts/{asset_id}/",
                    "submit_command": _cmd(book, "submit", "<book>", asset_id,
                                           "--kind asset --file <path>"),
                    "expected_format": "png"},
            approval_required=True,
        )

    return _task(
        book, "lock-visual",
        type="operator_decision",
        summary="Approve the reference set and lock the visual style",
        instructions=(
            "Every required visual reference is approved. Locking freezes them and lets mass "
            "page production begin. Until this lock, page production is refused - generating "
            "eighty pages before the style settled is the single most expensive mistake this "
            "system exists to prevent.\n\n"
            f"Run: {_cmd(book, 'lock', 'visual', '<book>')}"
        ),
        required_inputs=["style/visual-bible.md", "style/reference-set.json"],
        approval_required=True,
        gate="visual_lock",
    )


def _page_plan_task(book) -> Task | None:
    if len(book.manifest) > 0:
        return None
    return _task(
        book, "page-plan",
        type="authoring",
        summary="Create the page plan",
        instructions=(
            "Turn the locked manuscript into a page manifest: every page that will exist, in "
            "order, with a type and a title.\n\n"
            f"Run: {_cmd(book, 'plan', '<book>', '--from-file <plan.json>')}\n"
            "or add pages one at a time with `bookfactory plan <book> --add`.\n\n"
            "Page types: chapter_opener, editorial_illustration, text_illustration, checklist, "
            "diagnostic_test, comparison, diagram, quote, certificate, closing, front_matter, "
            "contents."
        ),
        required_inputs=["manuscript/manuscript.md", "manuscript/outline.md"],
        output={"destination": "pages/manifest.json"},
    )


def _approval_task(book, kind: str, identifier: str, revision: str, summary: str) -> Task:
    record = book._target(kind, identifier)
    draft = record.draft(revision)
    return _task(
        book, f"{identifier}-approve",
        type="approval",
        summary=summary,
        instructions=(
            f"Draft {revision} of {identifier} is waiting for an explicit decision.\n"
            f"File: {draft.path}\n\n"
            "Nothing is approved by silence. Approve or reject explicitly:\n"
            f"  {_cmd(book, 'approve', '<book>', identifier, f'--kind {kind} --draft {revision}')}\n"
            f"  {_cmd(book, 'reject', '<book>', identifier, f'--kind {kind} --draft {revision} --reason ' + chr(34) + '...' + chr(34))}"
        ),
        page_id=identifier if kind == "page" else None,
        asset_id=identifier if kind == "asset" else None,
        approval_required=True,
    )


def _page_production_task(book) -> Task | None:
    if len(book.manifest) == 0:
        return None
    gate = gates.page_production(book)
    if not gate.ok:
        return _task(
            book, "page-production-blocked",
            type="operator_decision",
            summary="Page production is blocked",
            instructions="Resolve before producing pages:\n  - " + "\n  - ".join(gate.reasons),
            approval_required=False,
        )

    for page in book.manifest:
        if not page.spec:
            return _task(
                book, f"{page.page_id}-spec",
                type="authoring",
                summary=f"Write the page spec for {page.page_id} - {page.title}",
                instructions=(
                    f"Create pages/specs/{page.page_id}.json.\n"
                    "It must contain the exact final copy for the page, taken from the locked "
                    f"manuscript ({book.state.manuscript.version}), plus the illustration brief.\n"
                    "Copy comes before artwork, always: the picture is drawn to fit the words, "
                    "not the other way round.\n"
                    "Schema: schemas/page-spec.schema.json"
                ),
                page_id=page.page_id,
                required_inputs=[book.state.manuscript.path or "manuscript/manuscript.md",
                                 "style/visual-bible.md"],
                output={"destination": f"pages/specs/{page.page_id}.json",
                        "expected_format": "json"},
            )

        for asset_id in page.required_assets:
            asset = book.registry.find(asset_id)
            if asset is None:
                return _task(
                    book, f"{asset_id}-register",
                    type="authoring",
                    summary=f"Register illustration asset '{asset_id}' for {page.page_id}",
                    instructions=(
                        f"Page {page.page_id} requires asset '{asset_id}', which is not in the "
                        "registry.\n\n"
                        f"Run: {_cmd(book, 'asset', 'add', '<book>', asset_id)} "
                        f"--kind illustration --page {page.page_id}"
                    ),
                    page_id=page.page_id, asset_id=asset_id,
                )
            if asset.is_approved and not asset.revision_open:
                continue
            reviewable = asset.reviewable_draft()
            if reviewable is not None:
                return _approval_task(book, "asset", asset_id, reviewable.revision,
                                      f"Review artwork '{asset_id}' for page {page.page_id}")
            return _illustration_task(book, page, asset)

        if page.is_approved and not page.revision_open:
            continue

        latest = page.latest_draft()
        if latest and latest.status == "draft":
            return _approval_task(book, "page", page.page_id, latest.revision,
                                  f"Approve page {page.page_id} - {page.title}")

        return _task(
            book, f"{page.page_id}-render",
            type="page_render",
            summary=f"Render page {page.page_id} - {page.title}",
            instructions=(
                "Render the page deterministically from its spec and its approved artwork. "
                "No generative step is involved: all typography, page numbers and structured "
                "content are set by the renderer.\n\n"
                f"Run: {_cmd(book, 'render', '<book>', '--page ' + page.page_id, '--submit')}"
            ),
            page_id=page.page_id,
            required_inputs=[page.spec] + [
                p for p in book.reference_paths(page.required_assets)
            ],
            output={"destination": f"pages/drafts/{page.page_id}/",
                    "submit_command": _cmd(book, "submit", "<book>", page.page_id,
                                           "--kind page --file <path>"),
                    "expected_format": "pdf"},
            approval_required=True,
        )
    return None


def _illustration_task(book, page, asset) -> Task:
    spec = {}
    try:
        spec = book.read_page_spec(page.page_id)
    except Exception:  # noqa: BLE001 - a missing spec is handled earlier
        spec = {}
    illustration = spec.get("illustration") or {}
    reference_ids = illustration.get("references") or asset.references or book.required_reference_ids()
    failing = asset.failing_draft()
    retry_count = len([d for d in asset.drafts if d.constraint_failures])
    remediation = ""
    if failing is not None:
        from bookfactory.core import constraints as constraint_rules

        remediation = (
            f"\n\nDraft {failing.revision} was submitted and does NOT meet the "
            "requirements of this task, so it was not put forward for approval:\n  - "
            + constraint_rules.describe(failing.constraint_failures)
            + "\n\nProduce a corrected version and submit it as a new draft. The failed "
            "draft is kept at "
            f"{failing.path} - do not overwrite it."
        )

    revising = ""
    if asset.revision_open and asset.approved:
        revising = (
            f"\n\nThis replaces artwork already approved as revision "
            f"{asset.approved.revision}. That file stays canonical until the replacement is "
            "approved, so do not touch it - submit a new draft."
        )
    return _task(
        book, f"{asset.asset_id}-illustration",
        type="illustration",
        summary=(
            f"Re-do illustration '{asset.asset_id}' for page {page.page_id} - "
            f"draft {failing.revision} failed a hard constraint" if failing is not None else
            f"Create replacement illustration '{asset.asset_id}' for page {page.page_id}"
            if asset.revision_open else
            f"Create illustration '{asset.asset_id}' for page {page.page_id}"),
        instructions=(
            f"{illustration.get('concept') or asset.description or ''}\n\n"
            "Match the locked references exactly - same character, same line style, same "
            "palette, same edge treatment. If you cannot match them, stop and say so rather "
            "than producing something near enough.\n"
            "No text, numbers, labels or signatures inside the artwork."
            f"{revising}{remediation}"
        ).strip(),
        page_id=page.page_id,
        asset_id=asset.asset_id,
        scene=illustration.get("scene") or asset.description,
        characters=illustration.get("characters") or asset.characters,
        references=book.reference_paths(reference_ids, generative_only=True),
        required_inputs=[page.spec, "style/visual-bible.md"],
        constraints={
            **book.asset_constraints(asset),
            "embedded_text": bool(illustration.get("embedded_text", False)),
        },
        output={"destination": f"assets/drafts/{asset.asset_id}/",
                "submit_command": _cmd(book, "submit", "<book>", asset.asset_id,
                                       "--kind asset --file <path>"),
                "expected_format": "png"},
        approval_required=True,
        remediation=failing is not None,
        retry_count=retry_count,
    )


def _qa_task(book) -> Task | None:
    if len(book.manifest) == 0:
        return None
    if not gates.page_approval_complete(book).ok:
        return None
    report = _latest_qa(book)
    if report is None or report.get("summary", {}).get("status") == "fail":
        reason = "QA has not been run" if report is None else "the last QA run failed"
        return _task(
            book, "qa",
            type="qa",
            summary="Run QA across the book",
            instructions=(
                f"Every page is approved and {reason}.\n\n"
                f"Run: {_cmd(book, 'qa', '<book>')}\n\n"
                "Content, visual and technical layers run together. Findings marked "
                "'needs_human' cannot be decided by a machine - a person or an agent has to "
                "look at the pages."
            ),
        )
    return None


def _latest_qa(book) -> dict | None:
    if not book.paths.qa_latest.is_file():
        return None
    return read_json(book.paths.qa_latest)


def _assembly_task(book) -> Task | None:
    if not gates.page_approval_complete(book).ok:
        return None
    if book.paths.interior_pdf.is_file():
        return None
    gate = gates.assembly(book)
    if not gate.ok:
        return _task(
            book, "assembly-blocked",
            type="operator_decision",
            summary="Assembly is blocked",
            instructions="Assembly fails closed. Resolve:\n  - " + "\n  - ".join(gate.reasons),
        )
    return _task(
        book, "assemble",
        type="assembly",
        summary="Assemble the interior PDF",
        instructions=(
            "Assembly is mechanical: approved pages, in manifest order, checksums verified. "
            "It never regenerates, rewrites or reinterprets anything.\n\n"
            f"Run: {_cmd(book, 'assemble', '<book>')}"
        ),
    )


def _preflight_task(book) -> Task | None:
    if not book.paths.interior_pdf.is_file():
        return None
    report = book.latest_preflight()
    if report is not None and report.get("status") != "fail":
        #: Warnings are informational - a 24-page gift book cannot carry spine
        #: text and that is not something to keep re-running preflight over.
        return None
    return _task(
        book, "preflight",
        type="preflight",
        summary="Run KDP preflight",
        instructions=(
            "Check the assembled interior against the KDP profile in "
            f"bookfactory/kdp/profiles/{book.state.format.kdp_profile}.json.\n\n"
            f"Run: {_cmd(book, 'preflight', '<book>')}"
        ),
    )


def _release_task(book) -> Task | None:
    if book.state.stage == stages.RELEASE_READY:
        return None
    gate = gates.release_ready(book)
    if not gate.ok:
        return None
    return _task(
        book, "release",
        type="operator_decision",
        summary="Mark the book release ready",
        instructions=(
            "Interior assembled and preflight passed.\n\n"
            f"Run: {_cmd(book, 'advance', '<book>', '--to release_ready')}"
        ),
        approval_required=True,
        gate="release_ready",
    )


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------


def task_path(book, task: Task) -> Path:
    return book.paths.open_tasks_dir / f"{task.task_id}.json"


def write_task(book, task: Task) -> Path:
    data = task.to_dict()
    schema.validate("task", data, context=task.task_id)
    path = task_path(book, task)
    write_json(path, data)
    return path


def close_task(book, task_id: str, *, status: str = "done") -> Path | None:
    source = book.paths.open_tasks_dir / f"{task_id}.json"
    if not source.is_file():
        return None
    data = read_json(source)
    data["status"] = status
    data["closed_at"] = clock.timestamp()
    destination = book.paths.done_tasks_dir / source.name
    write_json(destination, data)
    source.unlink()
    return destination


def open_tasks(book) -> list[dict]:
    if not book.paths.open_tasks_dir.is_dir():
        return []
    return [read_json(p) for p in sorted(book.paths.open_tasks_dir.glob("*.json"))]


def sync_open_task(book) -> Task | None:
    """Keep `tasks/open/` holding exactly the current next task.

    Stale task files are worse than none - they are how an agent ends up doing
    work that was superseded three approvals ago.
    """
    task = next_task(book)
    directory = book.paths.open_tasks_dir
    directory.mkdir(parents=True, exist_ok=True)
    keep = f"{task.task_id}.json" if task else None
    for existing in directory.glob("*.json"):
        if existing.name != keep:
            close_task(book, existing.stem, status="done")
    if task:
        write_task(book, task)
    return task
