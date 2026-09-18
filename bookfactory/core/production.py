"""The autonomous production-loop contract.

`bookfactory next` already derives the single next task from repository state.
This module answers the question a driving agent asks after that: *may I just
do this and keep going, or does a human need to decide?*

Five states, deliberately not a workflow engine:

    CONTINUE_AUTOMATICALLY  - do the task, then call `next` again.
    WAIT_FOR_OPERATOR       - genuine judgement is required; stop and ask.
    REMEDIATE               - a prior attempt failed a measurable, fixable
                              requirement; produce a corrected version.
    BLOCKED                 - the book is explicitly blocked.
    COMPLETE                - there is no next task; the book is finished.

The state is derived from the book's recorded `production_policy` and the task
itself - never from silence, and never by re-deriving the whole book from
scratch each time (that is what `bookfactory.core.tasks` already does).
"""

from __future__ import annotations

from bookfactory.core.models import IntakeState, ProductionPolicy  # noqa: F401  (re-export for callers)

CONTINUE_AUTOMATICALLY = "continue_automatically"
WAIT_FOR_OPERATOR = "wait_for_operator"
REMEDIATE = "remediate"
BLOCKED = "blocked"
COMPLETE = "complete"

MODES = (CONTINUE_AUTOMATICALLY, WAIT_FOR_OPERATOR, REMEDIATE, BLOCKED, COMPLETE)

#: How many times an asset may fail a hard constraint before it stops being a
#: "produce a corrected version" problem and becomes an operator problem.
RETRY_LIMIT = 3

#: Gates an operator explicitly authorised skipping past, when the policy says so.
_MAJOR_GATES = ("concept_lock", "voice_lock", "manuscript_lock", "release_ready")


def policy_from_choice(choice: str) -> ProductionPolicy:
    """The `ProductionPolicy` implied by the intake questionnaire's Q12 answer."""
    choice = (choice or "").strip().lower()
    if choice == "autonomous":
        return ProductionPolicy(
            mode="autonomous", operator_authorized=True, visual_checkpoint=False,
            major_gate_checkpoints=False, stop_on_soft_qa_failure=False,
            stop_on_hard_failure=True,
        )
    if choice == "visual_checkpoint":
        return ProductionPolicy(
            mode="visual_checkpoint", operator_authorized=True, visual_checkpoint=True,
            major_gate_checkpoints=False, stop_on_soft_qa_failure=False,
            stop_on_hard_failure=True,
        )
    if choice == "checkpointed":
        return ProductionPolicy(
            mode="checkpointed", operator_authorized=False, visual_checkpoint=True,
            major_gate_checkpoints=True, stop_on_soft_qa_failure=True,
            stop_on_hard_failure=True,
        )
    from bookfactory.core.errors import ValidationError

    raise ValidationError(
        f"Unknown production policy choice {choice!r}",
        remedy="Choose one of: autonomous, visual_checkpoint, checkpointed.",
    )


def is_autonomous(policy: ProductionPolicy) -> bool:
    """May normal production decisions proceed without asking the operator?"""
    return bool(policy.operator_authorized) and policy.mode in ("autonomous", "visual_checkpoint")


def _latest_qa_status(book) -> str | None:
    if not book.paths.qa_latest.is_file():
        return None
    from bookfactory.core.jsonio import read_json

    return read_json(book.paths.qa_latest).get("summary", {}).get("status")


def compute_mode(book, task) -> str:
    """The continuation state for `task`, given this book's recorded policy."""
    if task is None:
        return COMPLETE
    if book.state.blocked:
        return BLOCKED

    policy = book.state.production_policy

    if task.gate == "intake":
        #: Only the operator knows the answers. There is no policy yet to
        #: authorise skipping this - the policy itself comes out of it.
        return WAIT_FOR_OPERATOR

    if task.remediation:
        if task.retry_count >= RETRY_LIMIT:
            return WAIT_FOR_OPERATOR
        return REMEDIATE

    if task.task_id.endswith("-blocked"):
        return WAIT_FOR_OPERATOR

    if task.gate == "visual_lock" and policy.visual_checkpoint:
        return WAIT_FOR_OPERATOR
    if task.gate in _MAJOR_GATES and policy.major_gate_checkpoints:
        return WAIT_FOR_OPERATOR

    if task.type in ("operator_decision", "approval"):
        return CONTINUE_AUTOMATICALLY if is_autonomous(policy) else WAIT_FOR_OPERATOR

    if task.type in ("assembly", "preflight") and policy.stop_on_soft_qa_failure:
        if _latest_qa_status(book) == "warn":
            return WAIT_FOR_OPERATOR

    return CONTINUE_AUTOMATICALLY


__all__ = [
    "CONTINUE_AUTOMATICALLY", "WAIT_FOR_OPERATOR", "REMEDIATE", "BLOCKED", "COMPLETE", "MODES",
    "RETRY_LIMIT", "policy_from_choice", "is_autonomous", "compute_mode",
]
