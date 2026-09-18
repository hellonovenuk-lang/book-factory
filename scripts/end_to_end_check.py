#!/usr/bin/env python3
"""End-to-end check.

Runs a whole book through Book Factory in a temporary directory, including the
failure paths - an illegal overwrite of an approved page, a checksum mismatch,
assembly refusing to proceed - and reports whether each behaved correctly.

    python scripts/end_to_end_check.py

Nothing is written inside the repository. Use this to prove an installation
works, or after changing anything in the production pipeline.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import demo_art  # noqa: E402
import demo_content as content  # noqa: E402

from bookfactory.cli.main import main as cli  # noqa: E402

BOOK = "e2e"
RESULTS: list[tuple[str, bool, str]] = []

SPECS = {
    "p001": {"copy": {"heading": "End To End"},
             "layout": {"show_page_number": False, "show_running_head": False}},
    "p002": {"copy": {"eyebrow": "Chapter one", "heading": "The Assessment",
                      "subheading": "In which the garden is measured.",
                      "body": ["Every garden arrives with the previous owner's opinions "
                               "still in it, and they are now the subject's problem."]}},
    "p003": {"copy": {"eyebrow": "1.1", "heading": "Scope",
                      "body": ["This manual applies to any person who acquired a garden "
                               "without wishing to."],
                      "caption": "Fig. 1.1 - The garden, as inherited."},
             "illustration": {"asset_id": "fig-scope", "concept": "A neglected garden.",
                              "placement": "top", "embedded_text": False}},
    "p004": {"copy": {"quote": "The garden will outlast the subject's interest in it.",
                      "attribution": "Section 2.6"}},
}

PLAN = {"pages": [
    {"title": "Half title", "type": "front_matter"},
    {"title": "The Assessment", "type": "chapter_opener", "chapter": 1},
    {"title": "Scope of the manual", "type": "editorial_illustration", "chapter": 1,
     "required_assets": ["fig-scope"]},
    {"title": "Closing note", "type": "quote", "chapter": 1},
]}

REFERENCES = ["ref-character-main", "ref-character-support", "ref-layout-chapter-opener",
              "ref-page-editorial", "ref-page-diagnostic", "ref-palette"]


def run(root: Path, *argv: str, expect: int = 0) -> int:
    code = cli(["--root", str(root), *argv])
    if code != expect:
        print(f"    ! expected exit {expect}, got {code}: bookfactory {' '.join(argv)}")
    return code


def check(label: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((label, ok, detail))
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}{(' - ' + detail) if detail else ''}")


def step(number: float, title: str) -> None:
    print(f"\n{number:04.1f}. {title}")


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="bookfactory-e2e-"))
    (workspace / "books").mkdir()
    book_dir = workspace / "books" / BOOK
    try:
        return _run(workspace, book_dir)
    finally:
        _force_remove(workspace)


def _run(workspace: Path, book: Path) -> int:  # noqa: C901 - a checklist, read top to bottom
    step(1, "Create the project")
    check("create", run(workspace, "create", "End To End", "--id", BOOK, "--pages", "24") == 0)

    step(2, "Inspect status")
    check("status", run(workspace, "status", BOOK) == 0)

    step(3, "Lock the setup stages")
    (book / "brief" / "brief.md").write_text(content.BRIEF, encoding="utf-8")
    (book / "style" / "voice-bible.md").write_text(content.VOICE_BIBLE, encoding="utf-8")
    (book / "manuscript" / "writing-sample.md").write_text(content.WRITING_SAMPLE, encoding="utf-8")
    (book / "manuscript" / "manuscript.md").write_text(content.MANUSCRIPT, encoding="utf-8")
    (book / "style" / "visual-bible.md").write_text(content.VISUAL_BIBLE, encoding="utf-8")
    for what in ("concept", "voice", "manuscript"):
        run(workspace, "lock", what, BOOK)
    check("visual lock refused before the reference set is approved",
          run(workspace, "lock", "visual", BOOK, expect=6) == 6)

    for reference in REFERENCES:
        run(workspace, "asset", "add", BOOK, reference,
            "--kind", "character_reference", "--title", reference)
        art = workspace / f"art-{reference}.png"
        demo_art.generate(art, width=1800, height=1800, seed=reference)
        run(workspace, "submit", BOOK, reference, "--kind", "asset", "--file", str(art))
        run(workspace, "approve", BOOK, reference, "--kind", "asset", "--by", "operator")
    check("visual lock", run(workspace, "lock", "visual", BOOK) == 0)

    step(4, "Create the page plan")
    plan_file = workspace / "plan.json"
    plan_file.write_text(json.dumps(PLAN), encoding="utf-8")
    check("plan", run(workspace, "plan", BOOK, "--from-file", str(plan_file),
                      "--front-matter", "1") == 0)

    step(5, "Submit a draft asset")
    run(workspace, "asset", "add", BOOK, "fig-scope", "--kind", "illustration",
        "--title", "Scope", "--page", "p003")
    art = workspace / "fig-scope.png"
    demo_art.generate(art, width=1800, height=1350, seed="fig-scope")
    check("submit", run(workspace, "submit", BOOK, "fig-scope", "--kind", "asset",
                        "--file", str(art), "--source", "chatgpt-image") == 0)

    step(6, "Approve the asset")
    check("approve", run(workspace, "approve", BOOK, "fig-scope", "--kind", "asset",
                         "--by", "operator") == 0)

    step(7, "Verify checksums")
    check("validate", run(workspace, "validate", BOOK) == 0)

    for page_id, spec in SPECS.items():
        spec_file = workspace / f"spec-{page_id}.json"
        spec_file.write_text(json.dumps(spec), encoding="utf-8")
        run(workspace, "spec", BOOK, page_id, "--from-file", str(spec_file))
        run(workspace, "render", BOOK, "--page", page_id, "--submit")
        run(workspace, "approve", BOOK, page_id, "--kind", "page", "--by", "operator")
    check("four pages rendered and approved", True)

    step(8, "Attempt an illegal overwrite, then tamper with an approved page")
    approved = book / "pages" / "approved" / "p002-the-assessment.pdf"
    check("approved file is read-only", not os.stat(approved).st_mode & stat.S_IWUSR)
    check("submitting over approved work is refused",
          run(workspace, "submit", BOOK, "p002", "--kind", "page",
              "--file", str(art), expect=7) == 7)
    check("approving again without a revision is refused",
          run(workspace, "approve", BOOK, "p002", "--kind", "page", expect=7) == 7)

    step(8.5, "Submit artwork that fails a hard constraint")
    undersized = workspace / "undersized.png"
    demo_art.generate(undersized, width=600, height=600, seed="undersized")
    run(workspace, "revise", BOOK, "fig-scope", "--kind", "asset", "--reason", "smoke test")
    run(workspace, "submit", BOOK, "fig-scope", "--kind", "asset", "--file", str(undersized))
    registry = json.loads((book / "assets" / "registry.json").read_text())
    asset = next(a for a in registry["assets"] if a["asset_id"] == "fig-scope")
    failing = next(d for d in asset["drafts"] if d["revision"] == "v2")
    check("the failing draft is kept", (book / failing["path"]).is_file())
    check("the failure is recorded", bool(failing["constraint_failures"]),
          failing["constraint_failures"][0]["constraint"] if failing["constraint_failures"] else "")
    check("approval is refused",
          run(workspace, "approve", BOOK, "fig-scope", "--kind", "asset", expect=12) == 12)
    run(workspace, "reject", BOOK, "fig-scope", "--kind", "asset", "--draft", "v2",
        "--reason", "too small")
    registry = json.loads((book / "assets" / "registry.json").read_text())
    asset = next(a for a in registry["assets"] if a["asset_id"] == "fig-scope")
    check("status after rejection reports the canonical approved state",
          asset["status"] == "approved" and asset["revision_open"] is True,
          f"status={asset['status']} revision_open={asset['revision_open']}")
    art_good = workspace / "fig-scope-v3.png"
    demo_art.generate(art_good, width=1800, height=1350, seed="fig-scope-v3")
    run(workspace, "submit", BOOK, "fig-scope", "--kind", "asset", "--file", str(art_good))
    run(workspace, "approve", BOOK, "fig-scope", "--kind", "asset", "--by", "operator")
    run(workspace, "render", BOOK, "--page", "p003", "--submit")
    run(workspace, "approve", BOOK, "p003", "--kind", "page", "--by", "operator")
    check("a corrected resubmission goes through", run(workspace, "validate", BOOK) == 0)

    original = approved.read_bytes()
    os.chmod(approved, 0o644)
    approved.write_bytes(b"%PDF-1.4 this is not the approved page")
    check("validate detects the tamper", run(workspace, "validate", BOOK, expect=1) == 1)
    check("assembly refuses a tampered page",
          run(workspace, "assemble", BOOK, expect=9) == 9)
    approved.write_bytes(original)
    os.chmod(approved, 0o444)
    check("validate is clean once restored", run(workspace, "validate", BOOK) == 0)

    step(9, "Open a revision")
    check("revise", run(workspace, "revise", BOOK, "p002",
                        "--reason", "Standfirst needs tightening") == 0)
    manifest = json.loads((book / "pages" / "manifest.json").read_text())
    page = next(p for p in manifest["pages"] if p["page_id"] == "p002")
    check("approved version stays canonical during a revision",
          page["approved"] is not None and page["revision_open"] is True)

    step(10, "Approve the revision")
    spec = dict(SPECS["p002"])
    spec["copy"] = dict(spec["copy"])
    spec["copy"]["subheading"] = "In which the garden is measured, twice."
    spec_file = workspace / "spec-p002.json"
    spec_file.write_text(json.dumps(spec), encoding="utf-8")
    run(workspace, "spec", BOOK, "p002", "--from-file", str(spec_file))
    run(workspace, "render", BOOK, "--page", "p002", "--submit")
    check("approve revision",
          run(workspace, "approve", BOOK, "p002", "--kind", "page", "--by", "operator") == 0)
    history = list((book / "pages" / "approved" / "_history").glob("p002-*"))
    check("previous approval archived, not deleted", len(history) == 1,
          history[0].name if history else "nothing archived")

    step(11, "Run QA")
    check("qa", run(workspace, "qa", BOOK) == 0)

    step(12, "Assemble")
    check("assemble", run(workspace, "assemble", BOOK) == 0)
    interior = book / "output" / "interior.pdf"
    check("interior.pdf exists", interior.is_file())

    from pypdf import PdfReader

    reader = PdfReader(str(interior))
    check("interior has one page per manifest page", len(reader.pages) == 4,
          f"{len(reader.pages)} pages")
    box = reader.pages[0].mediabox
    check("pages are 6x9in", abs(float(box.width) - 432) < 1 and abs(float(box.height) - 648) < 1,
          f"{float(box.width):.0f}x{float(box.height):.0f}pt")

    step(13, "Generate review output")
    check("review", run(workspace, "review", BOOK) == 0)
    check("contact sheet exists",
          (book / "output" / "review" / "full-book-contact-sheet.pdf").is_file())

    step(14, "Run KDP preflight")
    #: four pages is far below the KDP minimum, so a failure here is correct
    check("preflight runs and fails on page count",
          run(workspace, "preflight", BOOK, expect=1) == 1)
    report = json.loads((book / "output" / "kdp-preflight.json").read_text())
    failures = [c["check"] for c in report["checks"] if c["status"] == "fail"]
    check("the only failure is the page count", failures == ["page_count.minimum"],
          ", ".join(failures))

    step(15, "Ask what happens next")
    check("next", run(workspace, "next", BOOK) == 0)

    step(16, "Final state")
    check("status", run(workspace, "status", BOOK) == 0)
    check("json status", run(workspace, "--json", "status", BOOK) == 0)

    failed = [label for label, ok, _ in RESULTS if not ok]
    print("\n" + "=" * 60)
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    for label in failed:
        print(f"  FAILED: {label}")
    return 1 if failed else 0


def _force_remove(path: Path) -> None:
    for item in path.rglob("*"):
        if item.is_file():
            os.chmod(item, stat.S_IWUSR | stat.S_IRUSR)
    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
