"""Cover gate and measurable print constraints."""

from __future__ import annotations

import pytest
from PIL import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from bookfactory.core import api, checksums, cover, gates, production, tasks
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import write_json


def _interior(book, pages=80):
    path = book.paths.interior_pdf
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=(432, 648))
    for _ in range(pages):
        pdf.showPage()
    pdf.save()


def test_new_book_requires_cover_but_legacy_book_does_not(new_book, workspace):
    assert cover.required(new_book)
    assert "cover" in " ".join(gates.release_ready(new_book).reasons).lower()
    cover.path(new_book).unlink()
    legacy = Book.load("test-book", workspace)
    assert cover.release_reasons(legacy) == []
    assert cover.readiness(legacy)["cover"] == "legacy_not_required"


def test_wrap_dimensions_follow_final_pdf_and_paper(new_book):
    _interior(new_book, 80)
    white = cover.dimensions(new_book)
    assert white["spine_in"] == .18016
    assert white["width_in"] == 12.43016
    assert white["height_in"] == 9.25
    data = cover.load(new_book)
    data["paper"] = "cream"
    write_json(cover.path(new_book), data)
    assert cover.dimensions(new_book)["spine_in"] == .2


def test_recovered_preview_can_size_draft_without_claiming_interior_readiness(new_book):
    _interior(new_book, 80)
    preserved = new_book.paths.root / "releases/preserved-interior.pdf"
    preserved.parent.mkdir(parents=True, exist_ok=True)
    new_book.paths.interior_pdf.rename(preserved)
    data = cover.load(new_book)
    data["preview_interior"] = {"path": "releases/preserved-interior.pdf",
                                "sha256": checksums.sha256_file(preserved)}
    write_json(cover.path(new_book), data)

    assert cover.dimensions(new_book)["width_in"] == 12.43016
    assert cover.readiness(new_book)["interior"] == "pending"
    with pytest.raises(ValidationError, match="Assemble the final interior"):
        cover.finalize(new_book, "v1")

    preserved.write_bytes(preserved.read_bytes() + b"changed")
    with pytest.raises(ValidationError, match="missing or has changed"):
        cover.dimensions(new_book)


def test_artwork_native_height_is_checked_and_draft_is_preserved(new_book, workspace):
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    source = workspace / "short.png"
    Image.new("RGB", (1024, 1200), "white").save(source)
    draft = api.submit_asset("test-book", cover.ART_ID, source, kind="asset", root=workspace)
    assert new_book.asset_constraints(new_book.registry.get(cover.ART_ID))["min_pixels"] == 1020
    assert [e["constraint"] for e in draft["constraint_failures"]] == ["min_height_pixels"]
    assert new_book.paths.resolve(draft["path"]).is_file()


def test_cover_checkpoint_waits_even_with_visual_checkpoint_authorization(new_book, workspace):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(direction="Matched cover direction", author="A Writer",
                back_copy="Some book copy", drafts=[{"revision": "v1", "path": "cover/drafts/cover-v1.pdf"}])
    write_json(cover.path(new_book), data)
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    source = workspace / "adequate.png"
    Image.new("RGB", (1100, 1600), "white").save(source)
    api.submit_asset("test-book", cover.ART_ID, source, kind="asset", root=workspace)
    book = Book.load("test-book", workspace)
    book.state.production_policy.mode = "visual_checkpoint"
    book.state.production_policy.operator_authorized = True
    task = tasks._cover_task(book)
    assert task.gate == "cover_visual_checkpoint"
    assert production.compute_mode(book, task) == "wait_for_operator"


def test_status_reports_interior_and_cover_separately(new_book, workspace):
    result = api.status("test-book", root=workspace)
    assert result["readiness"] == {"interior": "pending", "cover": "in_production",
                                   "book": "pending"}


def test_wrong_wrap_box_and_missing_selectable_type_fail(new_book, workspace):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(author="A Writer", back_copy="Back-cover statement")
    write_json(cover.path(new_book), data)
    wrong = workspace / "wrong-wrap.pdf"
    pdf = canvas.Canvas(str(wrong), pagesize=(612, 792))
    pdf.drawString(30, 700, "A Writer")
    pdf.save()
    failures = cover.check_pdf(new_book, wrong)
    assert any("box" in issue for issue in failures)
    assert any("selectable" in issue for issue in failures)


def test_migrating_former_release_preserves_interior_stage_evidence(new_book, workspace):
    _interior(new_book)
    cover.path(new_book).unlink()
    book = Book.load("test-book", workspace)
    book.state.stage = "release_ready"
    book.save()
    cover.initialize(book)
    assert Book.load("test-book", workspace).state.stage == "cover_production"
    assert book.paths.interior_pdf.is_file()


def test_explicit_cover_approval_then_preflight(new_book, workspace):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(direction="Match locked art", author="A Writer", back_copy="Gift for runners")
    write_json(cover.path(new_book), data)
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    art = workspace / "native.png"
    Image.new("RGB", (1100, 1600), "yellow").save(art)
    api.submit_asset("test-book", cover.ART_ID, art, kind="asset", root=workspace)
    wrap = workspace / "full-wrap.pdf"
    dim = cover.dimensions(new_book)
    pdfmetrics.registerFont(TTFont("CoverTest", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdf = canvas.Canvas(str(wrap), pagesize=(dim["width_in"]*72, dim["height_in"]*72))
    pdf.setFont("CoverTest", 18)
    pdf.drawString(6.6*72, 8*72, "Test Book")
    pdf.drawString(6.6*72, .5*72, "A Writer")
    pdf.drawString(.5*72, 5*72, "Gift for runners")
    pdf.drawImage(str(art), 7*72, 1.3*72, width=3.4*72, height=5.1*72)
    pdf.save()
    book = Book.load("test-book", workspace)
    draft = cover.submit(book, wrap)
    assert cover.readiness(book)["cover"] == "awaiting_approval"
    assert not gates.release_ready(book).ok
    cover.approve(book, draft["revision"], by="Test Operator")
    assert cover.preflight(book)["status"] == "pass"
    assert cover.readiness(book)["cover"] == "ready"


def test_provisional_cover_approval_waits_for_matching_final_interior(new_book, workspace):
    _interior(new_book)
    preserved = new_book.paths.root / "releases/preserved.pdf"
    preserved.parent.mkdir(exist_ok=True)
    new_book.paths.interior_pdf.rename(preserved)
    data = cover.load(new_book)
    data.update(direction="Match locked art", author="A Writer", back_copy="Gift for runners",
                preview_interior={"path": "releases/preserved.pdf",
                                  "sha256": checksums.sha256_file(preserved)})
    write_json(cover.path(new_book), data)
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.save()
    art = workspace / "native.png"
    Image.new("RGB", (1100, 1600), "yellow").save(art)
    api.submit_asset("test-book", cover.ART_ID, art, kind="asset", root=workspace)
    wrap = workspace / "wrap.pdf"
    dim = cover.dimensions(new_book)
    pdfmetrics.registerFont(TTFont("CoverTestProvisional", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdf = canvas.Canvas(str(wrap), pagesize=(dim["width_in"]*72, dim["height_in"]*72))
    pdf.setFont("CoverTestProvisional", 18)
    pdf.drawString(6.6*72, 8*72, "Test Book")
    pdf.drawString(6.6*72, .5*72, "A Writer")
    pdf.drawString(.5*72, 5*72, "Gift for runners")
    pdf.drawImage(str(art), 7*72, 1.3*72, width=3.4*72, height=5.1*72)
    pdf.save()
    book = Book.load("test-book", workspace)
    draft = cover.submit(book, wrap)
    approval = cover.approve(book, draft["revision"], by="Operator")
    assert approval["status"] == "review_approved"
    assert cover.readiness(book)["cover"] == "awaiting_final_interior"
    assert not (book.paths.root / "output/cover.pdf").exists()
    with pytest.raises(ValidationError, match="Assemble the final interior"):
        cover.finalize(book, draft["revision"])
    _interior(book, 82)
    with pytest.raises(ValidationError, match="dimensions changed"):
        cover.finalize(book, draft["revision"])
    _interior(book, 80)
    assert cover.finalize(book, draft["revision"])["by"] == "Operator"
    assert cover.preflight(book)["status"] == "pass"


def _wrap(book, workspace, name, *, art=None, dpi_art_size=None):
    """A full wrap with real embedded type, optionally placing an image on the front."""
    dim = cover.dimensions(book)
    wrap = workspace / name
    font = f"CoverTest-{name}"
    pdfmetrics.registerFont(TTFont(font, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdf = canvas.Canvas(str(wrap), pagesize=(dim["width_in"]*72, dim["height_in"]*72))
    pdf.setFont(font, 18)
    pdf.drawString(6.6*72, 8*72, "Test Book")
    pdf.drawString(6.6*72, .5*72, "A Writer")
    pdf.drawString(.5*72, 5*72, "Gift for runners")
    if art is not None:
        pdf.drawImage(str(art), 7*72, 1.3*72, width=3.4*72, height=5.1*72)
    pdf.save()
    return wrap


def _text_only_book(new_book):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(direction="Type only", author="A Writer", back_copy="Gift for runners")
    cover.save(new_book, data)
    cover.set_artwork(new_book, cover.TEXT_ONLY, by="Test Operator", reason="Operator choice")
    return Book.load("test-book", new_book.paths.root.parent.parent)


def test_text_only_cover_is_submitted_approved_and_preflighted_without_artwork(new_book, workspace):
    book = _text_only_book(new_book)
    assert book.registry.find(cover.ART_ID) is None
    # No artwork steps: the next cover task is the layout itself.
    assert tasks._cover_task(book).task_id.endswith("cover-layout")
    draft = cover.submit(book, _wrap(book, workspace, "text-only.pdf"))
    assert draft["artwork"] == "none" and draft["artwork_sha256"] is None
    assert tasks._cover_task(Book.load("test-book", workspace)).gate == "cover_visual_checkpoint"
    approved = cover.approve(Book.load("test-book", workspace), draft["revision"], by="Test Operator")
    assert approved["by"] == "Test Operator"
    book = Book.load("test-book", workspace)
    assert cover.preflight(book)["status"] == "pass"
    assert cover.readiness(book)["cover"] == "ready"
    events = [r for r in api.audit_history("test-book", root=workspace)
              if r["event"] == "cover_artwork_mode_set"]
    assert events and events[0]["mode"] == "none" and events[0]["by"] == "Test Operator"


def test_native_cover_still_requires_artwork(new_book, workspace):
    _interior(new_book)
    data = cover.load(new_book)
    data.update(author="A Writer", back_copy="Gift for runners")
    cover.save(new_book, data)
    assert cover.artwork_mode(cover.load(new_book)) == "native"
    failures = cover.check_pdf(new_book, _wrap(new_book, workspace, "no-art.pdf"))
    assert "No reviewable native cover artwork" in failures
    assert "Cover PDF contains no artwork image" in failures
    with pytest.raises(ValidationError, match="native cover artwork"):
        cover.submit(new_book, _wrap(new_book, workspace, "no-art-2.pdf"))


def test_text_only_cover_still_holds_placed_images_to_300_dpi(new_book, workspace):
    book = _text_only_book(new_book)
    small = workspace / "small.png"
    Image.new("RGB", (340, 510), "yellow").save(small)
    failures = cover.check_pdf(book, _wrap(book, workspace, "low-dpi.pdf", art=small))
    assert "Artwork below 300 DPI at actual PDF placement" in failures


def test_changing_artwork_mode_supersedes_pending_drafts(new_book, workspace):
    book = _text_only_book(new_book)
    draft = cover.submit(book, _wrap(book, workspace, "switch.pdf"))
    result = cover.set_artwork(Book.load("test-book", workspace), cover.NATIVE, by="Operator")
    assert result["superseded"] == [draft["revision"]]
    with pytest.raises(ValidationError, match="No reviewable cover draft"):
        cover.approve(Book.load("test-book", workspace), draft["revision"], by="Operator")
    # A draft recorded under the other mode is refused even if its status is hand-restored.
    data = cover.load(book)
    data["drafts"][0]["status"] = "draft"
    cover.save(book, data)
    with pytest.raises(ValidationError, match="artwork='none'"):
        cover.approve(Book.load("test-book", workspace), draft["revision"], by="Operator")


def test_artwork_mode_must_be_a_known_value(new_book):
    with pytest.raises(ValidationError):
        cover.set_artwork(new_book, "text", by="Operator")
    with pytest.raises(ValidationError):
        cover.set_artwork(new_book, cover.TEXT_ONLY, by=" ")
    data = cover.load(new_book)
    data["artwork"] = "None"
    with pytest.raises(ValidationError, match="cover.schema.json"):
        cover.save(new_book, data)


def test_cli_records_text_only_cover(new_book, workspace, capsys):
    from bookfactory.cli.main import main as cli

    assert cli(["cover", "artwork", "test-book", "--mode", "none", "--by", "Operator",
                "--root", str(workspace)]) == 0
    assert cover.text_only(Book.load("test-book", workspace))
    with pytest.raises(SystemExit):  # --by is required: the choice must name who made it
        cli(["cover", "artwork", "test-book", "--mode", "native", "--root", str(workspace)])


# ----------------------------------------------------------------------
# cover approve --autonomous
# ----------------------------------------------------------------------


def _native_cover_draft(new_book, workspace, policy):
    """A native-artwork cover draft awaiting approval, under `policy`."""
    _interior(new_book)
    data = cover.load(new_book)
    data.update(direction="Match locked art", author="A Writer", back_copy="Gift for runners")
    cover.save(new_book, data)
    new_book.register_asset(cover.ART_ID, kind="cover_artwork")
    new_book.state.production_policy = production.policy_from_choice(policy)
    new_book.save()
    art = workspace / "native.png"
    Image.new("RGB", (1100, 1600), "yellow").save(art)
    api.submit_asset("test-book", cover.ART_ID, art, kind="asset", root=workspace)
    book = Book.load("test-book", workspace)
    return cover.submit(book, _wrap(book, workspace, f"{policy}.pdf", art=art))


def test_autonomous_cover_approval_is_recorded_under_the_autonomous_policy(new_book, workspace):
    draft = _native_cover_draft(new_book, workspace, "autonomous")
    book = Book.load("test-book", workspace)
    task = tasks._cover_task(book)
    assert production.compute_mode(book, task) == "continue_automatically"
    assert "--autonomous" in task.instructions

    approved = cover.approve(book, draft["revision"], by="agent", autonomous=True)
    marker = "autonomous_production_policy:autonomous"
    assert approved["authorization"] == marker
    assert cover.load(book)["approved"]["authorization"] == marker
    for event in ("cover_visual_approved", "cover_approved"):
        assert api.audit_history("test-book", event=event, root=workspace)[-1][
            "authorization"] == marker
    # The native artwork it promoted is marked the same way.
    art = api.audit_history("test-book", event="approved", root=workspace)[-1]
    assert art["id"] == cover.ART_ID and art["authorization"] == marker


def test_autonomous_cover_approval_is_refused_where_the_operator_keeps_the_cover(
        new_book, workspace):
    from bookfactory.cli.main import main as cli

    draft = _native_cover_draft(new_book, workspace, "visual_checkpoint")
    book = Book.load("test-book", workspace)
    assert not gates.autonomous_cover_approval_authorized(book).ok
    assert "--autonomous" not in tasks._cover_task(book).instructions
    before = cover.path(book).read_bytes(), book.paths.audit_log.read_bytes()
    with pytest.raises(ValidationError, match="autonomous cover approval"):
        cover.approve(book, draft["revision"], by="agent", autonomous=True)
    assert cli(["cover", "approve", "test-book", "--draft", draft["revision"], "--by", "agent",
                "--autonomous", "--root", str(workspace)]) != 0
    book = Book.load("test-book", workspace)
    book.state.production_policy = production.policy_from_choice("checkpointed")
    book.save()
    with pytest.raises(ValidationError, match="autonomous cover approval"):
        cover.approve(Book.load("test-book", workspace), draft["revision"], by="agent",
                      autonomous=True)
    # A refusal changes nothing: no approval, no artwork promotion, no audit entry.
    book = Book.load("test-book", workspace)
    assert cover.path(book).read_bytes() == before[0]
    assert not book.registry.get(cover.ART_ID).is_approved
    assert api.audit_history("test-book", event="cover_visual_approved", root=workspace) == []


def test_an_ordinary_cover_approval_carries_no_autonomous_marker(new_book, workspace):
    draft = _native_cover_draft(new_book, workspace, "autonomous")
    approved = cover.approve(Book.load("test-book", workspace), draft["revision"],
                             by="Operator")
    assert "authorization" not in approved
    for event in ("cover_visual_approved", "cover_approved"):
        assert "authorization" not in api.audit_history(
            "test-book", event=event, root=workspace)[-1]


def test_finalize_carries_the_reviewed_authorization_forward(new_book, workspace):
    draft = _native_cover_draft(new_book, workspace, "autonomous")
    book = Book.load("test-book", workspace)
    preserved = book.paths.root / "releases/preserved.pdf"
    preserved.parent.mkdir(exist_ok=True)
    book.paths.interior_pdf.rename(preserved)
    data = cover.load(book)
    data["preview_interior"] = {"path": "releases/preserved.pdf",
                                "sha256": checksums.sha256_file(preserved)}
    cover.save(book, data)
    review = cover.approve(book, draft["revision"], by="agent", autonomous=True)
    assert review["status"] == "review_approved"
    assert review["authorization"] == "autonomous_production_policy:autonomous"
    _interior(book)
    task = tasks._cover_task(Book.load("test-book", workspace))
    assert task.task_id.endswith("cover-finalize")
    finalized = cover.finalize(Book.load("test-book", workspace), draft["revision"])
    assert finalized["authorization"] == "autonomous_production_policy:autonomous"


# ----------------------------------------------------------------------
# The approved cover lives at a tracked, checksummed path
# ----------------------------------------------------------------------


def _approved_text_only_cover(new_book, workspace):
    book = _text_only_book(new_book)
    draft = cover.submit(book, _wrap(book, workspace, "tracked.pdf"))
    cover.approve(Book.load("test-book", workspace), draft["revision"], by="Operator")
    return Book.load("test-book", workspace), draft


def test_approved_cover_is_the_tracked_draft_with_its_checksum(new_book, workspace):
    book, draft = _approved_text_only_cover(new_book, workspace)
    approved = cover.load(book)["approved"]
    assert approved["path"] == draft["path"] == "cover/drafts/cover-v1.pdf"
    tracked = book.paths.resolve(approved["path"])
    assert approved["sha256"] == checksums.sha256_file(tracked)
    assert checksums.is_immutable(tracked)
    # Stored once: no second tracked copy, and output/ holds only the upload copy.
    assert not (book.paths.root / "cover/_history").exists()
    assert checksums.sha256_file(cover.output_path(book)) == approved["sha256"]
    assert api.status("test-book", root=workspace)["outputs"]["cover_pdf"] == approved["path"]
    assert api.validate("test-book", root=workspace)["ok"]


def test_fresh_clone_without_output_still_has_the_approved_cover(new_book, workspace):
    book, _draft = _approved_text_only_cover(new_book, workspace)
    cover.output_path(book).unlink()  # books/*/output/ is gitignored
    assert api.validate("test-book", root=workspace)["ok"]
    assert cover.preflight(book)["status"] == "pass"
    assert cover.output_path(book).is_file()  # regenerated from the tracked file


def test_validate_and_status_flag_a_missing_or_tampered_approved_cover(new_book, workspace):
    book, draft = _approved_text_only_cover(new_book, workspace)
    assert cover.preflight(book)["status"] == "pass"
    tracked = book.paths.resolve(draft["path"])

    checksums.unlock_for_system(tracked)
    tracked.write_bytes(tracked.read_bytes() + b"%tampered")
    result = api.validate("test-book", root=workspace)
    assert not result["ok"]
    assert any("checksum mismatch" in p and draft["path"] in p for p in result["problems"])
    status = api.status("test-book", root=workspace)
    assert any("approved cover" in p for p in status["approved_integrity"])
    assert status["readiness"]["cover"] != "ready"
    assert cover.preflight(Book.load("test-book", workspace))["status"] == "fail"

    tracked.unlink()
    result = api.validate("test-book", root=workspace)
    assert any("file missing" in p and draft["path"] in p for p in result["problems"])


def test_old_format_approval_without_a_path_still_loads(new_book, workspace):
    book, draft = _approved_text_only_cover(new_book, workspace)
    data = cover.load(book)
    del data["approved"]["path"]  # as written before approvals recorded their file
    cover.save(book, data)
    book = Book.load("test-book", workspace)
    assert cover.approved_file(book) == draft["path"]
    assert api.validate("test-book", root=workspace)["ok"]
    assert api.status("test-book", root=workspace)["outputs"]["cover_pdf"] == draft["path"]

    # With no matching tracked draft, validate says so and how to fix it.
    data["drafts"][0]["sha256"] = "0" * 64
    cover.save(book, data)
    problems = api.validate("test-book", root=workspace)["problems"]
    assert any("no tracked copy" in p for p in problems)
