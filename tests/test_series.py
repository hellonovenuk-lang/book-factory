"""Series presets: `bookfactory create --series-from <source-book>`.

See `PLAN.md`, "Phase 6: Series presets", for the contract these tests check.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bookfactory.cli.main import main
from bookfactory.core import api, cover
from bookfactory.core.book import ASSET, Book
from bookfactory.core.errors import ValidationError


def test_refuses_a_source_whose_style_is_not_locked(new_book: Book, workspace: Path) -> None:
    with pytest.raises(ValidationError):
        api.create_book("Book Two", policy="checkpointed", book_id="book-two",
                        root=workspace, series_from="test-book")
    assert not Book.exists("book-two", workspace)


def _add_cover_design(source: Book) -> None:
    """Give the locked source book a cover design block with a font file to copy."""
    font_path = source.paths.root / "style/fonts/Title.ttf"
    font_path.parent.mkdir(parents=True, exist_ok=True)
    font_path.write_bytes(b"not a real font, just bytes to copy")
    data = cover.load(source)
    data["design"] = {"background": "#fff8ee", "ink": "#101010",
                      "title_font": "style/fonts/Title.ttf"}
    cover.save(source, data)


def test_series_preset_copies_locked_style_and_submits_references_as_drafts(
    locked_book: Book, workspace: Path,
) -> None:
    source = locked_book
    _add_cover_design(source)
    required_ids = source.required_reference_ids()
    source_shas = {
        asset_id: source.registry.find(asset_id).approved.sha256
        for asset_id in required_ids
    }
    source_revisions = {
        asset_id: source.registry.find(asset_id).approved.revision
        for asset_id in required_ids
    }

    result = api.create_book("Book Two", policy="visual_checkpoint", book_id="book-two",
                             root=workspace, series_from="test-book")
    assert "series_preset" in result
    preset = result["series_preset"]
    assert preset["source"] == "test-book"
    assert preset["series"] == source.state.title

    new_book = Book.load("book-two", workspace)

    # Series recorded.
    assert new_book.state.series == source.state.title

    # Style files copied byte for byte.
    for attr in ("voice_bible", "writing_sample_file", "visual_bible", "design_tokens",
                 "reference_set"):
        source_path = getattr(source.paths, attr)
        dest_path = getattr(new_book.paths, attr)
        assert dest_path.is_file()
        assert dest_path.read_bytes() == source_path.read_bytes()

    # Cover design block, including the font file, copied.
    new_cover = cover.load(new_book)
    assert new_cover["design"]["title_font"] == "style/fonts/Title.ttf"
    dest_font = new_book.paths.root / "style/fonts/Title.ttf"
    assert dest_font.is_file()
    assert dest_font.read_bytes() == (source.paths.root / "style/fonts/Title.ttf").read_bytes()

    # Every required reference exists in the new book as a draft, not approved,
    # with provenance pointing at the source's approved file.
    assert required_ids, "fixture should require at least one reference"
    for asset_id in required_ids:
        asset = new_book.registry.find(asset_id)
        assert asset is not None
        assert not asset.is_approved
        assert asset.drafts, f"{asset_id} should have a draft"
        draft = asset.drafts[-1]
        assert draft.source == "series:test-book"
        assert draft.sha256 == source_shas[asset_id]
        assert source_revisions[asset_id] in (draft.note or "")

    # Nothing approved or locked on the operator's behalf.
    assert not new_book.state.style.voice_locked
    assert not new_book.state.style.visual_locked
    assert all(not new_book.registry.find(a).is_approved for a in required_ids)

    # Audit entry present.
    from bookfactory.core import audit
    events = audit.history(new_book.paths.audit_log, event="series_preset_applied")
    assert len(events) == 1
    assert events[0]["source"] == "test-book"


def test_series_preset_does_not_skip_the_operators_checkpoints(
    locked_book: Book, workspace: Path,
) -> None:
    """The new book's own policy governs it. The preset only pre-populates
    style files and reference drafts: the new book still starts at its own
    brief, and under visual_checkpoint its visual lock stays the operator's,
    even once the copied references are reviewed."""
    from bookfactory.core import gates

    source = locked_book
    api.create_book("Book Two", policy="visual_checkpoint", book_id="book-two",
                    root=workspace, series_from="test-book")
    task = api.next_task("book-two", root=workspace)
    assert task["task_id"] == "book-two-brief", "a series book still writes its own brief"

    for asset_id in source.required_reference_ids():
        api.approve("book-two", asset_id, kind=ASSET, root=workspace, by="tester")
    new_book = Book.load("book-two", workspace)
    assert not new_book.state.style.voice_locked
    assert not new_book.state.style.visual_locked
    assert not gates.autonomous_lock_authorized(new_book, "visual").ok


def test_cli_create_series_from_end_to_end(locked_book: Book, workspace: Path, capsys) -> None:
    code = main(["--root", str(workspace), "create", "Book Two", "--policy", "checkpointed",
                "--id", "book-two-cli", "--series-from", "test-book"])
    assert code == 0
    out = capsys.readouterr().out
    assert "CREATED" in out
    assert Book.exists("book-two-cli", workspace)
