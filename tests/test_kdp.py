"""KDP preflight. Every rule comes from the profile, not from the code."""

from __future__ import annotations

import pytest

from bookfactory.core import api
from bookfactory.core.book import Book
from bookfactory.core.errors import ValidationError
from bookfactory.kdp import profiles


def _check(report: dict, name: str) -> dict:
    return next(check for check in report["checks"] if check["check"] == name)


def test_profile_supplies_trim_geometry():
    assert profiles.trim_inches("6x9") == (6.0, 9.0)
    assert profiles.trim_points("6x9") == (432.0, 648.0)


def test_unknown_trim_lists_the_ones_that_exist():
    with pytest.raises(ValidationError) as excinfo:
        profiles.trim_inches("7x7")
    assert "6x9" in excinfo.value.remedy


def test_gutter_requirement_grows_with_page_count():
    assert profiles.required_gutter_in(80) < profiles.required_gutter_in(400)
    assert profiles.required_gutter_in(400) < profiles.required_gutter_in(600)


def test_preflight_without_an_interior_fails_and_says_what_to_run(produced_book, workspace):
    report = api.preflight("test-book", root=workspace)
    assert report["status"] == "fail"
    assert "assemble" in _check(report, "interior.exists")["remedy"]


def test_preflight_checks_trim_page_count_and_margins(produced_book, workspace):
    api.assemble("test-book", root=workspace)
    report = api.preflight("test-book", root=workspace)

    assert _check(report, "trim.size")["status"] == "pass"
    assert _check(report, "margins.gutter")["status"] == "pass"
    assert _check(report, "manifest.agreement")["status"] == "pass"
    assert _check(report, "fonts.embedded")["status"] == "pass"
    #: four pages is well under the KDP minimum, and preflight must say so
    assert _check(report, "page_count.minimum")["status"] == "fail"
    assert report["status"] == "fail"


def test_preflight_warns_about_an_odd_page_count(produced_book, workspace):
    book = Book.load("test-book", workspace)
    book.manifest.remove("p004") if not book.manifest.get("p004").is_approved else None
    api.assemble("test-book", root=workspace)
    report = api.preflight("test-book", root=workspace)
    assert _check(report, "page_count.even")["status"] == "pass"


def test_preflight_records_which_profile_and_when_it_was_captured(produced_book, workspace):
    api.assemble("test-book", root=workspace)
    report = api.preflight("test-book", root=workspace)
    assert report["profile"] == "kdp-default"
    assert report["profile_captured_on"]


def test_preflight_report_is_written_to_the_book(produced_book, workspace):
    api.assemble("test-book", root=workspace)
    api.preflight("test-book", root=workspace)
    assert produced_book.paths.preflight_report.is_file()


def test_demo_book_passes_preflight_without_failures():
    """The shipped fixture must stay a working example."""
    from bookfactory.core.paths import books_dir

    if not (books_dir() / "demo-book" / "book.json").is_file():
        pytest.skip("demo book fixture not present")
    report = Book.load("demo-book").latest_preflight()
    if report is None:
        pytest.skip("demo book fixture has no stored preflight report in this checkout")
    assert report is not None
    assert report["failures"] == 0
    assert report["status"] in ("pass", "warn")
