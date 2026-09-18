"""bookfactory - the Book Factory command line.

Every command is a thin wrapper over bookfactory.core.api. If you find business
logic in this file, it is in the wrong place.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bookfactory import __version__
from bookfactory.cli import output as out
from bookfactory.core import api, stages
from bookfactory.core.book import ASSET, PAGE
from bookfactory.core.errors import BookFactoryError
from bookfactory.core.jsonio import read_json

EPILOG = """\
Typical day:

  bookfactory status <book>      where the book stands
  bookfactory next <book>        exactly what to do next
  bookfactory approve <book> p012 --kind page

Full walkthrough: docs/OPERATOR.md
Agent rules:      AGENTS.md
"""


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bookfactory",
        description="Book Factory - production system for illustrated humour and gift books.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"bookfactory {__version__}")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable output. Use this when an agent is driving.")
    parser.add_argument("--root", help="Repository root (defaults to the one containing books/).")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # -- discovery ------------------------------------------------------
    sub.add_parser("list", help="List every book in this repository.")
    sub.add_parser("stages", help="Show the production stages in order.")
    sub.add_parser("doctor", help="Check that this machine can render and assemble.")

    create = sub.add_parser("create", help="Start a new book project.")
    create.add_argument("title")
    create.add_argument("--id", dest="book_id", help="Book id (default: slug of the title).")
    create.add_argument("--idea", help="One sentence describing the book.")
    create.add_argument("--trim", default="6x9", help="Trim size key (default 6x9).")
    create.add_argument("--bw", action="store_true", help="Black and white interior.")
    create.add_argument("--bleed", action="store_true", help="Interior artwork bleeds off the page.")
    create.add_argument("--dpi", type=int, default=300)
    create.add_argument("--pages", type=int, dest="target_page_count",
                        help="Target page count.")
    create.add_argument("--subtitle")
    create.add_argument("--series")
    create.add_argument("--profile", default="kdp-default", help="KDP profile id.")

    for name, help_text in (
        ("status", "Where the book stands right now."),
        ("next", "The single next action, for a human or an agent."),
        ("validate", "Structural check: schemas, manifest, checksums."),
        ("relock", "Re-apply read-only permissions to approved artefacts."),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("book")

    task = sub.add_parser("task", help="Show a task in full (defaults to the next one).")
    task.add_argument("book")
    task.add_argument("task_id", nargs="?")

    plan = sub.add_parser("plan", help="Create or extend the page plan.")
    plan.add_argument("book")
    plan.add_argument("--from-file", dest="from_file",
                      help="JSON file: a list of pages, or {\"pages\": [...]}.")
    plan.add_argument("--add", action="store_true", help="Add a single page.")
    plan.add_argument("--title")
    plan.add_argument("--type", dest="page_type")
    plan.add_argument("--chapter", type=int)
    plan.add_argument("--assets", nargs="*", default=None, help="Required asset ids.")
    plan.add_argument("--front-matter", type=int, default=0, dest="front_matter",
                      help="How many leading pages carry no printed number.")
    plan.add_argument("--renumber", action="store_true",
                      help="Recompute printed page numbers.")

    spec = sub.add_parser("spec", help="Write a page specification.")
    spec.add_argument("book")
    spec.add_argument("page")
    spec.add_argument("--from-file", dest="from_file", required=True)

    asset = sub.add_parser("asset", help="Manage illustration assets and visual references.")
    asset_sub = asset.add_subparsers(dest="asset_command", metavar="<subcommand>")
    asset_add = asset_sub.add_parser("add", help="Register an asset.")
    asset_add.add_argument("book")
    asset_add.add_argument("asset_id")
    asset_add.add_argument("--kind", default="illustration")
    asset_add.add_argument("--title")
    asset_add.add_argument("--description")
    asset_add.add_argument("--page", dest="page_id")
    asset_add.add_argument("--characters", nargs="*", default=None)
    asset_add.add_argument("--references", nargs="*", default=None)
    asset_list = asset_sub.add_parser("list", help="List registered assets.")
    asset_list.add_argument("book")

    submit = sub.add_parser("submit", help="Register a draft (artwork or rendered page).")
    submit.add_argument("book")
    submit.add_argument("id")
    submit.add_argument("--file", required=True)
    submit.add_argument("--kind", choices=[PAGE, ASSET], default=ASSET)
    submit.add_argument("--revision", help="Force a revision label (default: next free).")
    submit.add_argument("--note")
    submit.add_argument("--source", help="What produced it, e.g. 'chatgpt-image'.")

    approve = sub.add_parser("approve", help="Approve a draft. The only way work becomes canonical.")
    approve.add_argument("book")
    approve.add_argument("id")
    approve.add_argument("--kind", choices=[PAGE, ASSET], default=PAGE)
    approve.add_argument("--draft", dest="revision", help="Which revision (default: latest).")
    approve.add_argument("--by", help="Who approved it.")
    approve.add_argument("--note")

    reject = sub.add_parser("reject", help="Reject a draft. The file is kept.")
    reject.add_argument("book")
    reject.add_argument("id")
    reject.add_argument("--kind", choices=[PAGE, ASSET], default=PAGE)
    reject.add_argument("--draft", dest="revision")
    reject.add_argument("--reason")
    reject.add_argument("--by")

    revise = sub.add_parser("revise", help="Open a revision on approved work.")
    revise.add_argument("book")
    revise.add_argument("id")
    revise.add_argument("--kind", choices=[PAGE, ASSET], default=PAGE)
    revise.add_argument("--reason")
    revise.add_argument("--by")

    lock = sub.add_parser("lock", help="Lock a stage of the book.")
    lock.add_argument("what", choices=sorted(api.LOCKS))
    lock.add_argument("book")
    lock.add_argument("--version")
    lock.add_argument("--by")
    lock.add_argument("--note")

    advance = sub.add_parser("advance", help="Move the book to the next stage.")
    advance.add_argument("book")
    advance.add_argument("--to", choices=stages.ORDER)
    advance.add_argument("--by")
    advance.add_argument("--note")
    advance.add_argument("--force", action="store_true",
                         help="Skip gate checks. Recorded in the audit log.")

    block = sub.add_parser("block", help="Mark the book blocked on an operator decision.")
    block.add_argument("book")
    block.add_argument("reason")
    block.add_argument("--needs")
    unblock = sub.add_parser("unblock", help="Clear the blocked flag.")
    unblock.add_argument("book")

    render = sub.add_parser("render", help="Render pages deterministically from their specs.")
    render.add_argument("book")
    render.add_argument("--page", dest="page_id")
    render.add_argument("--backend", help="weasyprint or chromium.")
    render.add_argument("--submit", action="store_true",
                        help="Also register the render as a draft.")

    qa = sub.add_parser("qa", help="Run quality assurance.")
    qa.add_argument("book")
    qa.add_argument("--layer", action="append", dest="layers",
                    choices=["content", "visual", "technical", "assembly"])

    assemble = sub.add_parser("assemble", help="Build the interior PDF from approved pages.")
    assemble.add_argument("book")
    assemble.add_argument("--out", dest="destination")

    review = sub.add_parser("review", help="Build contact sheets and review PDFs.")
    review.add_argument("book")
    review.add_argument("--no-chapters", action="store_true")
    review.add_argument("--no-contact-sheet", action="store_true")
    review.add_argument("--no-full", action="store_true")

    preflight = sub.add_parser("preflight", help="Check the interior against the KDP profile.")
    preflight.add_argument("book")

    history = sub.add_parser("history", help="Show the audit log.")
    history.add_argument("book")
    history.add_argument("--limit", type=int, default=20)
    history.add_argument("--event")

    return parser


# ----------------------------------------------------------------------
# Command implementations
# ----------------------------------------------------------------------


def cmd_list(args) -> int:
    books = api.list_books(args.root)
    if args.json:
        out.emit_json(books)
        return 0
    if not books:
        print("No books yet. Start one with:  bookfactory create \"Your Title\"")
        return 0
    out.table(
        [[b["book_id"], b["title"] or "", b["stage_label"], b["updated_at"] or ""] for b in books],
        ["id", "title", "stage", "updated"],
    )
    return 0


def cmd_stages(args) -> int:
    data = [{"number": s.number, "key": s.key, "label": s.label, "summary": s.summary,
             "approval_gate": s.approval_gate} for s in stages.STAGES]
    if args.json:
        out.emit_json(data)
        return 0
    for stage in stages.STAGES:
        gate = " (approval gate)" if stage.approval_gate else ""
        print(f"{stage.number:>2}. {out.BOLD}{stage.label}{out.RESET}{gate}")
        print(f"    {out.DIM}{stage.summary}{out.RESET}")
    return 0


def cmd_doctor(args) -> int:
    from bookfactory.render import backends
    from bookfactory.render.templates import page_template_names, templates_root

    available = backends.available_backends()
    report = {
        "version": __version__,
        "render_backends": available,
        "default_backend": available[0] if available else None,
        "templates_root": str(templates_root()),
        "page_templates": page_template_names(),
        "books": [b["book_id"] for b in api.list_books(args.root)],
    }
    try:
        import jsonschema  # noqa: F401  - presence is the whole check

        report["schema_validation"] = True
    except ImportError:
        report["schema_validation"] = False

    if args.json:
        out.emit_json(report)
        return 0 if available else 1

    out.heading("BOOK FACTORY DOCTOR")
    out.blank()
    out.field("version", __version__)
    out.field("templates", report["templates_root"])
    out.field("page types", str(len(report["page_templates"])))
    out.field("schemas", "on" if report["schema_validation"] else
              "off (pip install jsonschema)")
    out.blank()
    if available:
        out.bullet(f"render backends: {', '.join(available)} (using {available[0]})", level="ok")
    else:
        out.bullet("no HTML-to-PDF backend found - pages cannot be rendered", level="error")
    out.bullet(f"books in this repository: {len(report['books'])}", level="info")
    return 0 if available else 1


def cmd_create(args) -> int:
    result = api.create_book(
        args.title,
        book_id=args.book_id,
        root=args.root,
        trim=args.trim,
        colour=not args.bw,
        bleed=args.bleed,
        dpi=args.dpi,
        kdp_profile=args.profile,
        target_page_count=args.target_page_count,
        subtitle=args.subtitle,
        series=args.series,
        idea=args.idea,
    )
    if args.json:
        out.emit_json(result)
        return 0
    out.heading(f"CREATED  {result['book_id']}")
    out.blank()
    out.field("path", result["path"])
    out.field("files", str(len(result["created_files"])))
    out.blank()
    print("Next:")
    out.bullet(result["next_action"]["summary"] if result["next_action"] else "nothing", level="info")
    out.blank()
    print(f"  bookfactory next {result['book_id']}")
    return 0


def cmd_status(args) -> int:
    data = api.status(args.book, root=args.root)
    if args.json:
        out.emit_json(data)
        return 0

    pages = data["pages"]
    out.heading(f"BOOK: {data['title']}")
    out.field("id", data["book_id"])
    out.field("stage", f"{data['stage_number']:02d} {data['stage_label']}")
    out.field("format", f"{data['format']['trim']}, "
                        f"{'colour' if data['format']['colour'] else 'black and white'}"
                        f"{', bleed' if data['format']['bleed'] else ''}")
    out.field("manuscript", f"{data['manuscript']['version']} "
                            f"{'LOCKED' if data['manuscript']['locked'] else 'unlocked'}")
    out.field("voice", f"{data['style']['voice_version']} "
                       f"{'LOCKED' if data['style']['voice_locked'] else 'unlocked'}")
    out.field("visual style", f"{data['style']['visual_version']} "
                              f"{'LOCKED' if data['style']['visual_locked'] else 'unlocked'}")
    out.blank()

    if pages["total"]:
        out.heading("PAGES")
        out.field("planned", str(pages["total"]))
        out.field("approved", str(pages["approved"]))
        out.field("draft", str(pages["draft_submitted"]))
        out.field("not started", str(pages["not_started"]))
        if pages["in_revision"]:
            out.field("in revision", str(pages["in_revision"]))
        out.blank()

    assets = data["assets"]
    if assets["total"]:
        out.heading("ARTWORK")
        out.field("registered", str(assets["total"]))
        out.field("approved", str(assets["approved"]))
        out.field("draft", str(assets["draft_submitted"]))
        out.blank()

    if data["manifest_problems"]:
        out.heading("MANIFEST PROBLEMS")
        for problem in data["manifest_problems"]:
            out.bullet(problem, level="error")
        out.blank()

    if data["approved_integrity"]:
        out.heading("APPROVED ARTEFACT INTEGRITY")
        for problem in data["approved_integrity"]:
            out.bullet(problem, level="error")
        out.blank()

    if data["qa"]:
        out.heading("LAST QA")
        out.field("status", out.status_word(data["qa"]["status"]))
        out.field("errors", str(data["qa"]["errors"]))
        out.field("warnings", str(data["qa"]["warnings"]))
        out.blank()

    if data["blocked"]:
        out.heading("BLOCKED")
        out.bullet(data["blocked"]["reason"], level="error")
        out.blank()

    out.heading("NEXT")
    if data["next_action"]:
        out.bullet(data["next_action"]["summary"], level="info")
        print(f"  {out.DIM}task: {data['next_action']['task_id']}{out.RESET}")
        print(f"  {out.DIM}run:  bookfactory next {data['book_id']}{out.RESET}")
    else:
        out.bullet("nothing outstanding - the book is complete", level="ok")
    return 0


def cmd_next(args) -> int:
    task = api.next_task(args.book, root=args.root)
    if args.json:
        out.emit_json(task)
        return 0
    if task is None:
        out.heading("NEXT ACTION")
        out.blank()
        out.bullet("Nothing outstanding. The book is complete.", level="ok")
        return 0
    _print_task(task)
    return 0


def cmd_task(args) -> int:
    task = api.get_task(args.book, args.task_id, root=args.root)
    if args.json:
        out.emit_json(task)
        return 0
    if task is None:
        print("No open task.")
        return 0
    _print_task(task)
    return 0


def _print_task(task: dict) -> None:
    out.heading("NEXT ACTION")
    out.blank()
    out.field("stage", stages.label(task["stage"]) if task.get("stage") else "-")
    out.field("task", task["task_id"])
    out.field("type", task["type"])
    out.blank()
    print(task["summary"])
    out.blank()
    if task.get("instructions"):
        out.heading("INSTRUCTIONS")
        for line in task["instructions"].splitlines():
            print(f"  {line}")
        out.blank()
    if task.get("scene"):
        out.heading("SCENE")
        print(f"  {task['scene']}")
        out.blank()
    if task.get("characters"):
        out.field("characters", ", ".join(task["characters"]))
    if task.get("references"):
        out.heading("LOCKED REFERENCES TO MATCH")
        for reference in task["references"]:
            out.bullet(reference, level="info")
        out.blank()
    if task.get("required_inputs"):
        out.heading("REQUIRED INPUTS")
        for item in task["required_inputs"]:
            out.bullet(item, level="info")
        out.blank()
    if task.get("constraints"):
        out.heading("CONSTRAINTS")
        for key, value in task["constraints"].items():
            out.bullet(f"{key}: {value}", level="info")
        out.blank()
    if task.get("output"):
        out.heading("OUTPUT EXPECTED")
        for key, value in task["output"].items():
            out.bullet(f"{key}: {value}", level="info")
        out.blank()
    out.field("approval", "REQUIRED" if task.get("approval_required") else "not required")


def cmd_plan(args) -> int:
    pages: list[dict] = []
    if args.from_file:
        data = read_json(Path(args.from_file))
        pages = data["pages"] if isinstance(data, dict) else data
    elif args.add:
        if not (args.title and args.page_type):
            out.error("--add needs --title and --type")
            return 2
        pages = [{"title": args.title, "type": args.page_type, "chapter": args.chapter,
                  "required_assets": args.assets or []}]
    result = api.plan_pages(args.book, pages, root=args.root,
                            renumber=bool(pages) or args.renumber,
                            front_matter_pages=args.front_matter)
    if args.json:
        out.emit_json(result)
        return 0
    out.heading("PAGE PLAN")
    out.field("added", str(len(result["added"])))
    out.field("total pages", str(result["total"]))
    if result["problems"]:
        out.blank()
        out.heading("PROBLEMS")
        for problem in result["problems"]:
            out.bullet(problem, level="error")
        return 1
    return 0


def cmd_spec(args) -> int:
    spec = read_json(Path(args.from_file))
    result = api.write_page_spec(args.book, args.page, spec, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.bullet(f"wrote {result['spec']}", level="ok")
    return 0


def cmd_asset(args) -> int:
    if args.asset_command == "add":
        result = api.register_asset(
            args.book, args.asset_id, root=args.root, kind=args.kind, title=args.title,
            description=args.description, page_id=args.page_id,
            characters=args.characters, references=args.references)
        if args.json:
            out.emit_json(result)
            return 0
        out.bullet(f"registered {result['asset_id']} ({result['kind']})", level="ok")
        return 0

    from bookfactory.core.book import Book

    book = Book.load(args.book, args.root)
    rows = [[a.asset_id, a.kind, a.status,
             a.approved.revision if a.approved else "-",
             "locked" if a.locked else ""] for a in book.registry]
    if args.json:
        out.emit_json([a.to_dict() for a in book.registry])
        return 0
    out.table(rows, ["asset", "kind", "status", "approved", ""])
    return 0


def cmd_submit(args) -> int:
    result = api.submit_asset(args.book, args.id, args.file, kind=args.kind,
                              revision=args.revision, note=args.note, source=args.source,
                              root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.heading("DRAFT SUBMITTED")
    out.field("id", f"{result['id']} ({result['kind']})")
    out.field("revision", result["revision"])
    out.field("path", result["path"])
    out.field("sha256", result["sha256"][:16] + "...")
    out.blank()
    print("  Nothing is approved by silence. When you are happy:")
    print(f"  bookfactory approve {args.book} {result['id']} "
          f"--kind {result['kind']} --draft {result['revision']}")
    return 0


def cmd_approve(args) -> int:
    result = api.approve(args.book, args.id, kind=args.kind, revision=args.revision,
                         by=args.by, note=args.note, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.heading("APPROVED")
    out.field("id", f"{result['id']} ({result['kind']})")
    out.field("revision", result["revision"])
    out.field("canonical", result["path"])
    out.field("sha256", result["sha256"][:16] + "...")
    out.blank()
    out.bullet("This artefact is now immutable. Changing it requires "
               f"`bookfactory revise {args.book} {result['id']}`.", level="info")
    return 0


def cmd_reject(args) -> int:
    result = api.reject(args.book, args.id, kind=args.kind, revision=args.revision,
                        reason=args.reason, by=args.by, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.bullet(f"rejected {result['id']} {result['revision']} (file kept at {result['path']})",
               level="warning")
    return 0


def cmd_revise(args) -> int:
    result = api.revise(args.book, args.id, kind=args.kind, reason=args.reason,
                        by=args.by, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.heading("REVISION OPEN")
    out.field("id", result["id"])
    if result.get("current_revision"):
        out.field("still live", result["current_revision"])
    out.field("next draft", result["next_revision"])
    out.blank()
    out.bullet("The approved version stays canonical until the replacement is approved.",
               level="info")
    return 0


def cmd_lock(args) -> int:
    result = api.lock(args.book, args.what, version=args.version, by=args.by,
                      note=args.note, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.heading(f"LOCKED: {args.what.upper()}")
    out.field("stage", result["stage_label"])
    out.blank()
    if result["next_action"]:
        print("Next: " + result["next_action"]["summary"])
    return 0


def cmd_advance(args) -> int:
    result = api.advance(args.book, args.to, by=args.by, note=args.note,
                         force=args.force, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.bullet(f"stage is now {result['stage_label']}", level="ok")
    return 0


def cmd_block(args) -> int:
    result = api.block(args.book, args.reason, needs=args.needs, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.bullet(f"blocked: {args.reason}", level="warning")
    return 0


def cmd_unblock(args) -> int:
    result = api.unblock(args.book, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.bullet("unblocked", level="ok")
    return 0


def cmd_validate(args) -> int:
    result = api.validate(args.book, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0 if result["ok"] else 1
    out.heading("VALIDATE")
    out.field("pages", str(result["pages"]))
    out.field("assets", str(result["assets"]))
    out.blank()
    if result["ok"]:
        out.bullet("state is structurally sound", level="ok")
        return 0
    for problem in result["problems"]:
        out.bullet(problem, level="error")
    return 1


def cmd_relock(args) -> int:
    result = api.relock(args.book, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.bullet(f"re-locked {result['relocked']} approved artefact(s)", level="ok")
    return 0


def cmd_render(args) -> int:
    result = api.render(args.book, page_id=args.page_id, backend=args.backend,
                        submit=args.submit, root=args.root)
    if args.json:
        out.emit_json(result)
        return 0
    out.heading("RENDERED")
    for entry in result["rendered"]:
        suffix = f" -> draft {entry['draft']}" if entry.get("draft") else ""
        out.bullet(f"{entry['page_id']}: {entry['render']}{suffix}", level="ok")
    return 0


def cmd_qa(args) -> int:
    report = api.qa(args.book, layers=args.layers, root=args.root)
    if args.json:
        out.emit_json(report)
        return 0 if report["summary"]["status"] != "fail" else 1

    out.heading("QUALITY ASSURANCE")
    out.field("status", out.status_word(report["summary"]["status"]))
    out.field("errors", str(report["summary"]["errors"]))
    out.field("warnings", str(report["summary"]["warnings"]))
    out.blank()
    for layer in report["layers"]:
        out.heading(f"{layer['layer'].upper()}  {out.status_word(layer['status'])}")
        findings = [f for f in layer["findings"] if not f["needs_human"]]
        if not findings:
            out.bullet("no machine-detectable problems", level="ok")
        for finding in findings:
            where = f"[{finding['page_id'] or finding['asset_id']}] " if (
                finding["page_id"] or finding["asset_id"]) else ""
            out.bullet(f"{where}{finding['message']}", level=finding["level"])
            if finding["remedy"]:
                print(f"      {out.DIM}{finding['remedy']}{out.RESET}")
        out.blank()

    human = report["summary"]["human_review_required"]
    if human:
        out.heading("NEEDS A HUMAN (OR AN AGENT) TO LOOK")
        for item in human:
            out.bullet(item, level="info")
    return 0 if report["summary"]["status"] != "fail" else 1


def cmd_assemble(args) -> int:
    record = api.assemble(args.book, root=args.root, destination=args.destination)
    if args.json:
        out.emit_json(record)
        return 0
    out.heading("ASSEMBLED")
    out.field("output", record["output"])
    out.field("pages", str(record["page_count"]))
    out.field("sha256", record["output_sha256"][:16] + "...")
    out.field("manuscript", record["manuscript_version"])
    out.field("visual style", record["visual_style_version"])
    out.blank()
    out.bullet("Assembly is mechanical: approved pages only, checksums verified, "
               "nothing regenerated.", level="info")
    return 0


def cmd_review(args) -> int:
    result = api.review(args.book, root=args.root,
                        chapters=not args.no_chapters,
                        contact_sheet=not args.no_contact_sheet,
                        full=not args.no_full)
    if args.json:
        out.emit_json(result)
        return 0
    out.heading("REVIEW OUTPUT")
    for name, path in sorted(result["outputs"].items()):
        out.bullet(f"{name}: {path}", level="ok")
    return 0


def cmd_preflight(args) -> int:
    report = api.preflight(args.book, root=args.root)
    if args.json:
        out.emit_json(report)
        return 0 if report["status"] != "fail" else 1
    out.heading("KDP PREFLIGHT")
    out.field("profile", f"{report['profile']} (captured {report['profile_captured_on']})")
    out.field("status", out.status_word(report["status"]))
    out.blank()
    for check in report["checks"]:
        level = {"pass": "ok", "warn": "warning", "fail": "error"}[check["status"]]
        out.bullet(f"{check['check']}: {check['message']}", level=level)
        if check["remedy"] and check["status"] != "pass":
            print(f"      {out.DIM}{check['remedy']}{out.RESET}")
    return 0 if report["status"] != "fail" else 1


def cmd_history(args) -> int:
    records = api.audit_history(args.book, limit=args.limit, event=args.event, root=args.root)
    if args.json:
        out.emit_json(records)
        return 0
    for record in records:
        detail = " ".join(f"{k}={v}" for k, v in record.items()
                          if k not in ("at", "event"))
        print(f"{out.DIM}{record['at']}{out.RESET}  {out.BOLD}{record['event']}{out.RESET}  {detail}")
    return 0


COMMANDS = {
    "list": cmd_list,
    "stages": cmd_stages,
    "doctor": cmd_doctor,
    "create": cmd_create,
    "status": cmd_status,
    "next": cmd_next,
    "task": cmd_task,
    "plan": cmd_plan,
    "spec": cmd_spec,
    "asset": cmd_asset,
    "submit": cmd_submit,
    "approve": cmd_approve,
    "reject": cmd_reject,
    "revise": cmd_revise,
    "lock": cmd_lock,
    "advance": cmd_advance,
    "block": cmd_block,
    "unblock": cmd_unblock,
    "validate": cmd_validate,
    "relock": cmd_relock,
    "render": cmd_render,
    "qa": cmd_qa,
    "assemble": cmd_assemble,
    "review": cmd_review,
    "preflight": cmd_preflight,
    "history": cmd_history,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    handler = COMMANDS[args.command]
    try:
        return handler(args)
    except BookFactoryError as exc:
        if args.json:
            out.emit_json(exc.to_dict())
        else:
            out.error(exc.message, exc.remedy)
        return exc.exit_code
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
