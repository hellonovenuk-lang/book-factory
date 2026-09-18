"""QA orchestration and reporting."""

from __future__ import annotations

from pathlib import Path

from bookfactory import SCHEMA_VERSION
from bookfactory.core import clock, schema
from bookfactory.core.jsonio import write_json
from bookfactory.qa import assembly as assembly_layer
from bookfactory.qa import content as content_layer
from bookfactory.qa import technical as technical_layer
from bookfactory.qa import visual as visual_layer
from bookfactory.qa.findings import LayerResult

LAYERS = {
    "content": content_layer.check,
    "visual": visual_layer.check,
    "technical": technical_layer.check,
    "assembly": assembly_layer.check,
}

#: QA layer to the manifest field it stamps on each page.
PAGE_QA_FIELDS = ("content", "visual", "technical")


def run_qa(book, *, layers: list[str] | None = None, write_report: bool = True) -> dict:
    selected = layers or list(LAYERS)
    results: list[LayerResult] = []
    for name in selected:
        if name not in LAYERS:
            raise ValueError(f"Unknown QA layer {name!r}. Available: {', '.join(LAYERS)}")
        results.append(LAYERS[name](book))

    errors = sum(len(r.errors) for r in results)
    warnings = sum(len(r.warnings) for r in results)
    human = sorted({f.message for r in results for f in r.findings if f.needs_human})
    status = "fail" if errors else ("warn" if warnings else "pass")

    report = {
        "schema_version": SCHEMA_VERSION,
        "book_id": book.state.book_id,
        "run_at": clock.timestamp(),
        "layers": [r.to_dict() for r in results],
        "summary": {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "human_review_required": human,
        },
    }
    schema.validate("qa-report", report, context="qa report")

    _stamp_pages(book, results, selected)

    if write_report:
        stamp = clock.compact_timestamp()
        write_json(book.paths.qa_reports_dir / f"{stamp}-qa.json", report)
        write_json(book.paths.qa_latest, report)
        book.log("qa_run", status=status, errors=errors, warnings=warnings,
                 layers=selected)
        book.save()
    return report


def _stamp_pages(book, results: list[LayerResult], selected: list[str]) -> None:
    """Record each layer's verdict on the page it concerns, so the manifest
    shows QA state per page without anyone opening a report."""
    by_layer = {r.layer: r for r in results}
    for layer in PAGE_QA_FIELDS:
        if layer not in selected:
            continue
        result = by_layer.get(layer)
        if result is None:
            continue
        verdicts: dict[str, str] = {}
        for finding in result.findings:
            if not finding.page_id:
                continue
            current = verdicts.get(finding.page_id, "pass")
            if finding.level == "error":
                verdicts[finding.page_id] = "fail"
            elif finding.level == "warning" and current != "fail":
                verdicts[finding.page_id] = "warn"
        for page in book.manifest:
            page.qa[layer] = verdicts.get(page.page_id, "pass")


def latest_report(book) -> dict | None:
    path: Path = book.paths.qa_latest
    if not path.is_file():
        return None
    from bookfactory.core.jsonio import read_json

    return read_json(path)
