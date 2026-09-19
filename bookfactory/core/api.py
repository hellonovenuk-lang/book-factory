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
    "approve", "reject", "revise",
    "lock", "advance", "validate", "render", "qa", "assemble", "review", "preflight",
    "audit_history", "relock",
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


def create_book(title: str, **kwargs) -> dict:
    root = kwargs.pop("root", None)
    book = Book.create(title, root=root, **kwargs)
    task_module.sync_open_task(book)
    return {
        "book_id": book.state.book_id,
        "path": str(book.paths.root),
        "stage": book.state.stage,
        "next_action": book.state.next_action,
        "created_files": sorted(
            str(p.relative_to(book.paths.root))
            for p in book.paths.root.rglob("*") if p.is_file()
        ),
    }


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
    book = Book.load(book_id, root)
    summary = book.summary()
    summary["gates"] = _gate_summary(book)
    summary["approved_integrity"] = book.verify_approved()
    summary["qa"] = _qa_summary(book)
    summary["outputs"] = {
        "interior_pdf": (book.paths.relative(book.paths.interior_pdf)
                         if book.paths.interior_pdf.is_file() else None),
        "preflight": (book.latest_preflight() or {}).get("status"),
    }
    from bookfactory.core import cover, gates
    summary["readiness"] = cover.readiness(book)
    summary["outputs"]["cover_pdf"] = "output/cover.pdf" if (book.paths.root / "output/cover.pdf").is_file() else None
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


def next_task(book_id: str, *, root: str | Path | None = None, persist: bool = True) -> dict | None:
    book = Book.load(book_id, root)
    task = task_module.sync_open_task(book) if persist else task_module.next_task(book)
    if task is None:
        return None
    book.save()
    return task.to_dict()


def get_task(book_id: str, task_id: str | None = None, *,
             root: str | Path | None = None) -> dict | None:
    book = Book.load(book_id, root)
    if task_id is None:
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
    book = Book.load(book_id, root)
    added = []
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
            book.write_page_spec(record.page_id, entry["spec"])
    if renumber:
        book.manifest.renumber_printed(front_matter=front_matter_pages)
    book.state.page_plan.page_count = len(book.manifest)
    book.log("page_planned", added=added, total=len(book.manifest))
    book.save()
    task_module.sync_open_task(book)
    return {"added": added, "total": len(book.manifest),
            "problems": book.manifest.problems()}


def write_page_spec(book_id: str, page_id: str, spec: dict, *,
                    root: str | Path | None = None) -> dict:
    book = Book.load(book_id, root)
    path = book.write_page_spec(page_id, spec)
    book.save()
    task_module.sync_open_task(book)
    return {"page_id": page_id, "spec": book.paths.relative(path)}


def register_asset(book_id: str, asset_id: str, *, root: str | Path | None = None,
                   **kwargs) -> dict:
    book = Book.load(book_id, root)
    record = book.register_asset(asset_id, **kwargs)
    book.save()
    task_module.sync_open_task(book)
    return record.to_dict()


def submit_intake(book_id: str, answers: dict, *, root: str | Path | None = None) -> dict:
    """Persist the operator's one-time answers to the intake questionnaire.

    This is the only way `book.json`'s `intake` and `production_policy` get
    set. A fresh session never needs to ask again - it reads
    `brief/intake.json` or `book.json`'s `intake` block instead.
    """
    from bookfactory.core import intake as intake_module, production

    problems = intake_module.validate_answers(answers)
    if problems:
        raise ValidationError(
            "Questionnaire answers are incomplete or invalid",
            problems=problems,
            remedy="Fix the listed answers and submit again.",
        )
    book = Book.load(book_id, root)
    from bookfactory.core import clock

    book.state.intake.completed = True
    book.state.intake.completed_at = clock.timestamp()
    book.state.intake.answers = dict(answers)
    policy = production.policy_from_choice(answers["production_policy"])
    policy.authorized_at = clock.timestamp()
    policy.source = "intake_questionnaire"
    book.state.production_policy = policy
    write_json(book.paths.brief_dir / "intake.json", {
        "answers": book.state.intake.answers,
        "completed_at": book.state.intake.completed_at,
    })
    book.log("intake_submitted", production_policy=policy.mode,
             operator_authorized=policy.operator_authorized)
    book.save()
    task_module.sync_open_task(book)
    return status(book_id, root=root)


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
         note: str | None = None, root: str | Path | None = None) -> dict:
    if what not in LOCKS:
        raise ValidationError(f"Cannot lock {what!r}",
                              remedy="Lockable: " + ", ".join(LOCKS))
    book = Book.load(book_id, root)
    method = getattr(book, LOCKS[what])
    if what == "concept":
        method(by=by, note=note)
    else:
        method(version=version, by=by, note=note)
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
    """Structural validation only - schemas, manifest integrity, checksums."""
    book = Book.load(book_id, root)
    problems: list[str] = []
    problems.extend(f"page manifest: {p}" for p in book.manifest.problems())
    problems.extend(f"asset registry: {p}" for p in book.registry.problems())
    problems.extend(book.verify_approved())

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
    count = book.relock_approved()
    return {"book_id": book_id, "relocked": count}


def render(book_id: str, *, page_id: str | None = None, backend: str | None = None,
           submit: bool = False, root: str | Path | None = None) -> dict:
    from bookfactory.render.renderer import render_all, render_page

    book = Book.load(book_id, root)
    rendered: list[dict] = []
    targets = [page_id] if page_id else [p.page_id for p in book.manifest]
    for target in targets:
        path = render_page(book, target, backend=backend)
        entry = {"page_id": target, "render": book.paths.relative(path)}
        if submit:
            draft = book.submit(PAGE, target, path, source=f"renderer:{backend or 'default'}")
            entry["draft"] = draft.revision
            entry["sha256"] = draft.sha256
        rendered.append(entry)
    if not page_id and not submit:
        render_all(book, backend=backend)
    book.save()
    task_module.sync_open_task(book)
    return {"book_id": book_id, "rendered": rendered}


def qa(book_id: str, *, layers: list[str] | None = None,
       root: str | Path | None = None) -> dict:
    from bookfactory.qa.runner import run_qa

    book = Book.load(book_id, root)
    report = run_qa(book, layers=layers)
    task_module.sync_open_task(book)
    return report


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


def audit_history(book_id: str, *, limit: int | None = None, event: str | None = None,
                  root: str | Path | None = None) -> list[dict]:
    from bookfactory.core import audit

    book = Book.load(book_id, root)
    return audit.history(book.paths.audit_log, limit=limit, event=event)
