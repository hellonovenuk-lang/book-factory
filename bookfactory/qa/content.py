"""Content QA - the words.

Machine-checkable things only. Whether a joke lands is reported as a human
review item, not guessed at.
"""

from __future__ import annotations

import re

from bookfactory.qa.findings import LayerResult

PLACEHOLDER_RE = re.compile(r"\b(todo|tbd|lorem ipsum|placeholder|xxx+)\b", re.IGNORECASE)
DOUBLED_WORD_RE = re.compile(r"\b(\w+)[ \t]+\1\b", re.IGNORECASE)
SPACED_PUNCT_RE = re.compile(r"[ \t]+[,.;:!?]")

#: Constructions that gave the previous project away as machine-written.
AI_TELLS = (
    (re.compile(r"\bit'?s not (just )?\w+[^.]{0,40}, it'?s\b", re.IGNORECASE),
     "the \"it's not X, it's Y\" construction"),
    (re.compile(r"\b(unlock|leverage|elevate|delve into|navigate the landscape)\b", re.IGNORECASE),
     "corporate/AI vocabulary"),
    (re.compile(r"\b(in today'?s world|at the end of the day|the journey)\b", re.IGNORECASE),
     "filler phrasing"),
    (re.compile(r"\b(\w+), (\w+), and (\w+)\. (And that'?s|That is)\b", re.IGNORECASE),
     "three-part aphorism followed by a summary beat"),
)

REQUIRED_COPY = {
    "chapter_opener": ["heading"],
    "editorial_illustration": ["heading"],
    "text_illustration": ["body"],
    "checklist": ["items"],
    "diagnostic_test": ["items"],
    "comparison": ["columns"],
    "diagram": ["heading"],
    "quote": ["quote"],
    "certificate": ["heading"],
    "closing": ["heading"],
    "front_matter": [],
    "contents": ["items"],
    "activity": ["blocks"],
}

#: Block keys that are structure, not copy, so QA does not read them as words.
_BLOCK_STRUCTURE_KEYS = ("type", "widths", "start", "out_of", "count")


def _block_text(value) -> list[str]:
    """Every string of copy inside activity blocks, however deeply nested
    (tick items, table rows, gauge bands, cycle steps)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _block_text(item)]
    if isinstance(value, dict):
        return [text for key, item in value.items()
                if key not in _BLOCK_STRUCTURE_KEYS for text in _block_text(item)]
    return []


def _copy_text(copy: dict) -> str:
    chunks = []
    for key, value in copy.items():
        if key == "blocks":
            chunks.extend(_block_text(value))
        elif isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    chunks.append(item)
                elif isinstance(item, dict):
                    chunks.extend(str(v) for v in item.values() if isinstance(v, str))
    return "\n".join(chunks)


def banned_phrases(book) -> list[str]:
    """Phrases the operator banned in the voice bible."""
    path = book.paths.voice_bible
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    match = re.search(r"##\s*Banned phrases(.*?)(\n##\s|\Z)", text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    phrases = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if line.startswith("- "):
            phrase = line[2:].strip().strip('"').strip("'")
            if phrase and not PLACEHOLDER_RE.fullmatch(phrase):
                phrases.append(phrase)
    return phrases


def check(book) -> LayerResult:
    result = LayerResult("content")
    banned = banned_phrases(book)
    headings: dict[str, str] = {}
    titles: dict[str, str] = {}
    chapters_with_opener = set()

    for page in book.manifest:
        if not page.spec:
            result.error("content.missing_spec",
                         f"{page.page_id} has no page spec",
                         page_id=page.page_id,
                         remedy=f"Write pages/specs/{page.page_id}.json")
            continue
        try:
            spec = book.read_page_spec(page.page_id)
        except Exception as exc:  # noqa: BLE001
            result.error("content.unreadable_spec", f"{page.page_id}: {exc}", page_id=page.page_id)
            continue

        copy = spec.get("copy") or {}
        for required in REQUIRED_COPY.get(page.type, []):
            value = copy.get(required)
            if not value:
                result.error("content.missing_copy",
                             f"{page.page_id} is a {page.type} page but its spec has no '{required}'",
                             page_id=page.page_id,
                             remedy=f"Add copy.{required} to pages/specs/{page.page_id}.json")

        text = _copy_text(copy)
        if PLACEHOLDER_RE.search(text):
            result.error("content.placeholder",
                         f"{page.page_id} still contains placeholder copy",
                         page_id=page.page_id,
                         remedy="Replace TODO/TBD/placeholder text with the final wording.")

        doubled = DOUBLED_WORD_RE.search(text)
        if doubled:
            result.warn("content.doubled_word",
                        f"{page.page_id} contains a doubled word: '{doubled.group(0)}'",
                        page_id=page.page_id)

        if SPACED_PUNCT_RE.search(text):
            result.warn("content.spacing",
                        f"{page.page_id} has a space before punctuation",
                        page_id=page.page_id)

        for pattern, label in AI_TELLS:
            if pattern.search(text):
                result.warn("content.ai_tell",
                            f"{page.page_id} uses {label}",
                            page_id=page.page_id,
                            remedy="style/voice-bible.md bans this. Rewrite the line.")

        for phrase in banned:
            if phrase.lower() in text.lower():
                result.warn("content.banned_phrase",
                            f"{page.page_id} contains the banned phrase '{phrase}'",
                            page_id=page.page_id,
                            remedy="The voice bible bans this phrase.")

        heading = (copy.get("heading") or "").strip().lower()
        if heading:
            if heading in headings and headings[heading] != page.page_id:
                result.warn("content.duplicate_heading",
                            f"{page.page_id} repeats the heading of {headings[heading]}: "
                            f"'{copy.get('heading')}'",
                            page_id=page.page_id,
                            remedy="Two pages with the same heading is usually a duplicated concept.")
            headings.setdefault(heading, page.page_id)

        title = page.title.strip().lower()
        if title:
            if title in titles and titles[title] != page.page_id:
                result.warn("content.duplicate_title",
                            f"{page.page_id} has the same title as {titles[title]}: '{page.title}'",
                            page_id=page.page_id)
            titles.setdefault(title, page.page_id)

        source = spec.get("source") or {}
        locked_version = book.state.manuscript.version
        spec_version = source.get("manuscript_version")
        if book.state.manuscript.locked and spec_version and spec_version != locked_version:
            result.warn("content.manuscript_drift",
                        f"{page.page_id} was written against manuscript {spec_version}, "
                        f"the locked manuscript is {locked_version}",
                        page_id=page.page_id,
                        remedy="Re-check the copy against the current locked manuscript.")

        if page.type == "chapter_opener" and page.chapter is not None:
            chapters_with_opener.add(page.chapter)

    for chapter in book.manifest.chapters():
        if chapter not in chapters_with_opener:
            result.warn("content.missing_chapter_opener",
                        f"Chapter {chapter} has pages but no chapter_opener page",
                        remedy="Every chapter normally opens with a chapter_opener page.")

    if len(book.manifest):
        result.findings.append(_human_review(
            "content.human_review",
            "Humour, pacing and whether each page earns its place cannot be machine-checked. "
            "Read the review PDF before approving the book."))
    return result


def _human_review(code: str, message: str):
    from bookfactory.qa.findings import Finding, INFO

    return Finding(INFO, code, message, needs_human=True,
                   remedy="Run `bookfactory review <book>` and read output/review/.")
