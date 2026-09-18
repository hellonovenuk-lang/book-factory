"""Canonical on-disk layout for a book project.

Everything in Book Factory addresses files through this object. Nothing builds
paths by string concatenation elsewhere, so the layout can be reasoned about in
one place and an agent can be told exactly where things live.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BOOKS_DIRNAME = "books"


def repo_root(start: str | Path | None = None) -> Path:
    """Locate the Book Factory repository root.

    Honours BOOKFACTORY_ROOT, otherwise walks upwards looking for a `books/`
    directory next to a `bookfactory/` package or a `.git` directory.
    """
    override = os.environ.get("BOOKFACTORY_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    current = Path(start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / DEFAULT_BOOKS_DIRNAME).is_dir() and (
            (candidate / "bookfactory").is_dir() or (candidate / ".git").is_dir()
        ):
            return candidate
    return current


def books_dir(root: str | Path | None = None) -> Path:
    return Path(root or repo_root()) / DEFAULT_BOOKS_DIRNAME


@dataclass(frozen=True)
class BookPaths:
    """Every canonical path for one book."""

    book_id: str
    root: Path

    @classmethod
    def for_book(cls, book_id: str, root: str | Path | None = None) -> "BookPaths":
        return cls(book_id=book_id, root=books_dir(root) / book_id)

    # --- top level -------------------------------------------------------
    @property
    def state_file(self) -> Path:
        return self.root / "book.json"

    @property
    def audit_log(self) -> Path:
        return self.root / "audit.jsonl"

    @property
    def readme(self) -> Path:
        return self.root / "README.md"

    # --- brief / concept -------------------------------------------------
    @property
    def brief_dir(self) -> Path:
        return self.root / "brief"

    @property
    def brief_file(self) -> Path:
        return self.brief_dir / "brief.md"

    @property
    def concept_file(self) -> Path:
        return self.brief_dir / "concept.md"

    @property
    def audience_file(self) -> Path:
        return self.brief_dir / "audience.md"

    @property
    def outline_file(self) -> Path:
        return self.root / "manuscript" / "outline.md"

    # --- manuscript ------------------------------------------------------
    @property
    def manuscript_dir(self) -> Path:
        return self.root / "manuscript"

    @property
    def manuscript_file(self) -> Path:
        return self.manuscript_dir / "manuscript.md"

    @property
    def writing_sample_file(self) -> Path:
        return self.manuscript_dir / "writing-sample.md"

    @property
    def manuscript_versions_dir(self) -> Path:
        return self.manuscript_dir / "versions"

    def manuscript_version_file(self, version: str) -> Path:
        return self.manuscript_versions_dir / f"manuscript-{version}.md"

    # --- style -----------------------------------------------------------
    @property
    def style_dir(self) -> Path:
        return self.root / "style"

    @property
    def visual_bible(self) -> Path:
        return self.style_dir / "visual-bible.md"

    @property
    def voice_bible(self) -> Path:
        return self.style_dir / "voice-bible.md"

    @property
    def design_tokens(self) -> Path:
        return self.style_dir / "design-tokens.json"

    @property
    def reference_set(self) -> Path:
        return self.style_dir / "reference-set.json"

    @property
    def references_dir(self) -> Path:
        return self.style_dir / "references"

    @property
    def fonts_dir(self) -> Path:
        return self.style_dir / "fonts"

    # --- pages -----------------------------------------------------------
    @property
    def pages_dir(self) -> Path:
        return self.root / "pages"

    @property
    def manifest_file(self) -> Path:
        return self.pages_dir / "manifest.json"

    @property
    def specs_dir(self) -> Path:
        return self.pages_dir / "specs"

    def spec_file(self, page_id: str) -> Path:
        return self.specs_dir / f"{page_id}.json"

    @property
    def page_drafts_dir(self) -> Path:
        return self.pages_dir / "drafts"

    @property
    def page_approved_dir(self) -> Path:
        return self.pages_dir / "approved"

    @property
    def page_history_dir(self) -> Path:
        return self.pages_dir / "approved" / "_history"

    @property
    def renders_dir(self) -> Path:
        return self.pages_dir / "renders"

    # --- illustration assets --------------------------------------------
    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def asset_registry(self) -> Path:
        return self.assets_dir / "registry.json"

    @property
    def asset_drafts_dir(self) -> Path:
        return self.assets_dir / "drafts"

    @property
    def asset_approved_dir(self) -> Path:
        return self.assets_dir / "approved"

    @property
    def asset_history_dir(self) -> Path:
        return self.assets_dir / "approved" / "_history"

    # --- tasks / qa / output ---------------------------------------------
    @property
    def tasks_dir(self) -> Path:
        return self.root / "tasks"

    @property
    def open_tasks_dir(self) -> Path:
        return self.tasks_dir / "open"

    @property
    def done_tasks_dir(self) -> Path:
        return self.tasks_dir / "done"

    @property
    def qa_dir(self) -> Path:
        return self.root / "qa"

    @property
    def qa_reports_dir(self) -> Path:
        return self.qa_dir / "reports"

    @property
    def qa_latest(self) -> Path:
        return self.qa_dir / "latest.json"

    @property
    def output_dir(self) -> Path:
        return self.root / "output"

    @property
    def interior_pdf(self) -> Path:
        return self.output_dir / "interior.pdf"

    @property
    def review_dir(self) -> Path:
        return self.output_dir / "review"

    @property
    def preflight_report(self) -> Path:
        return self.output_dir / "kdp-preflight.json"

    @property
    def tmp_dir(self) -> Path:
        return self.root / ".tmp"

    # --- helpers ----------------------------------------------------------
    def exists(self) -> bool:
        return self.state_file.is_file()

    def relative(self, path: str | Path) -> str:
        """Path relative to the book root, used in every state file so that
        state is portable between machines."""
        return str(Path(path).resolve().relative_to(self.root.resolve()))

    def resolve(self, relative_path: str) -> Path:
        return self.root / relative_path

    ALL_DIRS = (
        "brief", "manuscript", "manuscript/versions", "style", "style/references",
        "style/references/characters", "style/references/layouts", "style/references/pages",
        "style/fonts", "pages", "pages/specs", "pages/drafts", "pages/approved",
        "pages/approved/_history", "pages/renders", "assets", "assets/drafts",
        "assets/approved", "assets/approved/_history", "tasks", "tasks/open",
        "tasks/done", "qa", "qa/reports", "output", "output/review",
    )

    def create_skeleton(self) -> None:
        for rel in self.ALL_DIRS:
            (self.root / rel).mkdir(parents=True, exist_ok=True)
