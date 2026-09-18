"""The page manifest.

This is the single authoritative list of what pages exist in the book, in what
order, and which file is the approved artefact for each one. Assembly reads
this and nothing else. If a page is not in the manifest it is not in the book.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory import SCHEMA_VERSION
from bookfactory.core import clock, ids, schema
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import read_json, write_json
from bookfactory.core.models import PageRecord


class PageManifest:
    def __init__(self, book_id: str, pages: list[PageRecord] | None = None,
                 *, front_matter_pages: int = 0, updated_at: str | None = None) -> None:
        self.book_id = book_id
        self.pages: list[PageRecord] = pages or []
        self.front_matter_pages = front_matter_pages
        self.updated_at = updated_at or clock.timestamp()

    # -- persistence ------------------------------------------------------
    @classmethod
    def empty(cls, book_id: str) -> "PageManifest":
        return cls(book_id)

    @classmethod
    def load(cls, path: str | Path) -> "PageManifest":
        data = read_json(path)
        schema.validate("page-manifest", data, context=str(path))
        return cls(
            book_id=data["book_id"],
            pages=[PageRecord.from_dict(p) for p in data.get("pages", [])],
            front_matter_pages=data.get("front_matter_pages", 0),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "book_id": self.book_id,
            "updated_at": self.updated_at,
            "front_matter_pages": self.front_matter_pages,
            "pages": [p.to_dict() for p in self.sorted_pages()],
        }

    def save(self, path: str | Path) -> Path:
        self.updated_at = clock.timestamp()
        data = self.to_dict()
        schema.validate("page-manifest", data, context=str(path))
        return write_json(path, data)

    # -- access -----------------------------------------------------------
    def sorted_pages(self) -> list[PageRecord]:
        return sorted(self.pages, key=lambda p: p.sequence)

    def get(self, page_id: str) -> PageRecord:
        page = self.find(page_id)
        if page is None:
            known = ", ".join(p.page_id for p in self.sorted_pages()[:10]) or "<none>"
            raise ValidationError(
                f"Page {page_id} is not in the page manifest",
                remedy=f"Known pages: {known}. Add it with `bookfactory plan`.",
            )
        return page

    def find(self, page_id: str) -> PageRecord | None:
        for page in self.pages:
            if page.page_id == page_id:
                return page
        return None

    def __len__(self) -> int:
        return len(self.pages)

    def __iter__(self):
        return iter(self.sorted_pages())

    # -- mutation ---------------------------------------------------------
    def add(self, page: PageRecord) -> PageRecord:
        if self.find(page.page_id):
            raise ValidationError(
                f"Page {page.page_id} is already in the manifest",
                remedy="Page ids are unique. Use a different sequence number.",
            )
        clash = [p for p in self.pages if p.sequence == page.sequence]
        if clash:
            raise ValidationError(
                f"Sequence {page.sequence} is already taken by {clash[0].page_id}",
                remedy="Two pages may not occupy the same position in the book.",
            )
        self.pages.append(page)
        return page

    def remove(self, page_id: str) -> None:
        page = self.get(page_id)
        if page.is_approved:
            raise ValidationError(
                f"Refusing to remove {page_id}: it has an approved artefact",
                remedy="Approved work is never silently discarded. Remove it by hand and commit the change deliberately.",
            )
        self.pages.remove(page)

    def renumber_printed(self, *, start_at: int = 1, front_matter: int | None = None) -> None:
        """Assign printed page numbers. Front matter carries no printed number."""
        if front_matter is not None:
            self.front_matter_pages = front_matter
        number = start_at
        for page in self.sorted_pages():
            if page.sequence <= self.front_matter_pages:
                page.printed_number = None
            else:
                page.printed_number = number
                number += 1

    # -- integrity --------------------------------------------------------
    def problems(self) -> list[str]:
        """Structural problems that make the manifest untrustworthy."""
        found: list[str] = []
        seen_ids: dict[str, int] = {}
        seen_seq: dict[int, str] = {}
        seen_paths: dict[str, str] = {}

        for page in self.sorted_pages():
            if page.page_id in seen_ids:
                found.append(f"duplicate page id {page.page_id}")
            seen_ids[page.page_id] = 1

            if page.sequence in seen_seq:
                found.append(
                    f"duplicate sequence {page.sequence}: {seen_seq[page.sequence]} and {page.page_id}"
                )
            seen_seq[page.sequence] = page.page_id

            if page.approved:
                path = page.approved.path
                if path in seen_paths:
                    found.append(
                        f"filename collision: {page.page_id} and {seen_paths[path]} both claim {path}"
                    )
                seen_paths[path] = page.page_id

        sequences = sorted(seen_seq)
        if sequences:
            expected = list(range(sequences[0], sequences[-1] + 1))
            missing = sorted(set(expected) - set(sequences))
            if missing:
                found.append(
                    "gaps in page sequence: " + ", ".join(str(m) for m in missing)
                )
            if sequences[0] != 1:
                found.append(f"page sequence starts at {sequences[0]}, expected 1")

        printed = [(p.sequence, p.printed_number) for p in self.sorted_pages()
                   if p.printed_number is not None]
        for (seq_a, num_a), (seq_b, num_b) in zip(printed, printed[1:]):
            if num_b != num_a + 1:
                found.append(
                    f"printed page numbers jump from {num_a} (seq {seq_a}) to {num_b} (seq {seq_b})"
                )
        return found

    # -- reporting --------------------------------------------------------
    def counts(self) -> dict:
        counts = {"planned": 0, "spec_ready": 0, "in_production": 0,
                  "draft_submitted": 0, "approved": 0, "rejected": 0}
        for page in self.pages:
            counts[page.status] = counts.get(page.status, 0) + 1
        counts["total"] = len(self.pages)
        counts["not_started"] = counts["planned"] + counts["spec_ready"]
        counts["in_revision"] = sum(1 for p in self.pages if p.revision_open)
        return counts

    def chapters(self) -> list[int]:
        return sorted({p.chapter for p in self.pages if p.chapter is not None})

    def next_sequence(self) -> int:
        return max((p.sequence for p in self.pages), default=0) + 1

    def new_page_id(self) -> str:
        return ids.page_id(self.next_sequence())
