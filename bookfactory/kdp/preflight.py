"""KDP preflight.

Checks the assembled interior against a KDP profile. Every number comes from
the profile JSON, never from a constant buried in the code, because Amazon
changes its requirements and this must stay a data edit.
"""

from __future__ import annotations

from bookfactory import SCHEMA_VERSION
from bookfactory.core import clock
from bookfactory.core.jsonio import write_json
from bookfactory.kdp import profiles

POINTS_PER_INCH = 72.0
SIZE_TOLERANCE_PT = 0.75


def _check(name: str, status: str, message: str, remedy: str | None = None) -> dict:
    return {"check": name, "status": status, "message": message, "remedy": remedy}


def preflight(book, *, write_report: bool = True) -> dict:
    profile_id = book.state.format.kdp_profile
    profile = profiles.load_profile(profile_id)
    checks: list[dict] = []

    interior = book.paths.interior_pdf
    if not interior.is_file():
        checks.append(_check(
            "interior.exists", "fail",
            "output/interior.pdf does not exist",
            "Run `bookfactory assemble <book>` first."))
        return _finalise(book, profile, checks, write_report)

    allowed = profile["interior"]["allowed_formats"]
    if interior.suffix.lstrip(".").lower() not in allowed:
        checks.append(_check("interior.format", "fail",
                             f"Interior must be one of {allowed}",
                             "Assemble to PDF."))

    size_mb = interior.stat().st_size / (1024 * 1024)
    max_mb = profile["interior"]["max_file_size_mb"]
    checks.append(_check(
        "interior.file_size",
        "pass" if size_mb <= max_mb else "fail",
        f"Interior is {size_mb:.1f} MB (limit {max_mb} MB)",
        None if size_mb <= max_mb else "Reduce image sizes and re-assemble."))

    from pypdf import PdfReader

    reader = PdfReader(str(interior))
    page_count = len(reader.pages)

    checks.extend(_page_count_checks(book, profile, page_count))
    checks.extend(_page_size_checks(book, reader, profile_id))
    checks.extend(_font_checks(book, reader, profile))
    checks.extend(_margin_checks(book, profile_id, page_count))
    checks.extend(_manifest_agreement_checks(book, page_count))

    return _finalise(book, profile, checks, write_report)


def _page_count_checks(book, profile, page_count: int) -> list[dict]:
    checks = []
    spec = profile["page_count"]
    minimum = int(spec["min"])
    interior_key = _interior_key(book)
    maximum = int(spec["max_by_interior"].get(interior_key, max(spec["max_by_interior"].values())))

    if page_count < minimum:
        checks.append(_check("page_count.minimum", "fail",
                             f"{page_count} pages; KDP requires at least {minimum}",
                             "Add pages, or merge this into a larger title."))
    elif page_count > maximum:
        checks.append(_check("page_count.maximum", "fail",
                             f"{page_count} pages; the limit for {interior_key} is {maximum}",
                             "Split the book or change the interior paper type."))
    else:
        checks.append(_check("page_count.range", "pass",
                             f"{page_count} pages, within {minimum}-{maximum} for {interior_key}"))

    if page_count % 2 != 0:
        checks.append(_check("page_count.even", "warn",
                             f"{page_count} pages is odd. "
                             + profile["warnings"]["page_count_odd"],
                             "Add a deliberate blank page to the manifest so you choose where it lands."))
    else:
        checks.append(_check("page_count.even", "pass", f"{page_count} pages is even"))

    spine_min = int(profile["warnings"].get("spine_text_min_pages", 0))
    if spine_min and page_count < spine_min:
        checks.append(_check("page_count.spine_text", "warn",
                             f"{page_count} pages is below the {spine_min} needed for spine text",
                             "Fine for a gift book; the cover just cannot carry a title on the spine."))
    return checks


def _interior_key(book) -> str:
    if book.state.format.colour:
        return "premium_colour"
    return "black_and_white_white_paper"


def _page_size_checks(book, reader, profile_id: str) -> list[dict]:
    trim_w, trim_h = profiles.trim_inches(book.state.format.trim, profile_id)
    bleed = profiles.bleed_inches(profile_id) if book.state.format.bleed else 0.0
    expected_w = (trim_w + bleed) * POINTS_PER_INCH
    expected_h = (trim_h + (2 * bleed)) * POINTS_PER_INCH

    wrong = []
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if (abs(width - expected_w) > SIZE_TOLERANCE_PT
                or abs(height - expected_h) > SIZE_TOLERANCE_PT):
            wrong.append(f"page {index} is {width:.1f}x{height:.1f}pt")

    if wrong:
        shown = "; ".join(wrong[:5])
        more = f" (+{len(wrong) - 5} more)" if len(wrong) > 5 else ""
        return [_check("trim.size", "fail",
                       f"Expected every page to be {expected_w:.1f}x{expected_h:.1f}pt "
                       f"({book.state.format.trim}"
                       f"{' plus bleed' if bleed else ''}), but {shown}{more}",
                       "Re-render the offending pages. Never rescale a PDF to fit.")]
    return [_check("trim.size", "pass",
                   f"All pages are {expected_w:.1f}x{expected_h:.1f}pt "
                   f"({book.state.format.trim}{' plus bleed' if bleed else ''})")]


def _font_checks(book, _reader, profile) -> list[dict]:
    if not profile["interior"].get("embedded_fonts_required"):
        return []
    from bookfactory.qa.technical import _fonts_embedded

    embedded = _fonts_embedded(book.paths.interior_pdf)
    if embedded is False:
        return [_check("fonts.embedded", "fail",
                       "The interior contains fonts that are not embedded",
                       "KDP rejects these. Re-render with the fonts available to the renderer.")]
    if embedded is None:
        return [_check("fonts.embedded", "warn",
                       "Could not determine whether all fonts are embedded",
                       "Check in a PDF reader's document properties before uploading.")]
    return [_check("fonts.embedded", "pass", "Fonts are embedded")]


def _margin_checks(book, profile_id: str, page_count: int) -> list[dict]:
    tokens = book.design_tokens()
    margins = tokens.get("margins_in", {})
    required_gutter = profiles.required_gutter_in(page_count, profile_id)
    min_outside = profiles.min_outside_margin_in(bleed=book.state.format.bleed,
                                                 profile_id=profile_id)
    checks = []
    inner = float(margins.get("inner", 0))
    if inner < required_gutter:
        checks.append(_check("margins.gutter", "fail",
                             f"Inner margin {inner}in is below the {required_gutter}in required "
                             f"for a {page_count}-page book",
                             "Raise margins_in.inner in style/design-tokens.json, re-render, "
                             "re-approve and re-assemble."))
    else:
        checks.append(_check("margins.gutter", "pass",
                             f"Inner margin {inner}in meets the {required_gutter}in requirement"))

    smallest = min(float(margins.get(edge, 0)) for edge in ("outer", "top", "bottom"))
    if smallest < min_outside:
        checks.append(_check("margins.outside", "fail",
                             f"Smallest outside margin is {smallest}in, minimum {min_outside}in",
                             "Raise it in style/design-tokens.json and re-render."))
    else:
        checks.append(_check("margins.outside", "pass",
                             f"Outside margins are at least {smallest}in "
                             f"(minimum {min_outside}in)"))
    return checks


def _manifest_agreement_checks(book, page_count: int) -> list[dict]:
    planned = len(book.manifest)
    if planned != page_count:
        return [_check("manifest.agreement", "fail",
                       f"The manifest plans {planned} pages but the interior has {page_count}",
                       "Re-assemble. The interior must be exactly the manifest.")]
    target = book.state.format.target_page_count
    checks = [_check("manifest.agreement", "pass",
                     f"Interior matches the manifest ({planned} pages)")]
    if target and abs(target - page_count) > max(4, target * 0.1):
        checks.append(_check("manifest.target", "warn",
                             f"Target page count was {target}, the book is {page_count}",
                             "Update format.target_page_count in book.json if the plan changed."))
    return checks


def _finalise(book, profile, checks: list[dict], write_report: bool) -> dict:
    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    status = "fail" if failures else ("warn" if warnings else "pass")
    report = {
        "schema_version": SCHEMA_VERSION,
        "book_id": book.state.book_id,
        "profile": profile["profile_id"],
        "profile_captured_on": profile.get("captured_on"),
        "run_at": clock.timestamp(),
        "status": status,
        "failures": len(failures),
        "warnings": len(warnings),
        "checks": checks,
    }
    if write_report:
        write_json(book.paths.preflight_report, report)
        book.log("preflight_run", status=status, failures=len(failures),
                 warnings=len(warnings), profile=profile["profile_id"])
        book.save()
    return report
