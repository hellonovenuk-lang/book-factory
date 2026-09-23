"""Series presets: start a new book from an earlier book's locked voice and look.

See `PLAN.md`, "Phase 6: Series presets", for the exact command contract this
implements. This module never approves or locks anything on the operator's
behalf (`AGENTS.md` section 3): it copies locked style material byte for byte
and submits the source's approved reference art into the new book as drafts
that record where they came from. The new book's own production policy and
`next` decide who approves those drafts and locks its voice and visual style.
"""

from __future__ import annotations

import shutil

from bookfactory.core import checksums
from bookfactory.core.errors import ValidationError

#: `BookPaths` attribute names for the files copied byte for byte from the
#: source book. Anything missing on the source is skipped, not an error - an
#: older source book may predate one of these files.
STYLE_FILE_ATTRS = (
    "voice_bible",
    "writing_sample_file",
    "visual_bible",
    "design_tokens",
    "reference_set",
)


def check_source(source) -> None:
    """Refuse a book that is not ready to found a series.

    Both voice and visual style must be locked, and every required reference
    must already have approved artwork - the preset copies that approved file,
    not a draft. Call this *before* the new book is created, so a refusal
    leaves nothing behind.
    """
    problems = []
    if not source.state.style.voice_locked:
        problems.append("its voice is not locked")
    if not source.state.style.visual_locked:
        problems.append("its visual style is not locked")
    if problems:
        raise ValidationError(
            f"'{source.state.book_id}' cannot be used as a series source: "
            + " and ".join(problems),
            remedy=(
                f"Lock them on '{source.state.book_id}' first: "
                f"`bookfactory lock {source.state.book_id} voice` and "
                f"`bookfactory lock {source.state.book_id} visual`."
            ),
        )
    unapproved = []
    for asset_id in source.required_reference_ids():
        asset = source.registry.find(asset_id)
        if asset is None or not asset.is_approved:
            unapproved.append(asset_id)
    if unapproved:
        raise ValidationError(
            f"'{source.state.book_id}' has required references with no approved artwork: "
            + ", ".join(unapproved),
            remedy=(
                "Approve every required reference on the source book before using it "
                "as a series preset."
            ),
        )


def _copy_style_files(book, source) -> tuple[list[dict], list[str]]:
    copied: list[dict] = []
    skipped: list[str] = []
    for attr in STYLE_FILE_ATTRS:
        src_path = getattr(source.paths, attr)
        dest_path = getattr(book.paths, attr)
        if not src_path.is_file():
            skipped.append(book.paths.relative(dest_path))
            continue
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        copied.append({"path": book.paths.relative(dest_path),
                       "sha256": checksums.sha256_file(dest_path)})
    return copied, skipped


def _copy_cover_design(book, source) -> list[dict]:
    """Copy the source's cover `design` block, including any font files it names."""
    from bookfactory.core import cover

    source_data = cover.load(source)
    design = source_data.get("design")
    if not design:
        return []
    new_design = dict(design)
    copied: list[dict] = []
    for field in ("title_font", "body_font"):
        rel = new_design.get(field)
        if not rel:
            continue
        src_font = (source.paths.root / rel).resolve()
        if not src_font.is_relative_to(source.paths.root.resolve()):
            raise ValidationError(
                f"Series source's cover.json design.{field} points outside the book: {rel}",
                remedy="Fix the source book's cover.json before using it as a series source.",
            )
        if not src_font.is_file():
            #: Recorded but not usable - drop it rather than copy a design
            #: block that points at nothing.
            new_design.pop(field, None)
            continue
        dest_font = book.paths.root / rel
        dest_font.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_font, dest_font)
        copied.append({"path": book.paths.relative(dest_font),
                       "sha256": checksums.sha256_file(dest_font)})
    cover_data = cover.load(book)
    cover_data["design"] = new_design
    cover.save(book, cover_data)
    return copied


def _copy_references(book, source) -> list[dict]:
    """Register each required reference in `book` and submit the source's
    approved file as a draft recording its provenance. Never approves it."""
    from bookfactory.core.book import ASSET

    results: list[dict] = []
    for asset_id in source.required_reference_ids():
        asset = source.registry.find(asset_id)
        if asset is None or not asset.is_approved:
            # check_source already refused this; defensive only.
            continue
        book.register_asset(
            asset_id,
            kind=asset.kind,
            title=asset.title,
            description=asset.description,
            characters=list(asset.characters),
            references=list(asset.references),
            reference_role=asset.reference_role,
        )
        approved_path = source.paths.resolve(asset.approved.path)
        checksums.verify(approved_path, asset.approved.sha256)
        draft = book.submit(
            ASSET, asset_id, approved_path,
            source=f"series:{source.state.book_id}",
            note=(f"From {source.state.book_id} approved revision "
                  f"{asset.approved.revision} (sha256 {asset.approved.sha256})"),
        )
        results.append({
            "asset_id": asset_id,
            "source_revision": asset.approved.revision,
            "source_sha256": asset.approved.sha256,
            "draft": draft.revision,
        })
    return results


def apply_preset(book, source) -> dict:
    """Copy `source`'s locked style into the freshly created `book`.

    Copies the voice bible and writing sample, the visual bible, design
    tokens and reference set, and the cover `design` block with any font
    files it names. Submits each required reference's approved source file
    into `book` as a draft with provenance. Sets `book`'s series to the
    source's series, or its title if it has none. Never approves or locks
    anything. Returns a summary of what was copied, also written to the audit
    log as `series_preset_applied`.
    """
    style_files, skipped_files = _copy_style_files(book, source)
    cover_files = _copy_cover_design(book, source)
    references = _copy_references(book, source)

    # An explicit `create --series` name wins; otherwise inherit the source's.
    book.state.series = book.state.series or source.state.series or source.state.title

    files = style_files + cover_files
    summary = {
        "source": source.state.book_id,
        "files": files,
        "skipped_files": skipped_files,
        "references": references,
        "series": book.state.series,
    }
    book.log("series_preset_applied", source=source.state.book_id, files=files,
             skipped_files=skipped_files, references=references, series=book.state.series)
    return summary
