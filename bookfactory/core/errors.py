"""Error types.

Book Factory fails loudly. Every error carries a human-readable message and,
where possible, the exact remedy. Nothing guesses.
"""

from __future__ import annotations


class BookFactoryError(Exception):
    """Base class for every Book Factory failure."""

    exit_code = 1

    def __init__(self, message: str, *, remedy: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.remedy = remedy

    def to_dict(self) -> dict:
        return {
            "error": type(self).__name__,
            "message": self.message,
            "remedy": self.remedy,
        }


class BookNotFound(BookFactoryError):
    exit_code = 4


class BookAlreadyExists(BookFactoryError):
    exit_code = 4


class ValidationError(BookFactoryError):
    """State on disk does not match its schema or internal invariants."""

    exit_code = 5

    def __init__(self, message: str, *, problems: list[str] | None = None,
                 remedy: str | None = None) -> None:
        super().__init__(message, remedy=remedy)
        self.problems = problems or []

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["problems"] = self.problems
        return data


class GateBlocked(BookFactoryError):
    """A production gate refused to open. Always explains exactly why."""

    exit_code = 6

    def __init__(self, gate: str, reasons: list[str], *, remedy: str | None = None) -> None:
        message = f"Gate '{gate}' is blocked:\n  - " + "\n  - ".join(reasons)
        super().__init__(message, remedy=remedy)
        self.gate = gate
        self.reasons = reasons

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["gate"] = self.gate
        data["reasons"] = self.reasons
        return data


class ImmutableAssetError(BookFactoryError):
    """Someone tried to mutate an approved artefact."""

    exit_code = 7


class ChecksumMismatch(BookFactoryError):
    """An approved artefact no longer matches its recorded SHA-256."""

    exit_code = 7

    def __init__(self, path: str, expected: str, actual: str) -> None:
        super().__init__(
            f"Checksum mismatch for {path}\n"
            f"  expected sha256: {expected}\n"
            f"  actual   sha256: {actual}",
            remedy=(
                "The approved artefact has been modified outside Book Factory. "
                "Restore it from git history, or run "
                "`bookfactory revise <book> <id>` to open a proper revision."
            ),
        )
        self.path = path
        self.expected = expected
        self.actual = actual


class RenderError(BookFactoryError):
    exit_code = 8


class AssemblyError(BookFactoryError):
    exit_code = 9


class QAFailure(BookFactoryError):
    exit_code = 10


class PreflightFailure(BookFactoryError):
    exit_code = 11
