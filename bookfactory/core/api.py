"""The library API.

Every operation Book Factory can perform is a plain Python function here. The
CLI is a thin adapter over this module, and a future MCP server will be another
thin adapter - no business logic lives in either.

The function names deliberately mirror the operations an agent will want:

    create_book, status, next_task, get_task, submit_asset, approve, reject,
    qa, assemble, preflight
"""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import stages, tasks as task_module
from bookfactory.core.book import ASSET, PAGE, Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import read_json, write_json
from bookfactory.core.paths import books_dir

__all__ = [
    "list_books", "create_book", "create_from_idea", "status", "next_task", "get_task",
    "plan_pages", "write_page_spec", "register_asset", "submit_asset", "submit_intake",
    "draft_intake", "confirm_intake", "show_pictures", "set_pictures", "show_policy", "set_policy",
    "approve", "reject", "revise",
    "lock", "advance", "validate", "render", "render_reference", "qa", "assemble", "review",
    "preflight", "audit_history", "relock", "produce",
]


# ----------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------


def list_books(root: str | Path | None = None) -> list[dict]:
    directory = books_dir(root)
    if not directory.is_dir():
        return []
    books = []
    for candidate in sorted(directory.iterdir()):
        state_file = candidate / "book.json"
        if not state_file.is_file():
            continue
        data = read_json(state_file)
        books.append({
            "book_id": data.get("book_id", candidate.name),
            "title": data.get("title"),
            "stage": data.get("stage"),
            "stage_label": stages.label(data.get("stage", stages.IDEA)),
            "updated_at": data.get("updated_at"),
        })
    return books


# ----------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------


def _require_policy_choice(policy: str | None) -> str:
    """The operator's explicit policy choice, or a refusal that says how to give one."""
    from bookfactory.core.intake import PRODUCTION_POLICIES

    choice = (policy or "").strip().lower()
    if not choice:
        raise ValidationError(
            "A production policy is required: the operator must choose one explicitly",
            remedy="Pass policy= (CLI: --policy) as one of: " + ", ".join(PRODUCTION_POLICIES)
                   + ". visual_checkpoint is recommended.",
        )
    if choice not in PRODUCTION_POLICIES:
        raise ValidationError(f"Unknown production policy {policy!r}",
                              remedy="Choose one of: " + ", ".join(PRODUCTION_POLICIES) + ".")
    return choice


def create_book(title: str, *, policy: str, series_from: str | None = None, **kwargs) -> dict:
    """Start a book whose operator supplies every production detail up front.

    `policy` is required - `checkpointed`, `visual_checkpoint` or
    `autonomous` - because a book's autonomy is the operator's explicit
    choice, never a default nobody picked (`AGENTS.md` section 3). It is
    recorded as `production_policy` with source `create_command`.

    `series_from` starts the book from an earlier, locked book's voice,
    visual style, design tokens, reference art (as drafts) and cover design
    (`bookfactory.core.series`). The source is checked *before* anything is
    created, so a refused preset leaves nothing behind. Nothing is approved
    or locked on the operator's behalf either way.
    """
    from bookfactory.core import production, series as series_module

    choice = _require_policy_choice(policy)
    root = kwargs.pop("root", None)
    source_book = None
    if series_from:
        source_book = Book.load(series_from, root)
        series_module.check_source(source_book)
    book = Book.create(title, root=root, **kwargs)
    recorded = production.policy_from_choice(choice, source="create_command")
    book.state.production_policy = recorded
    book.log("production_policy_recorded", production_policy=recorded.mode,
             operator_authorized=recorded.operator_authorized, source=recorded.source)
    series_preset = None
    if source_book is not None:
        series_preset = series_module.apply_preset(book, source_book)
    book.save()
    task_module.sync_open_task(book)
    result = {
        "book_id": book.state.book_id,
        "path": str(book.paths.root),
        "stage": book.state.stage,
        "next_action": book.state.next_action,
        "created_files": sorted(
            str(p.relative_to(book.paths.root))
            for p in book.paths.root.rglob("*") if p.is_file()
        ),
    }
    if series_preset is not None:
        result["series_preset"] = series_preset
    return result


def _title_from_idea(idea: str) -> str:
    text = " ".join(idea.strip().split())
    if not text:
        return "Untitled"
    return " ".join(text.split(" ")[:8])[:80]


def create_from_idea(idea: str, *, title: str | None = None, **kwargs) -> dict:
    """Start a book from nothing but a one-line idea.

    Unlike `create_book`, this marks the intake questionnaire required: the
    book cannot proceed past it until the operator's answers are persisted.
    `bookfactory create` stays available for callers (including scripts and
    tests) that already know every production detail up front.
    """
    root = kwargs.pop("root", None)
    book = Book.create(title or _title_from_idea(idea), root=root, idea=idea, **kwargs)
    book.state.intake.required = True
    book.save()
    task_module.sync_open_task(book)
    return {
        "book_id": book.state.book_id,
        "path": str(book.paths.root),
        "stage": book.state.stage,
        "next_action": book.state.next_action,
    }


def status(book_id: str, *, root: str | Path | None = None) -> dict:
    """Where the book stands. Read-only: it writes nothing to the repository."""
    book = Book.load(book_id, root)
    book.refresh_view()
    summary = book.summary()
    summary["gates"] = _gate_summary(book)
    from bookfactory.core import cover, gates
    summary["approved_integrity"] = book.verify_approved() + cover.integrity_problems(book)
    summary["qa"] = _qa_summary(book)
    summary["outputs"] = {
        "interior_pdf": (book.paths.relative(book.paths.interior_pdf)
                         if book.paths.interior_pdf.is_file() else None),
        "preflight": (book.latest_preflight() or {}).get("status"),
    }
    summary["readiness"] = cover.readiness(book)
    #: The approved cover is the tracked, checksummed file cover.json records;
    #: output/cover.pdf is only its regenerable upload copy.
    approved_cover = cover.approved_file(book) if cover.required(book) else None
    summary["outputs"]["cover_pdf"] = (
        approved_cover if approved_cover and book.paths.resolve(approved_cover).is_file()
        else None)
    summary["outputs"]["cover_preflight"] = (cover.load(book).get("preflight") or {}).get("status")
    if summary["stage"] == stages.RELEASE_READY and not gates.release_ready(book).ok:
        summary["stage_label"] = "Cover pending (interior ready)"
    return summary


def _gate_summary(book) -> list[dict]:
    from bookfactory.core import gates

    summary = []
    for stage_key, check in gates.ENTRY_GATES.items():
        result = check(book)
        summary.append({"stage": stage_key, "ok": result.ok, "reasons": result.reasons})
    return summary


def _qa_summary(book) -> dict | None:
    from bookfactory.qa.runner import latest_report

    report = latest_report(book)
    if report is None:
        return None
    return {"run_at": report["run_at"], **report["summary"]}


def next_task(book_id: str, *, root: str | Path | None = None,
              persist: bool = False) -> dict | None:
    """The single next task. Read-only unless `persist` is set.

    Every command that changes a book already rewrites `tasks/open/` and
    `book.json`'s `next_action`. `persist=True` (`next --persist`) does the
    same on demand - for example after hand-editing a manuscript or brief, so
    an agent reading files without a shell sees the current task.
    """
    book = Book.load(book_id, root)
    if persist:
        task = task_module.sync_open_task(book)
        book.save()
    else:
        book.refresh_view()
        task = task_module.next_task(book)
    return task.to_dict() if task else None


def get_task(book_id: str, task_id: str | None = None, *,
             root: str | Path | None = None) -> dict | None:
    """A task in full: the current one by default, or a recorded one by id. Read-only."""
    book = Book.load(book_id, root)
    if task_id is None:
        book.refresh_view()
        task = task_module.next_task(book)
        return task.to_dict() if task else None
    for directory in (book.paths.open_tasks_dir, book.paths.done_tasks_dir):
        path = directory / f"{task_id}.json"
        if path.is_file():
            return read_json(path)
    raise ValidationError(
        f"No task {task_id!r} for book {book_id}",
        remedy="Run `bookfactory next <book>` to see the current task.",
    )


# ----------------------------------------------------------------------
# Planning
# ----------------------------------------------------------------------


def plan_pages(book_id: str, pages: list[dict], *, root: str | Path | None = None,
               renumber: bool = True, front_matter_pages: int = 0) -> dict:
    """Add pages to the plan, each optionally with its spec.

    Every spec is checked before anything is written, so one bad spec leaves
    the book unchanged. Artwork a spec names is registered for its page.
    """
    book = Book.load(book_id, root)
    known_assets = {asset.asset_id for asset in book.registry.assets}
    added = []
    specs = []
    problems = []
    planned_pictures: set[str] = set()
    for entry in pages:
        record = book.add_page(
            title=entry["title"],
            type=entry["type"],
            chapter=entry.get("chapter"),
            sequence=entry.get("sequence"),
            page_id=entry.get("page_id"),
            required_assets=entry.get("required_assets"),
            notes=entry.get("notes"),
        )
        added.append(record.page_id)
        if entry.get("spec"):
            try:
                book.prepare_page_spec(record.page_id, entry["spec"],
                                       planned_pictures=planned_pictures)
            except ValidationError as exc:
                problems.extend(f"{record.page_id}: {p}" for p in exc.problems or [str(exc)])
                continue
            specs.append((record.page_id, entry["spec"]))
            picture = (entry["spec"].get("illustration") or {}).get("asset_id")
            if picture:
                planned_pictures.add(picture)
    if problems:
        raise ValidationError(
            f"{len(problems)} problem(s) in the page specs; nothing was planned",
            problems=problems,
            remedy="Fix the listed specs in the plan file and run the command again.",
        )
    for page_id, spec in specs:
        book.write_page_spec(page_id, spec)
    registered = [asset.asset_id for asset in book.registry.assets
                  if asset.asset_id not in known_assets]
    if renumber:
        book.manifest.renumber_printed(front_matter=front_matter_pages)
    book.state.page_plan.page_count = len(book.manifest)
    book.log("page_planned", added=added, total=len(book.manifest),
             specs=len(specs), assets_registered=registered or None)
    book.save()
    task_module.sync_open_task(book)
    return {"added": added, "total": len(book.manifest), "specs": len(specs),
            "assets_registered": registered, "problems": book.manifest.problems()}


def plan_from_manuscript(book_id: str, out: str | Path, *,
                         backends: list[str] | None = None,
                         root: str | Path | None = None) -> dict:
    """Turn the locked manuscript into a plan file, fit-tested page by page.

    Writes `out` only: `{"pages": [...], "warnings": [...], "fit": [...]}`,
    which `plan --from-file` loads as it stands. Nothing in the book changes;
    the fit test renders in a temporary folder, and the Book it borrows is
    never saved.
    """
    from bookfactory.core.manuscript_plan import parse_manuscript
    from bookfactory.render.fit import fit_pages

    book = Book.load(book_id, root)
    if not book.state.manuscript.locked:
        raise ValidationError(
            "The manuscript is not locked, so a plan built from it would drift",
            remedy="Lock the manuscript first; `bookfactory next` says how.",
        )
    parsed = parse_manuscript(book.paths.manuscript_file.read_text(encoding="utf-8"))
    fitted = fit_pages(book, parsed["pages"], backends=backends)
    plan = {"pages": fitted["pages"], "warnings": parsed["warnings"],
            "fit": fitted["report"]}
    path = write_json(out, plan)
    counts: dict[str, int] = {}
    for entry in fitted["report"]:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    return {"out": str(path), "pages": len(fitted["pages"]),
            "manuscript_sections": len(parsed["pages"]), "warnings": parsed["warnings"],
            "fit": fitted["report"], "fit_counts": counts}


def write_page_spec(book_id: str, page_id: str, spec: dict, *,
                    root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    known_assets = {asset.asset_id for asset in book.registry.assets}
    path = book.write_page_spec(page_id, spec)
    book.save()
    task_module.sync_open_task(book)
    registered = [asset.asset_id for asset in book.registry.assets
                  if asset.asset_id not in known_assets]
    return {"page_id": page_id, "spec": book.paths.relative(path),
            "assets_registered": registered}


def register_asset(book_id: str, asset_id: str, *, root: str | Path | None = None,
                   **kwargs) -> dict:
    book = Book.load(book_id, root)
    record = book.register_asset(asset_id, **kwargs)
    book.save()
    task_module.sync_open_task(book)
    return record.to_dict()


def submit_intake(book_id: str, answers: dict, *, root: str | Path | None = None) -> dict:
    """Persist the operator's one-time answers to the intake questionnaire.

    This is the only way `book.json`'s `intake` gets set, and it records
    `production_policy` from question 12 (`create_book` and `set_policy` are
    the other two ways a policy is chosen). A fresh session never needs to ask
    again - it reads `brief/intake.json` or `book.json`'s `intake` block
    instead. `confirm_intake` completes intake through the same path.
    """
    book = Book.load(book_id, root)
    return _complete_intake(book, dict(answers), root=root)


def _complete_intake(book, answers: dict, *, root, drafted_by: str | None = None,
                     confirmed_by: str | None = None,
                     changed: list[str] | None = None) -> dict:
    from bookfactory.core import clock, intake as intake_module, production

    problems = intake_module.validate_answers(answers)
    if problems:
        raise ValidationError(
            "Questionnaire answers are incomplete or invalid",
            problems=problems,
            remedy="Fix the listed answers and submit again.",
        )
    book.state.intake.completed = True
    book.state.intake.completed_at = clock.timestamp()
    book.state.intake.answers = dict(answers)
    book.state.intake.draft = None
    book.state.intake.drafted_by = drafted_by
    book.state.intake.confirmed_by = confirmed_by
    book.state.intake.changed_on_confirm = list(changed or [])
    policy = production.policy_from_choice(answers["production_policy"],
                                           source="intake_questionnaire")
    book.state.production_policy = policy
    record = {"answers": book.state.intake.answers,
              "completed_at": book.state.intake.completed_at}
    if drafted_by:
        record.update({"drafted_by": drafted_by, "confirmed_by": confirmed_by,
                       "changed_on_confirm": book.state.intake.changed_on_confirm})
    write_json(book.paths.brief_dir / "intake.json", record)
    draft_file = book.paths.brief_dir / "intake-draft.json"
    if draft_file.is_file():
        draft_file.unlink()
    book.log("intake_submitted", production_policy=policy.mode,
             operator_authorized=policy.operator_authorized,
             drafted_by=drafted_by, confirmed_by=confirmed_by,
             changed_on_confirm=list(changed or []) if drafted_by else None)
    book.save()
    task_module.sync_open_task(book)
    return status(book.state.book_id, root=root)


def _require_open_intake(book) -> None:
    if book.state.intake.completed:
        raise ValidationError(
            "Intake is already complete for this book",
            remedy="Intake happens once. Read brief/intake.json instead of asking again.",
        )


def draft_intake(book_id: str, answers: dict, *, by: str, unclear: list[str] | None = None,
                 root: str | Path | None = None) -> dict:
    """Save an agent's best-guess intake answers for the operator to confirm.

    A draft never completes intake, and it may never contain the production
    policy: that stays the operator's own choice, made at `confirm_intake`.
    Questions the agent could not answer from the idea go in `unclear`. A new
    draft replaces an older one.
    """
    from bookfactory.core import clock, intake as intake_module

    if not by or not by.strip():
        raise ValidationError("A draft needs --by: who drafted it")
    answers = dict(answers)
    unclear = list(unclear or [])
    book = Book.load(book_id, root)
    _require_open_intake(book)
    problems = intake_module.validate_draft(answers, unclear)
    if problems:
        raise ValidationError(
            "The drafted intake answers cannot be saved",
            problems=problems,
            remedy="Fix the listed answers; list anything you cannot tell from the idea "
                   "as unclear.",
        )
    draft = {"answers": answers, "unclear": unclear, "drafted_by": by,
             "drafted_at": clock.timestamp()}
    book.state.intake.draft = draft
    write_json(book.paths.brief_dir / "intake-draft.json", draft)
    book.log("intake_drafted", drafted_by=by, unclear=unclear or None)
    book.save()
    task_module.sync_open_task(book)
    return {"book_id": book_id, "draft": draft,
            "still_to_ask": unclear + ["production_policy"]}


def confirm_intake(book_id: str, *, by: str, policy: str, changes: dict | None = None,
                   root: str | Path | None = None) -> dict:
    """Complete intake from the drafted answers, as the operator confirmed them.

    `changes` are the operator's corrections and their answers to the unclear
    questions; `policy` is the production policy they chose. The full set is
    checked exactly as `submit_intake` checks it, and the book records who
    drafted and who confirmed the answers, and which the operator changed.
    """
    if not by or not by.strip():
        raise ValidationError("Confirming intake needs --by: the operator confirming it")
    book = Book.load(book_id, root)
    _require_open_intake(book)
    draft = book.state.intake.draft
    if not draft:
        raise ValidationError(
            "There is no drafted intake to confirm",
            remedy="Draft the answers first with `bookfactory intake <book> --draft`, "
                   "or submit all of them with `bookfactory intake <book> --from-file`.",
        )
    changes = dict(changes or {})
    if "production_policy" in changes:
        raise ValidationError("Give the production policy with --policy, not as a change")
    unclear = draft.get("unclear", [])
    answers = {key: value for key, value in draft["answers"].items() if key not in unclear}
    changed = sorted(key for key, value in changes.items()
                     if draft["answers"].get(key) != value)
    answers.update(changes)
    missing = [key for key in unclear if key not in answers]
    if missing:
        raise ValidationError(
            "Some questions the draft left unclear have no answer yet",
            problems=[f"'{key}' is still unclear" for key in missing],
            remedy="Ask the operator and pass each answer with --set key=value.",
        )
    answers["production_policy"] = policy
    return _complete_intake(book, answers, root=root, drafted_by=draft["drafted_by"],
                            confirmed_by=by, changed=changed)


def show_pictures(book_id: str, *, root: str | Path | None = None) -> dict:
    """The book's picture budget and how many page pictures it has. Read-only."""
    from dataclasses import asdict

    book = Book.load(book_id, root)
    return {"book_id": book_id, "pictures": asdict(book.state.pictures),
            "page_pictures": sorted(book.page_picture_ids())}


def set_pictures(book_id: str, budget: str, *, by: str, count: int | None = None,
                 reason: str | None = None, root: str | Path | None = None) -> dict:
    """Change a book's picture budget. Operator only.

    Each page picture costs image credits and a review, so how many a book
    has is the operator's decision: `by` names them, and the change - old and
    new budget, who, when and why - is written to the audit log as
    `picture_budget_changed`. Pictures already planned are left as they are;
    the budget is checked when a spec is written.
    """
    from dataclasses import asdict

    from bookfactory.core import clock
    from bookfactory.core.models import PICTURE_BUDGETS, PictureBudget

    if not by or not by.strip():
        raise ValidationError("Changing the picture budget needs --by: the operator choosing it")
    if budget not in PICTURE_BUDGETS:
        raise ValidationError(f"Unknown picture budget {budget!r}",
                              remedy="Choose one of: " + ", ".join(PICTURE_BUDGETS))
    if budget == "limit":
        if count is None or count < 0:
            raise ValidationError("The limit budget needs --count: how many page pictures")
    elif count is not None:
        raise ValidationError("--count only goes with the limit budget")
    book = Book.load(book_id, root)
    old = asdict(book.state.pictures)
    book.state.pictures = PictureBudget(budget=budget, count=count, set_by=by,
                                        set_at=clock.timestamp(),
                                        source="pictures_set_command")
    book.log("picture_budget_changed", old_budget=old["budget"], old_count=old["count"],
             budget=budget, count=count, by=by, reason=reason)
    book.save()
    task_module.sync_open_task(book)
    return show_pictures(book_id, root=root)


def show_policy(book_id: str, *, root: str | Path | None = None) -> dict:
    """The book's recorded production policy and the current task's mode. Read-only."""
    from dataclasses import asdict

    book = Book.load(book_id, root)
    book.refresh_view()
    return {"book_id": book_id, "production_policy": asdict(book.state.production_policy),
            "mode": book.state.production_mode}


def set_policy(book_id: str, mode: str, *, by: str, reason: str | None = None,
               root: str | Path | None = None) -> dict:
    """Switch an existing book's production policy. Operator only.

    This is how autonomy is granted (or withdrawn) after creation, so it is
    never something an agent decides: `by` names the operator who chose it,
    and the change - old mode, new mode, who, when and why - is written to
    the audit log as `production_policy_changed`. The next task's `mode`
    reflects the new policy at once.
    """
    from dataclasses import asdict

    from bookfactory.core import production

    if not (by or "").strip():
        raise ValidationError("Changing a production policy needs the operator's name",
                              remedy="Pass by= (CLI: --by <operator>).")
    choice = _require_policy_choice(mode)
    book = Book.load(book_id, root)
    if book.state.intake.required and not book.state.intake.completed:
        raise ValidationError(
            "This book's intake questionnaire is not answered yet, and its answers set the policy",
            remedy="Answer question 12 of the questionnaire (`bookfactory intake`) instead.",
        )
    previous = book.state.production_policy.mode
    policy = production.policy_from_choice(choice, source="policy_set_command")
    book.state.production_policy = policy
    book.log("production_policy_changed", old_mode=previous, new_mode=policy.mode,
             operator_authorized=policy.operator_authorized, by=by.strip(), reason=reason)
    book.save()
    task_module.sync_open_task(book)
    return {"book_id": book_id, "previous_mode": previous,
            "production_policy": asdict(policy), "mode": book.state.production_mode,
            "next_action": book.state.next_action}


# ----------------------------------------------------------------------
# Drafts and approvals
# ----------------------------------------------------------------------


def submit_asset(book_id: str, identifier: str, file: str | Path, *, kind: str = ASSET,
                 revision: str | None = None, note: str | None = None,
                 source: str | None = None, root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    draft = book.submit(kind, identifier, file, revision=revision, note=note, source=source)
    task_module.sync_open_task(book)
    return {"kind": kind, "id": identifier, **draft.to_dict(with_dimensions=True)}


def approve(book_id: str, identifier: str, *, kind: str = PAGE, revision: str | None = None,
            by: str | None = None, note: str | None = None, autonomous: bool = False,
            root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    approval = book.approve(kind, identifier, revision=revision, by=by, note=note,
                            autonomous=autonomous)
    task_module.sync_open_task(book)
    return {"kind": kind, "id": identifier, **approval.to_dict(with_dimensions=True)}


def approve_passing(book_id: str, *, by: str | None = None, kind: str | None = None,
                    dry_run: bool = False, autonomous: bool = False, note: str | None = None,
                    root: str | Path | None = None) -> dict:
    """Approve, one by one through the normal single approval, the newest
    reviewable draft of every asset and page that has one and is not already
    approved (or has a revision open).

    Assets before pages, each through `Book.approve` so every existing check
    (checksum, constraints, immutability, autonomous authorization) still
    applies. A draft that failed a measured constraint is never reviewable, so
    it is never a candidate - it is listed under "not_ready" instead, for
    information only. The cover artwork asset has its own approval and is
    never included. `dry_run` changes nothing.
    """
    from bookfactory.core import gates
    from bookfactory.core.cover import ART_ID
    from bookfactory.core.errors import BookFactoryError

    if not (by or "").strip():
        raise ValidationError("Batch approval needs the operator's name",
                              remedy="Pass by= (CLI: --by <operator>).")
    if kind is not None and kind not in (PAGE, ASSET):
        raise ValidationError(f"Cannot batch-approve kind {kind!r}",
                              remedy=f"Valid kinds: {PAGE}, {ASSET}.")

    book = Book.load(book_id, root)
    if autonomous and not gates.autonomous_approval_authorized(book).ok:
        raise ValidationError(
            "This book's production_policy does not authorize autonomous approval",
            remedy=("Answer the intake questionnaire's production policy question with "
                    "FULL AUTONOMOUS or VISUAL CHECKPOINT, or approve explicitly without "
                    "--autonomous."),
        )

    candidates: list[tuple[str, str]] = []  # (kind, identifier)
    not_ready: list[dict] = []

    if kind in (None, ASSET):
        for asset in book.registry:
            if asset.asset_id == ART_ID:
                continue
            reviewable = asset.reviewable_draft()
            if reviewable is not None and (not asset.is_approved or asset.revision_open):
                candidates.append((ASSET, asset.asset_id))
                continue
            failing = asset.failing_draft()
            if failing is not None and reviewable is None:
                not_ready.append({"kind": ASSET, "id": asset.asset_id,
                                  "revision": failing.revision,
                                  "failures": list(failing.constraint_failures)})

    if kind in (None, PAGE):
        for page in book.manifest:
            reviewable = page.reviewable_draft()
            if reviewable is not None and (not page.is_approved or page.revision_open):
                candidates.append((PAGE, page.page_id))
                continue
            failing = page.failing_draft()
            if failing is not None and reviewable is None:
                not_ready.append({"kind": PAGE, "id": page.page_id,
                                  "revision": failing.revision,
                                  "failures": list(failing.constraint_failures)})

    if dry_run:
        would_approve = []
        for item_kind, identifier in candidates:
            record = book.registry.get(identifier) if item_kind == ASSET else book.manifest.get(identifier)
            reviewable = record.reviewable_draft()
            would_approve.append({"kind": item_kind, "id": identifier,
                                  "revision": reviewable.revision})
        return {"book_id": book_id, "dry_run": True, "approved": [],
                "would_approve": would_approve, "not_ready": not_ready, "failed": []}

    approved: list[dict] = []
    failed: list[dict] = []
    for item_kind, identifier in candidates:
        record = book.registry.get(identifier) if item_kind == ASSET else book.manifest.get(identifier)
        reviewable = record.reviewable_draft()
        if reviewable is None:
            continue
        try:
            approval = book.approve(item_kind, identifier, revision=reviewable.revision,
                                    by=by, note=note, autonomous=autonomous)
            approved.append({"kind": item_kind, "id": identifier, "revision": reviewable.revision,
                             "path": approval.path, "sha256": approval.sha256})
        except BookFactoryError as exc:
            failure = {"kind": item_kind, "id": identifier, "revision": reviewable.revision,
                      "error": exc.message}
            if exc.remedy:
                failure["remedy"] = exc.remedy
            failed.append(failure)

    task_module.sync_open_task(book)
    return {"book_id": book_id, "dry_run": False, "approved": approved,
            "not_ready": not_ready, "failed": failed}


def reject(book_id: str, identifier: str, *, kind: str = PAGE, revision: str | None = None,
           reason: str | None = None, by: str | None = None,
           root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    draft = book.reject(kind, identifier, revision=revision, reason=reason, by=by)
    task_module.sync_open_task(book)
    return {"kind": kind, "id": identifier, **draft.to_dict(with_dimensions=True)}


def revise(book_id: str, identifier: str, *, kind: str = PAGE, reason: str | None = None,
           by: str | None = None, root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    result = book.revise(kind, identifier, reason=reason, by=by)
    task_module.sync_open_task(book)
    return {"kind": kind, "id": identifier, **result}


# ----------------------------------------------------------------------
# Locks and stages
# ----------------------------------------------------------------------


LOCKS = {
    "concept": "lock_concept",
    "voice": "lock_voice",
    "manuscript": "lock_manuscript",
    "visual": "lock_visual",
}


def lock(book_id: str, what: str, *, version: str | None = None, by: str | None = None,
         note: str | None = None, autonomous: bool = False,
         root: str | Path | None = None) -> dict:
    if what not in LOCKS:
        raise ValidationError(f"Cannot lock {what!r}",
                              remedy="Lockable: " + ", ".join(LOCKS))
    book = Book.load(book_id, root)
    method = getattr(book, LOCKS[what])
    if what == "concept":
        method(by=by, note=note, autonomous=autonomous)
    else:
        method(version=version, by=by, note=note, autonomous=autonomous)
    task_module.sync_open_task(book)
    return status(book_id, root=root)


def advance(book_id: str, to: str | None = None, *, by: str | None = None,
            note: str | None = None, force: bool = False,
            root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    stage = book.advance(to, by=by, note=note, force=force)
    task_module.sync_open_task(book)
    return {"book_id": book_id, "stage": stage, "stage_label": stages.label(stage)}


def block(book_id: str, reason: str, *, needs: str | None = None,
          root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    book.block(reason, needs=needs)
    return status(book_id, root=root)


def unblock(book_id: str, *, root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    book.unblock()
    return status(book_id, root=root)


# ----------------------------------------------------------------------
# Validation, rendering, QA, assembly
# ----------------------------------------------------------------------


def validate(book_id: str, *, root: str | Path | None = None) -> dict:
    """Structural validation only - schemas, manifest integrity, checksums. Read-only."""
    book = Book.load(book_id, root)
    problems: list[str] = []
    problems.extend(f"page manifest: {p}" for p in book.manifest.problems())
    problems.extend(f"asset registry: {p}" for p in book.registry.problems())
    problems.extend(book.verify_approved())
    from bookfactory.core import cover
    problems.extend(cover.integrity_problems(book))

    for page in book.manifest:
        if page.spec:
            spec_path = book.paths.resolve(page.spec)
            if not spec_path.is_file():
                problems.append(f"{page.page_id}: spec file missing ({page.spec})")
            else:
                try:
                    book.read_page_spec(page.page_id)
                except Exception as exc:  # noqa: BLE001
                    problems.append(f"{page.page_id}: {exc}")
        for draft in page.drafts:
            path = book.paths.resolve(draft.path)
            if not path.is_file():
                problems.append(f"{page.page_id}: draft {draft.revision} missing ({draft.path})")

    for asset in book.registry:
        for draft in asset.drafts:
            path = book.paths.resolve(draft.path)
            if not path.is_file():
                problems.append(f"{asset.asset_id}: draft {draft.revision} missing ({draft.path})")

    return {
        "book_id": book_id,
        "ok": not problems,
        "problems": problems,
        "pages": len(book.manifest),
        "assets": len(book.registry),
    }


def relock(book_id: str, *, root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    from bookfactory.core import cover
    count = book.relock_approved() + cover.relock(book)
    return {"book_id": book_id, "relocked": count}


def render(book_id: str, *, page_id: str | None = None, backend: str | None = None,
           submit: bool = False, root: str | Path | None = None) -> dict:
    from bookfactory.core.errors import BookFactoryError
    from bookfactory.render.renderer import render_page

    book = Book.load(book_id, root)
    rendered: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []

    if page_id:
        # Single-page renders keep today's behaviour exactly: errors raise.
        path = render_page(book, page_id, backend=backend)
        entry = {"page_id": page_id, "render": book.paths.relative(path)}
        if submit:
            draft = book.submit(PAGE, page_id, path, source=f"renderer:{backend or 'default'}")
            entry["draft"] = draft.revision
            entry["sha256"] = draft.sha256
        rendered.append(entry)
    else:
        for page in list(book.manifest):
            target = page.page_id
            if not page.spec:
                skipped.append({"page_id": target, "reason": "no spec"})
                continue
            if submit and page.is_approved and not page.revision_open:
                skipped.append({"page_id": target, "reason": "approved"})
                continue
            try:
                path = render_page(book, target, backend=backend)
                entry = {"page_id": target, "render": book.paths.relative(path)}
                if submit:
                    draft = book.submit(PAGE, target, path, source=f"renderer:{backend or 'default'}")
                    entry["draft"] = draft.revision
                    entry["sha256"] = draft.sha256
                rendered.append(entry)
            except BookFactoryError as exc:
                failure = {"page_id": target, "error": exc.message}
                if exc.remedy:
                    failure["remedy"] = exc.remedy
                failed.append(failure)

    book.save()
    task_module.sync_open_task(book)
    return {"book_id": book_id, "rendered": rendered, "skipped": skipped, "failed": failed}


def render_reference(book_id: str, asset_id: str, spec: dict, *, dpi: int = 300,
                     backend: str | None = None, source: str | None = None,
                     root: str | Path | None = None) -> dict:
    """Typeset one reference-set sample page and submit it as a new draft of `asset_id`.

    A reference-set sample (a chapter opener, a checklist/diagnostic page, an
    editorial page, a palette sheet, ...) is needed before a book has a page
    plan, so it is rendered from an ordinary page spec that never joins the
    page manifest: it reserves no page id and nothing is written to pages/.
    `asset_id` must already be registered (`bookfactory asset add`) - this
    never registers one. The picture budget (AGENTS.md section 5a) does not
    apply: a reference is never a page picture.

    The rendered page is rasterised to PNG at `dpi` and submitted through the
    same path `bookfactory submit --kind asset` uses, so every measured check
    (min_pixels etc.) runs on it exactly as it would on any other draft.
    """
    import tempfile

    from bookfactory.render.renderer import render_reference_page

    book = Book.load(book_id, root)
    if book.registry.find(asset_id) is None:
        raise ValidationError(
            f"Asset '{asset_id}' is not registered",
            remedy=(f"Register it first: `bookfactory asset add {book_id} {asset_id} "
                    "--kind reference --reference-role <role>`"),
        )

    with tempfile.TemporaryDirectory(prefix="bookfactory-reference-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        page_type = spec.get("type") or "reference"
        pdf_path = render_reference_page(
            book, spec, destination=tmp_path / f"{page_type}.pdf", backend=backend)
        png_path = tmp_path / f"{asset_id}.png"
        _rasterize_to_png(pdf_path, png_path, dpi=dpi)
        draft = book.submit(ASSET, asset_id, png_path,
                            source=source or f"reference-render:{backend or 'default'}")

    task_module.sync_open_task(book)
    return {"book_id": book_id, "asset_id": asset_id, "page_type": page_type,
            **draft.to_dict(with_dimensions=True)}


def _rasterize_to_png(pdf_path: Path, png_path: Path, *, dpi: int) -> Path:
    import fitz

    with fitz.open(str(pdf_path)) as doc:
        doc[0].get_pixmap(dpi=dpi).save(str(png_path))
    return png_path


def qa(book_id: str, *, layers: list[str] | None = None,
       root: str | Path | None = None) -> dict:
    from bookfactory.qa.runner import run_qa

    book = Book.load(book_id, root)
    #: Writes the QA report (qa/reports/ and qa/latest.json) and nothing else.
    #: Later stages depend on it; the stage and next task it unlocks are picked
    #: up by `next`/`status` at once and recorded by the next mutating command.
    return run_qa(book, layers=layers)


def assemble(book_id: str, *, root: str | Path | None = None,
             destination: str | Path | None = None) -> dict:
    from bookfactory.assembly.assemble import assemble as do_assemble

    book = Book.load(book_id, root)
    record = do_assemble(book, destination=destination)
    task_module.sync_open_task(book)
    return record


def review(book_id: str, *, root: str | Path | None = None, **kwargs) -> dict:
    from bookfactory.assembly.review import generate_review

    book = Book.load(book_id, root)
    produced = generate_review(book, **kwargs)
    book.save()
    return {"book_id": book_id, "outputs": produced}


def preflight(book_id: str, *, root: str | Path | None = None) -> dict:
    from bookfactory.kdp.preflight import preflight as do_preflight

    book = Book.load(book_id, root)
    report = do_preflight(book)
    task_module.sync_open_task(book)
    return report


def produce(book_id: str, *, root: str | Path | None = None, max_steps: int = 50,
            dry_run: bool = False) -> dict:
    """Run the book's mechanical tasks (render, QA, assembly, preflight) until one
    needs a person. Approves page drafts only under a recorded policy that
    authorizes it; never pictures, locks, the cover or advances. See
    `core/produce.py`."""
    from bookfactory.core import produce as produce_loop

    return produce_loop.run(book_id, root=root, max_steps=max_steps, dry_run=dry_run)


def cover_build(book_id: str, *, submit: bool = False,
                root: str | Path | None = None) -> dict:
    from bookfactory.render import cover as cover_builder

    book = Book.load(book_id, root)
    result = cover_builder.build(book, submit=submit)
    task_module.sync_open_task(book)
    return result


def audit_history(book_id: str, *, limit: int | None = None, event: str | None = None,
                  root: str | Path | None = None) -> list[dict]:
    from bookfactory.core import audit

    book = Book.load(book_id, root)
    return audit.history(book.paths.audit_log, limit=limit, event=event)
