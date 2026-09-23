"""The `produce` loop: run a book's routine tasks until one needs a person.

`bookfactory next` says what the single next task is. `produce` repeats
"read the next task, do it" - but only for these tasks, each of which already
has a deterministic command behind it:

    page_render  -> render the page from its spec and submit it as a draft
    approval     -> approve a PAGE draft, only under a recorded policy that
                    authorizes autonomous approval (see below)
    qa           -> run QA
    assembly     -> assemble the interior PDF
    preflight    -> run the interior KDP preflight

and only while the task's `mode` is `continue_automatically` (AGENTS.md 3a),
so it follows the book's recorded production policy without re-deriving it.

A page approval is the one decision it takes, and only when all of these
hold: the task is a page's own approval task, its `mode` is
`continue_automatically`, and `gates.autonomous_approval_authorized` passes -
that is, the operator recorded an `autonomous` or `visual_checkpoint` policy.
It approves exactly the page's current reviewable draft through the ordinary
`api.approve(..., autonomous=True)`, so every existing check applies and the
audit log records the approval as granted under that policy (AGENTS.md 3).
A `checkpointed` book stops at its first page approval.

It stops, with a plain reason, at the first task of any other kind: writing,
a picture, a picture's approval, the cover, a lock, an operator decision,
remediation, a blocked book, or a finished one. It never approves pictures or
the cover, never locks, advances, rejects, revises, changes a policy or a
picture budget, never batch-approves, and never passes `force` to anything -
those stay decisions (AGENTS.md 3 and 8).

Two guards keep it from looping: a step limit, and a no-progress stop when a
step leaves the same task next (for example a preflight that keeps failing).
A dry run only reads: it reports the first step it would take, or why it
would stop, and changes nothing.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import api, gates, production
from bookfactory.core.book import PAGE, Book
from bookfactory.core.errors import BookFactoryError, ValidationError

#: The only task types `produce` ever runs without a decision.
MECHANICAL_TYPES = ("page_render", "qa", "assembly", "preflight")

#: The name the audit log records for an approval `produce` makes.
APPROVER = "produce"

#: Codes for `stopped_because`.
COMPLETE = "complete"
WAIT_FOR_OPERATOR = production.WAIT_FOR_OPERATOR
REMEDIATE = production.REMEDIATE
BLOCKED = production.BLOCKED
NOT_MECHANICAL = "not_mechanical"
MAX_STEPS = "max_steps"
NO_PROGRESS = "no_progress"
ERROR = "error"
DRY_RUN = "dry_run"

STOP_REASONS = (COMPLETE, WAIT_FOR_OPERATOR, REMEDIATE, BLOCKED, NOT_MECHANICAL,
                MAX_STEPS, NO_PROGRESS, ERROR, DRY_RUN)

DEFAULT_MAX_STEPS = 50

#: What a task of each non-mechanical type needs, in plain words.
_NEEDS = {
    "authoring": "writing",
    "illustration": "a picture",
    "character_reference": "a picture",
    "layout_reference": "a picture",
    "approval": "an approval",
    "operator_decision": "an operator decision",
    "intake": "the operator's answers to the intake questions",
}


# ----------------------------------------------------------------------
# Deciding
# ----------------------------------------------------------------------


def _describe(task: dict) -> str:
    return f"'{task.get('summary')}' ({task.get('task_id')})"


def _mechanical_action(book_id: str, task: dict) -> str | None:
    """The command `produce` would run for this task, or None if it is not one of its jobs.

    The type alone is not enough: the cover's finalize step is typed
    `assembly` and the cover preflight `preflight`, and both belong to the
    cover's review, not to this loop. Only the interior's own QA, assembly
    and preflight tasks, and page renders, qualify.
    """
    kind = task.get("type")
    task_id = task.get("task_id")
    if kind == "page_render" and task.get("page_id"):
        return f"bookfactory render {book_id} --page {task['page_id']} --submit"
    if kind == "qa" and task_id == f"{book_id}-qa":
        return f"bookfactory qa {book_id}"
    if kind == "assembly" and task_id == f"{book_id}-assemble":
        return f"bookfactory assemble {book_id}"
    if kind == "preflight" and task_id == f"{book_id}-preflight":
        return f"bookfactory preflight {book_id}"
    return None


def _page_approval(book_id: str, task: dict,
                   root=None) -> tuple[dict | None, str | None]:
    """The page approval `produce` may make for this task, or why it may not.

    Returns `({page_id, revision, policy, action}, None)` when every condition
    holds, else `(None, reason)`. Assumes the caller has already checked that
    the task's `mode` is `continue_automatically`. Only reads the book.
    """
    page_id = task.get("page_id")
    if task.get("asset_id"):
        return None, "approving a picture stays with the operator"
    if (task.get("gate") == "cover_visual_checkpoint"
            or task.get("task_id") == f"{book_id}-cover-approval"):
        return None, "approving the cover stays with the operator"
    if not page_id or task.get("gate") is not None \
            or task.get("task_id") != f"{book_id}-{page_id}-approve":
        return None, "only a page's own approval task can be approved by produce"

    book = Book.load(book_id, root)
    authorized = gates.autonomous_approval_authorized(book)
    if not authorized.ok:
        return None, ("the book's recorded production policy does not authorize autonomous "
                      "approval (" + "; ".join(authorized.reasons) + ")")
    page = book.manifest.get(page_id)
    if page is None:
        return None, f"page {page_id} is not in the manifest"
    if page.is_approved and not page.revision_open:
        return None, f"page {page_id} is already approved"
    draft = page.reviewable_draft()
    latest = page.latest_draft()
    if draft is None or latest is None or draft.revision != latest.revision:
        return None, (f"page {page_id} has no reviewable draft matching the task, so there is "
                      "nothing produce could safely approve")
    policy = book.state.production_policy.mode
    return {"page_id": page_id, "revision": draft.revision, "policy": policy,
            "action": (f"bookfactory approve {book_id} {page_id} --kind page "
                       f"--draft {draft.revision} --by {APPROVER} --autonomous")}, None


def _action_for(book_id: str, task: dict, root=None) -> str | None:
    """The command `produce` would run for a task it may take, else None."""
    if task.get("type") == "approval":
        approval, _ = _page_approval(book_id, task, root)
        return approval["action"] if approval else None
    return _mechanical_action(book_id, task)


def _stop_for(book_id: str, task: dict | None, root=None) -> tuple[str, str] | None:
    """(code, message) if `produce` must stop before this task, else None."""
    if task is None:
        return COMPLETE, "Nothing left to do: the book has no next task."
    mode = task.get("mode")
    if mode != production.CONTINUE_AUTOMATICALLY:
        if mode == production.BLOCKED:
            return BLOCKED, (f"Stopped: the book is blocked; the next task is {_describe(task)} "
                             "and needs the operator.")
        if mode == production.REMEDIATE:
            return REMEDIATE, (f"Stopped: the next task, {_describe(task)}, must redo work that "
                               "failed a measured check, which produce does not do.")
        if mode == production.WAIT_FOR_OPERATOR:
            return WAIT_FOR_OPERATOR, (f"Stopped: the next task, {_describe(task)}, waits for "
                                       "the operator's decision.")
        return str(mode), f"Stopped: the next task, {_describe(task)}, has mode {mode!r}."
    if task.get("type") == "approval":
        _, reason = _page_approval(book_id, task, root)
        if reason is not None:
            return NOT_MECHANICAL, (f"Stopped: the next task, {_describe(task)}, needs an "
                                    f"approval that produce does not make: {reason}. Pictures "
                                    "and the cover always stay with the operator.")
        return None
    if _mechanical_action(book_id, task) is None:
        kind = task.get("type")
        needs = _NEEDS.get(kind)
        if needs is None and kind in MECHANICAL_TYPES:
            needs = "a cover step"
        needs = needs or f"a '{kind}' task"
        return NOT_MECHANICAL, (f"Stopped: the next task, {_describe(task)}, needs {needs}, "
                                "which produce does not do.")
    return None


# ----------------------------------------------------------------------
# Doing
# ----------------------------------------------------------------------


def _run_step(book_id: str, task: dict, root) -> str:
    """Run exactly the one existing API call for the task; return a summary."""
    kind = task["type"]
    if kind == "approval":
        approval, reason = _page_approval(book_id, task, root)
        if approval is None:  # pragma: no cover - _stop_for already refused it
            raise AssertionError(f"produce may not approve {task.get('task_id')}: {reason}")
        #: The ordinary single approval: every existing check applies, and the
        #: audit log records it as granted under the recorded policy. Never force.
        api.approve(book_id, approval["page_id"], kind=PAGE, revision=approval["revision"],
                    by=APPROVER, autonomous=True, root=root)
        return (f"approved {approval['page_id']} draft {approval['revision']} under the "
                f"recorded {approval['policy']} policy")
    if kind == "page_render":
        page_id = task["page_id"]
        result = api.render(book_id, page_id=page_id, submit=True, root=root)
        entry = result["rendered"][0]
        return f"rendered {page_id} and submitted it as draft {entry.get('draft')}"
    if kind == "qa":
        report = api.qa(book_id, root=root)
        return f"QA {report.get('summary', {}).get('status')}"
    if kind == "assembly":
        record = api.assemble(book_id, root=root)
        return f"assembled {record.get('output')} ({record.get('page_count')} pages)"
    if kind == "preflight":
        report = api.preflight(book_id, root=root)
        return (f"preflight {report.get('status')} ({report.get('failures', 0)} failures, "
                f"{report.get('warnings', 0)} warnings)")
    raise AssertionError(f"produce has no step for task type {kind!r}")  # pragma: no cover


# ----------------------------------------------------------------------
# The loop
# ----------------------------------------------------------------------


def run(book_id: str, *, root: str | Path | None = None, max_steps: int = DEFAULT_MAX_STEPS,
        dry_run: bool = False) -> dict:
    """Run the book's routine tasks until one needs a person, then say why it stopped.

    Returns a JSON-friendly dict: `book_id`, `dry_run`, `steps` (each
    `{task_id, type, action, result}`), `stopped_because` (one of
    `STOP_REASONS`), `message` (one plain sentence) and `next_task` (the task
    it stopped on, or None).
    """
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
        raise ValidationError(f"max_steps must be a whole number of at least 1, not {max_steps!r}",
                              remedy="Pass max_steps=1 or more (CLI: --max-steps N).")

    steps: list[dict] = []
    last_run: str | None = None

    def finish(code: str, message: str, task: dict | None) -> dict:
        return {"book_id": book_id, "dry_run": dry_run, "steps": steps,
                "stopped_because": code, "message": message, "next_task": task}

    while True:
        #: Read-only, exactly as `bookfactory next` reads it.
        task = api.next_task(book_id, root=root)

        stop = _stop_for(book_id, task, root)
        if stop is not None:
            return finish(*stop, task)

        action = _action_for(book_id, task, root)
        if task["task_id"] == last_run:
            return finish(NO_PROGRESS, (
                f"Stopped: after running {task['task_id']} ({steps[-1]['result']}), the same "
                "task is still next, so running it again would not help."), task)
        if dry_run:
            return finish(DRY_RUN, (f"Dry run: the first step would be {_describe(task)}: "
                                    f"{action}. Nothing was changed."), task)
        if len(steps) >= max_steps:
            return finish(MAX_STEPS, (f"Stopped after {len(steps)} steps (the step limit); "
                                      f"the next task is {_describe(task)}."), task)

        try:
            result = _run_step(book_id, task, root)
        except BookFactoryError as exc:
            message = f"Stopped: {task['task_id']} failed: {exc.message}"
            if exc.remedy:
                message += f" Remedy: {exc.remedy}"
            steps.append({"task_id": task["task_id"], "type": task["type"], "action": action,
                          "result": f"error: {exc.message}"})
            outcome = finish(ERROR, message, task)
            outcome["error"] = exc.to_dict()
            return outcome

        steps.append({"task_id": task["task_id"], "type": task["type"], "action": action,
                      "result": result})
        last_run = task["task_id"]


__all__ = ["run", "MECHANICAL_TYPES", "STOP_REASONS", "DEFAULT_MAX_STEPS"]
