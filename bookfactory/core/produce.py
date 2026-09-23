"""The `produce` loop: run a book's mechanical tasks until one needs a person.

`bookfactory next` says what the single next task is. `produce` repeats
"read the next task, do it" - but only for the tasks that are purely
mechanical and already have a deterministic command behind them:

    page_render  -> render the page from its spec and submit it as a draft
    qa           -> run QA
    assembly     -> assemble the interior PDF
    preflight    -> run the interior KDP preflight

and only while the task's `mode` is `continue_automatically` (AGENTS.md 3a),
so it follows the book's recorded production policy without re-deriving it.

It stops, with a plain reason, at the first task of any other kind: writing,
a picture, an approval, a lock, an operator decision, remediation, a blocked
book, or a finished one. It never approves, locks, advances, rejects,
revises, changes a policy or a picture budget, and never passes `force` or
`autonomous` to anything - those stay decisions (AGENTS.md 3 and 8).

Two guards keep it from looping: a step limit, and a no-progress stop when a
step leaves the same task next (for example a preflight that keeps failing).
A dry run only reads: it reports the first step it would take, or why it
would stop, and changes nothing.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import api, production
from bookfactory.core.errors import BookFactoryError, ValidationError

#: The only task types `produce` ever runs.
MECHANICAL_TYPES = ("page_render", "qa", "assembly", "preflight")

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


def _stop_for(book_id: str, task: dict | None) -> tuple[str, str] | None:
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
    """Run exactly the one existing API call for a mechanical task; return a summary."""
    kind = task["type"]
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
    """Run the book's mechanical tasks until one needs a person, then say why it stopped.

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

        stop = _stop_for(book_id, task)
        if stop is not None:
            return finish(*stop, task)

        action = _mechanical_action(book_id, task)
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
