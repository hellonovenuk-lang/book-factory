"""Technical QA - print compliance and file integrity."""

from __future__ import annotations

from pathlib import Path

from bookfactory.core import checksums
from bookfactory.qa.findings import LayerResult

POINTS_PER_INCH = 72.0
#: PDF page boxes are floats; a thousandth of an inch of slop is not a defect.
SIZE_TOLERANCE_PT = 0.75


def _pdf_page_size(path: Path) -> tuple[float, float] | None:
    try:
        from pypdf import PdfReader

        box = PdfReader(str(path)).pages[0].mediabox
        return float(box.width), float(box.height)
    except Exception:  # noqa: BLE001
        return None


def _pdf_page_count(path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001
        return None


def _fonts_embedded(path: Path) -> bool | None:
    """True if every font on page 1 carries an embedded font file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        page = reader.pages[0]
        resources = page.get("/Resources")
        if resources is None:
            return None
        fonts = resources.get_object().get("/Font")
        if fonts is None:
            return True
        for font_ref in fonts.get_object().values():
            font = font_ref.get_object()
            descendants = font.get("/DescendantFonts")
            targets = ([d.get_object() for d in descendants.get_object()]
                       if descendants is not None else [font])
            for target in targets:
                descriptor = target.get("/FontDescriptor")
                if descriptor is None:
                    return False
                descriptor = descriptor.get_object()
                if not any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3")):
                    return False
        return True
    except Exception:  # noqa: BLE001
        return None


def check(book) -> LayerResult:
    result = LayerResult("technical")
    from bookfactory.kdp import profiles

    profile_id = book.state.format.kdp_profile
    profile = profiles.load_profile(profile_id)
    trim_w_in, trim_h_in = profiles.trim_inches(book.state.format.trim, profile_id)
    bleed_in = profiles.bleed_inches(profile_id) if book.state.format.bleed else 0.0
    expected_w = (trim_w_in + bleed_in) * POINTS_PER_INCH
    expected_h = (trim_h_in + (2 * bleed_in)) * POINTS_PER_INCH

    for problem in book.manifest.problems():
        result.error("technical.manifest", f"Page manifest: {problem}",
                     remedy="Fix pages/manifest.json before producing more pages.")
    for problem in book.registry.problems():
        result.error("technical.registry", f"Asset registry: {problem}")

    for page in book.manifest:
        if not page.approved:
            continue
        path = book.paths.resolve(page.approved.path)
        if not path.exists():
            result.error("technical.missing_approved",
                         f"{page.page_id}: approved file missing ({page.approved.path})",
                         page_id=page.page_id)
            continue
        if not checksums.matches(path, page.approved.sha256):
            result.error("technical.checksum_mismatch",
                         f"{page.page_id}: approved file no longer matches its recorded checksum",
                         page_id=page.page_id,
                         remedy="Restore the file, or open a revision with `bookfactory revise`.")
            continue
        if not checksums.is_immutable(path):
            result.warn("technical.writable_approved",
                        f"{page.page_id}: approved file is writable",
                        page_id=page.page_id,
                        remedy="Run `bookfactory relock <book>` (git restores contents, not file modes).")

        if path.suffix.lower() == ".pdf":
            count = _pdf_page_count(path)
            if count != 1:
                result.error("technical.multi_page_artefact",
                             f"{page.page_id}: approved PDF has {count} pages, expected 1",
                             page_id=page.page_id)
            size = _pdf_page_size(path)
            if size:
                width, height = size
                if (abs(width - expected_w) > SIZE_TOLERANCE_PT
                        or abs(height - expected_h) > SIZE_TOLERANCE_PT):
                    result.error("technical.wrong_trim",
                                 f"{page.page_id}: page is {width:.1f}x{height:.1f}pt, "
                                 f"expected {expected_w:.1f}x{expected_h:.1f}pt "
                                 f"({book.state.format.trim}"
                                 f"{' with bleed' if bleed_in else ''})",
                                 page_id=page.page_id,
                                 remedy="Re-render the page; do not rescale the PDF.")
            if profile["interior"].get("embedded_fonts_required"):
                embedded = _fonts_embedded(path)
                if embedded is False:
                    result.error("technical.fonts_not_embedded",
                                 f"{page.page_id}: fonts are not embedded",
                                 page_id=page.page_id,
                                 remedy="KDP rejects interiors with unembedded fonts.")

    _check_margins(book, result, profile_id)
    _check_page_numbers(book, result)
    return result


def _check_margins(book, result: LayerResult, profile_id: str) -> None:
    from bookfactory.kdp import profiles

    tokens = book.design_tokens()
    margins = tokens.get("margins_in", {})
    page_count = len(book.manifest)
    if page_count == 0:
        return
    required_gutter = profiles.required_gutter_in(page_count, profile_id)
    min_outside = profiles.min_outside_margin_in(bleed=book.state.format.bleed,
                                                 profile_id=profile_id)
    inner = float(margins.get("inner", 0))
    if inner < required_gutter:
        result.error("technical.gutter_too_small",
                     f"Inner margin is {inner}in but a {page_count}-page book needs at least "
                     f"{required_gutter}in of gutter",
                     remedy="Raise margins_in.inner in style/design-tokens.json and re-render.")
    for edge in ("outer", "top", "bottom"):
        value = float(margins.get(edge, 0))
        if value < min_outside:
            result.error("technical.margin_too_small",
                         f"{edge.capitalize()} margin is {value}in, minimum is {min_outside}in",
                         remedy="Raise it in style/design-tokens.json and re-render.")


def _check_page_numbers(book, result: LayerResult) -> None:
    pages = list(book.manifest)
    numbered = [p for p in pages if p.printed_number is not None]
    if not numbered:
        result.warn("technical.no_printed_numbers",
                    "No page carries a printed page number",
                    remedy="Run `bookfactory plan <book> --renumber`.")
        return
    for page in numbered:
        if page.printed_number < 1:
            result.error("technical.bad_printed_number",
                         f"{page.page_id} has printed number {page.printed_number}",
                         page_id=page.page_id)
    seen: dict[int, str] = {}
    for page in numbered:
        if page.printed_number in seen:
            result.error("technical.duplicate_printed_number",
                         f"{page.page_id} and {seen[page.printed_number]} both print as page "
                         f"{page.printed_number}",
                         page_id=page.page_id)
        seen[page.printed_number] = page.page_id
