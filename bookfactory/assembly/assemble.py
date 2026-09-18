"""Deterministic PDF assembly.

The one rule: if anything is missing, unapproved or fails its checksum,
assembly stops and says so. It never uses the closest available file.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory import SCHEMA_VERSION
from bookfactory.core import checksums, clock
from bookfactory.core.errors import AssemblyError
from bookfactory.core.jsonio import write_json
from bookfactory.qa import assembly as assembly_qa

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
POINTS_PER_INCH = 72.0
ASPECT_TOLERANCE = 0.01


def assemble(book, *, destination: Path | str | None = None,
             label: str = "interior", skip_checks: bool = False) -> dict:
    """Build the interior PDF from approved pages. Returns an assembly record."""
    if not skip_checks:
        result = assembly_qa.check(book)
        if result.errors:
            raise AssemblyError(
                "Assembly refused - the book is not ready:\n  - "
                + "\n  - ".join(f.message for f in result.errors),
                remedy="Fix each item above. Assembly never substitutes a near-enough file.",
            )

    from pypdf import PdfWriter

    pages = list(book.manifest)
    if not pages:
        raise AssemblyError("Nothing to assemble: the page manifest is empty")

    destination = Path(destination) if destination else book.paths.interior_pdf
    destination.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()
    included: list[dict] = []
    temp_files: list[Path] = []

    try:
        for page in pages:
            approved = page.approved
            if approved is None:  # pragma: no cover - guarded by assembly QA
                raise AssemblyError(f"{page.page_id} is not approved")
            source = book.paths.resolve(approved.path)
            checksums.verify(source, approved.sha256)

            pdf_source = source
            if source.suffix.lower() in IMAGE_SUFFIXES:
                pdf_source = _image_to_pdf_page(book, source, page.page_id)
                temp_files.append(pdf_source)

            from pypdf import PdfReader

            reader = PdfReader(str(pdf_source))
            if len(reader.pages) != 1:
                raise AssemblyError(
                    f"{page.page_id}: approved artefact has {len(reader.pages)} PDF pages, "
                    "expected exactly 1"
                )
            writer.add_page(reader.pages[0])
            included.append({
                "position": len(included) + 1,
                "page_id": page.page_id,
                "sequence": page.sequence,
                "printed_number": page.printed_number,
                "chapter": page.chapter,
                "title": page.title,
                "source": approved.path,
                "sha256": approved.sha256,
                "revision": approved.revision,
            })

        writer.add_metadata({
            "/Title": book.state.title,
            "/Author": book.state.series or book.state.title,
            "/Producer": "Book Factory",
            "/Creator": f"Book Factory assembly ({label})",
        })
        with destination.open("wb") as handle:
            writer.write(handle)
    finally:
        for temp in temp_files:
            temp.unlink(missing_ok=True)

    from bookfactory.render.backends import normalise_pdf

    normalise_pdf(destination)

    record = {
        "schema_version": SCHEMA_VERSION,
        "book_id": book.state.book_id,
        "label": label,
        "assembled_at": clock.timestamp(),
        "output": book.paths.relative(destination),
        "output_sha256": checksums.sha256_file(destination),
        "page_count": len(included),
        "manuscript_version": book.state.manuscript.version,
        "visual_style_version": book.state.style.visual_version,
        "pages": included,
    }
    write_json(destination.with_suffix(".manifest.json"), record)
    book.log("assembled", label=label, output=record["output"],
             page_count=record["page_count"], sha256=record["output_sha256"])
    book.save()
    return record


def _image_to_pdf_page(book, source: Path, page_id: str) -> Path:
    """Wrap an approved raster page in a PDF page at exactly the trim size.

    The pixels are passed through untouched. If the image is not the trim's
    aspect ratio we refuse rather than crop or stretch it - a silently cropped
    page is exactly the kind of quiet damage this system exists to prevent.
    """
    from PIL import Image

    from bookfactory.kdp import profiles

    profile_id = book.state.format.kdp_profile
    trim_w, trim_h = profiles.trim_inches(book.state.format.trim, profile_id)
    bleed = profiles.bleed_inches(profile_id) if book.state.format.bleed else 0.0
    target_w = trim_w + bleed
    target_h = trim_h + (2 * bleed)
    target_aspect = target_w / target_h

    with Image.open(source) as image:
        aspect = image.width / image.height
        if abs(aspect - target_aspect) > ASPECT_TOLERANCE:
            raise AssemblyError(
                f"{page_id}: approved image is {image.width}x{image.height} "
                f"(aspect {aspect:.4f}) but the page is {target_w}x{target_h}in "
                f"(aspect {target_aspect:.4f})",
                remedy=("Re-render the page at the correct trim. Assembly will not crop or "
                        "stretch an approved artefact."),
            )
        resolution = image.width / target_w
        output = book.paths.tmp_dir / f"{page_id}-assembly.pdf"
        output.parent.mkdir(parents=True, exist_ok=True)
        converted = image.convert("RGB") if image.mode not in ("RGB", "L") else image
        converted.save(output, "PDF", resolution=resolution)
    return output
