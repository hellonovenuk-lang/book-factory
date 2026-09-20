"""Versioned print-cover drafts and a separate KDP readiness gate.

Projects created before this feature have no cover/cover.json and remain legacy
interior-only projects until explicitly migrated with `cover init`.
"""

from __future__ import annotations

import math
import shutil
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from bookfactory.core import checksums, clock
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import read_json, write_json

BLEED = .125
SPINE_PER_PAGE = {"white": .002252, "cream": .0025}
ART_ID = "cover-front-artwork"


def path(book) -> Path:
    return book.paths.root / "cover/cover.json"


def load(book) -> dict:
    return read_json(path(book)) if path(book).is_file() else {}


def required(book) -> bool:
    return bool(load(book).get("required"))


def initialize(book, *, paper: str = "white", finish: str = "matte") -> dict:
    if paper not in SPINE_PER_PAGE or finish not in ("matte", "glossy"):
        raise ValidationError("Choose KDP white/cream paper and matte/glossy finish")
    if path(book).exists():
        raise ValidationError("Cover already configured")
    data = {"required": True, "paper": paper, "finish": finish,
            "direction": "", "author": "", "back_copy": "",
            "artwork_width_in": 3.4, "artwork_height_in": 5.1,
            "drafts": [], "approved": None, "preflight": None}
    write_json(path(book), data)
    book.log("cover_required", paper=paper, finish=finish)
    # Older print books must be explicitly reopened for cover production.
    from bookfactory.core import stages
    if book.state.stage == stages.RELEASE_READY:
        book._transition(stages.COVER_PRODUCTION, by="system",
                         note="Legacy interior-only release reopened for required print cover")
    book.save()
    return data


def dimensions(book) -> dict:
    from bookfactory.kdp.profiles import trim_inches
    data = load(book)
    if data.get("paper") not in SPINE_PER_PAGE:
        raise ValidationError("Select paper before calculating the cover")
    interior = book.paths.interior_pdf
    if not interior.is_file():
        # A recovered project can develop a review draft against an immutable
        # preserved interior. This does not establish interior readiness.
        preview = data.get("preview_interior") or {}
        if not preview.get("path") or not preview.get("sha256"):
            raise ValidationError("Assemble the final interior before sizing the cover, or record a checksummed preview_interior")
        interior = book.paths.resolve(preview["path"])
        if not interior.resolve().is_relative_to(book.paths.root.resolve()):
            raise ValidationError("The preview interior must be inside this book project")
        if not interior.is_file() or checksums.sha256_file(interior) != preview["sha256"]:
            raise ValidationError("The preserved preview interior is missing or has changed")
    pages = len(PdfReader(str(interior)).pages)
    trim_w, trim_h = trim_inches(book.state.format.trim, book.state.format.kdp_profile)
    spine = pages * SPINE_PER_PAGE[data["paper"]]
    return {"page_count": pages, "paper": data["paper"], "spine_in": round(spine, 6),
            "width_in": round(2 * trim_w + spine + 2 * BLEED, 6),
            "height_in": round(trim_h + 2 * BLEED, 6),
            "trim_width_in": trim_w, "trim_height_in": trim_h, "bleed_in": BLEED}


def artwork_constraints(book) -> dict:
    data = load(book)
    return {"embedded_text": False, "maintain_character_identity": True,
            "maintain_style": True, "colour": True, "readable_image": True,
            "min_pixels": math.ceil(float(data["artwork_width_in"]) * 300),
            "min_height_pixels": math.ceil(float(data["artwork_height_in"]) * 300)}


def artwork_failures(book, file: str | Path) -> list[dict]:
    expected = artwork_constraints(book)["min_height_pixels"]
    try:
        with Image.open(file) as im:
            actual = im.height
    except Exception:
        return []  # Existing readable_image check handles invalid files.
    if actual >= expected:
        return []
    return [{"constraint": "min_height_pixels", "expected": expected, "actual": actual,
             "message": f"Native cover art is {actual}px high, requires {expected}px",
             "remedy": "Regenerate natively at print resolution; do not upscale."}]


def _artwork(book):
    asset = book.registry.find(ART_ID)
    return asset, asset.approved or asset.reviewable_draft() if asset else None


def check_pdf(book, file: str | Path) -> list[str]:
    data, dim = load(book), dimensions(book)
    problems = []
    pdf = PdfReader(str(file))
    if len(pdf.pages) != 1:
        return ["Cover must be a single full-wrap PDF page"]
    sheet = pdf.pages[0]
    width, height = float(sheet.mediabox.width)/72, float(sheet.mediabox.height)/72
    if abs(width-dim["width_in"]) > .001 or abs(height-dim["height_in"]) > .001:
        problems.append(f"Cover PDF box {width:.5f} x {height:.5f} in differs from calculated wrap")
    extracted = "".join(c for c in (sheet.extract_text() or "").casefold() if c.isalnum())
    for value in (book.state.title, data.get("author"), data.get("back_copy")):
        if not value or "".join(c for c in value.casefold() if c.isalnum()) not in extracted:
            problems.append(f"Missing selectable cover type: {str(value)[:50]}")
    asset, artwork = _artwork(book)
    if not artwork:
        problems.append("No reviewable native cover artwork")
    else:
        problems.extend(f["message"] for f in book.check_asset_constraints(
            asset, book.paths.resolve(artwork.path)))
    if data.get("spine_text") and (dim["page_count"] < 79 or dim["spine_in"]-.125 < 7/72):
        problems.append("Spine text cannot fit KDP's page count, 7 pt minimum and fold clearances")
    try:
        import fitz
        with fitz.open(str(file)) as doc:
            page = doc[0]
            back_fold = (BLEED + dim["trim_width_in"]) * 72
            front_fold = back_fold + dim["spine_in"] * 72
            safe = .25 * 72  # .125 bleed plus .125 inward text margin.
            barcode = fitz.Rect((BLEED + dim["trim_width_in"] - 2.16)*72,
                                (dim["height_in"] - 1.56)*72,
                                (BLEED + dim["trim_width_in"] - .14)*72,
                                (dim["height_in"] - .34)*72)
            used_fonts = set()
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        used_fonts.add(span["font"])
                        box = fitz.Rect(span["bbox"])
                        if span["size"] < 7 or box.y0 < safe or box.y1 > page.rect.height-safe:
                            problems.append(f"Unsafe or undersized type: {span['text'][:35]}")
                        if box.x0 < back_fold and (box.x0 < safe or box.x1 > back_fold-safe):
                            problems.append(f"Back type enters trim/spine safety: {span['text'][:35]}")
                        if box.x0 >= front_fold and (box.x0 < front_fold+safe or box.x1 > page.rect.width-safe):
                            problems.append(f"Front type enters trim/spine safety: {span['text'][:35]}")
                        if box.intersects(barcode):
                            problems.append("Type enters the KDP barcode zone")
            images = page.get_images(full=True)
            if not images:
                problems.append("Cover PDF contains no artwork image")
            for image in images:
                for box in page.get_image_rects(image[0]):
                    if min(image[2]*72/box.width, image[3]*72/box.height) < 299.99:
                        problems.append("Artwork below 300 DPI at actual PDF placement")
                    if box.intersects(barcode):
                        problems.append("Cover artwork enters the KDP barcode zone")
            for font in page.get_fonts(full=True):
                base_name = font[3].split("+")[-1]
                if (font[0] > 0 and
                        any(base_name in used or used in base_name for used in used_fonts) and
                        not doc.extract_font(font[0])[3]):
                    problems.append(f"Cover font is not embedded: {font[3]}")
    except Exception as exc:
        problems.append(f"Could not inspect PDF artwork and type: {exc}")
    return problems


def submit(book, file: str | Path) -> dict:
    if not required(book):
        raise ValidationError("Enable cover production with cover init")
    problems = check_pdf(book, file)
    if problems:
        raise ValidationError("Cover draft failed: " + "; ".join(problems))
    data = load(book)
    revision = f"v{len(data['drafts'])+1}"
    output = book.paths.root / f"cover/drafts/cover-{revision}.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file, output)
    for prior in data["drafts"]:
        if prior["status"] in ("draft", "review_approved"):
            prior["status"] = "superseded"
    asset, art = _artwork(book)
    record = {"revision": revision, "path": book.paths.relative(output),
              "sha256": checksums.sha256_file(output), "artwork_sha256": art.sha256,
              "status": "draft", "submitted_at": clock.timestamp(), "dimensions": dimensions(book)}
    data["drafts"].append(record)
    write_json(path(book), data)
    book.log("cover_draft_submitted", revision=revision, path=record["path"])
    book.save()
    return record


def approve(book, revision: str, *, by: str) -> dict:
    if not by.strip():
        raise ValidationError("The operator must explicitly identify cover approval")
    data = load(book)
    candidate = next((d for d in data["drafts"] if d["revision"] == revision), None)
    if not candidate or candidate["status"] != "draft":
        raise ValidationError("No reviewable cover draft with that revision")
    source = book.paths.resolve(candidate["path"])
    checksums.verify(source, candidate["sha256"])
    asset, art = _artwork(book)
    if not art or art.sha256 != candidate["artwork_sha256"]:
        raise ValidationError("Cover artwork changed since draft submission")
    failures = check_pdf(book, source)
    if failures:
        raise ValidationError("Cover no longer passes checks: " + "; ".join(failures))
    if not asset.approved:
        book.approve("asset", ART_ID, revision=art.revision, by=by,
                     note=f"Explicit operator cover approval {revision}")
    candidate["status"] = "review_approved"
    candidate["review_approval"] = {"at": clock.timestamp(), "by": by}
    write_json(path(book), data)
    book.log("cover_visual_approved", revision=revision, by=by,
             provisional=not book.paths.interior_pdf.is_file())
    book.save()
    if not book.paths.interior_pdf.is_file():
        return {"revision": revision, "by": by, "status": "review_approved",
                "awaiting": "final_interior_and_cover_finalization"}
    return finalize(book, revision)


def finalize(book, revision: str) -> dict:
    """Promote an operator-approved draft only after final interior sizing agrees."""
    if not book.paths.interior_pdf.is_file():
        raise ValidationError("Assemble the final interior before finalizing the cover")
    data = load(book)
    candidate = next((d for d in data["drafts"] if d["revision"] == revision), None)
    if not candidate or candidate["status"] != "review_approved" or not candidate.get("review_approval"):
        raise ValidationError("The operator must approve this cover draft first")
    if candidate["dimensions"] != dimensions(book):
        raise ValidationError("Final interior dimensions changed; submit a resized cover for review")
    source = book.paths.resolve(candidate["path"])
    checksums.verify(source, candidate["sha256"])
    asset, art = _artwork(book)
    if not asset or not asset.approved or asset.approved.sha256 != candidate["artwork_sha256"]:
        raise ValidationError("Approved cover artwork changed since review")
    failures = check_pdf(book, source)
    if failures:
        raise ValidationError("Cover no longer passes checks: " + "; ".join(failures))
    destination = book.paths.root / "output/cover.pdf"
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        history = book.paths.root / "cover/_history"
        history.mkdir(exist_ok=True)
        shutil.copy2(destination, history / f"cover-{data['approved']['revision']}.pdf")
    shutil.copy2(source, destination)
    candidate["status"] = "approved"
    data["approved"] = {"revision": revision, "sha256": candidate["sha256"],
                        "at": clock.timestamp(), "by": candidate["review_approval"]["by"]}
    data["preflight"] = None
    write_json(path(book), data)
    book.log("cover_approved", revision=revision, by=candidate["review_approval"]["by"])
    book.save()
    return data["approved"]


def preflight(book) -> dict:
    data = load(book)
    if not data.get("approved"):
        raise ValidationError("The operator must approve the cover draft first")
    file = book.paths.root / "output/cover.pdf"
    problems = check_pdf(book, file)
    if checksums.sha256_file(file) != data["approved"]["sha256"]:
        problems.append("Cover PDF differs from approved draft")
    record = {"status": "fail" if problems else "pass", "errors": problems,
              "cover_sha256": checksums.sha256_file(file),
              "page_count": dimensions(book)["page_count"], "run_at": clock.timestamp()}
    data["preflight"] = record
    write_json(path(book), data)
    book.save()
    return record


def preflight_current(book) -> bool:
    data = load(book)
    report, approved = data.get("preflight") or {}, data.get("approved") or {}
    return (report.get("status") == "pass" and
            report.get("cover_sha256") == approved.get("sha256") and
            report.get("page_count") == dimensions(book)["page_count"])


def release_reasons(book) -> list[str]:
    if not required(book):
        return []
    data = load(book)
    if any(d["status"] == "review_approved" for d in data.get("drafts", [])):
        return ["Reviewed cover awaits final interior and cover finalization"]
    if not data.get("approved"):
        return ["Full-wrap cover awaits operator approval"]
    if not preflight_current(book):
        return ["Approved cover has not passed current cover preflight"]
    return []


def readiness(book) -> dict:
    interior = (book.paths.interior_pdf.is_file() and
                (book.latest_preflight() or {}).get("status") in ("pass", "warn"))
    data = load(book)
    cover_state = ("legacy_not_required" if not required(book) else
                   "ready" if preflight_current(book) else
                   "awaiting_final_interior" if any(d["status"] == "review_approved" for d in data.get("drafts", [])) else
                   "awaiting_approval" if data.get("drafts") and not data.get("approved") else
                   "pending_preflight" if data.get("approved") else "in_production")
    return {"interior": "ready" if interior else "pending", "cover": cover_state,
            "book": "ready" if interior and not release_reasons(book) else "pending"}
