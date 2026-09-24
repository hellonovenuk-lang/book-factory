"""Turn a manuscript into page-plan pages.

A manuscript written in Book Factory's markdown conventions (the Golf
Addict's Guide's `manuscript/manuscript.md` is the reference) maps to the
same plan-file shape `bookfactory plan <book> --from-file` accepts: a list of
pages, each with its title, type, chapter and spec. Page ids, the schema
version, the book id and the spec's `source` are left out; `plan_pages` and
`write_page_spec` add them.

The conventions:

* `## Front matter` and `## Back matter` hold unnumbered sections. Every
  other `##` heading is a chapter, numbered from 1 in order.
* Each `###` heading is one page. Nothing is split here: a section that
  overflows its page is split later, when pages are fit-tested.
* `### Title page` (front matter) is the title page, `### Contents` is the
  contents page, `### Chapter opener` is the chapter's opener: its first line
  repeats the chapter heading, then a standfirst, then body paragraphs, and a
  `[Picture: ...]` note for the opener's artwork.
* `### No. NN · Kind: Title` is a numbered activity panel. Its first
  paragraph is the instructions; numbered statements with a
  `Score: ____ out of N` line become tick boxes and a score box; `- [ ]`
  lists become checklists; markdown tables become tables; `Label: ____` lines
  become signature or write-in lines.
* An ordinary `###` section of plain paragraphs is a text page. One that also
  holds a case note (`> **Case notes ...** text`), a list, a table or a
  `[Typeset diagram: ...]` becomes an unnumbered activity page built from
  blocks.
* A one-paragraph section directly before a numbered panel is that panel's
  introduction: its heading becomes the panel page's eyebrow and its
  paragraph the page's intro body.
* A section headed `Certificate ...` (or marked `[Bordered ...]`) is a
  certificate: paragraphs as its body, `Label: ____` lines as its signature
  lines.

Anything the parser cannot map confidently is still kept, as prose on the
page it belongs to, and named in `warnings`.

This module is pure: it reads text and returns data. It writes nothing and
loads no book.
"""

from __future__ import annotations

import re
from pathlib import Path

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_PANEL = re.compile(r"^No\.\s*(\d+)\s*[·•|\-–—]\s*([^:]+?)\s*:\s*(.+)$")
_NOTE = re.compile(r"^\[(.+)\]$", re.DOTALL)
_SCORE = re.compile(r"^(?:\*\*)?(Score|Points|Total)(?:\*\*)?\s*:?\s*_{2,}\s*out of\s*(\d+)\.?$",
                    re.IGNORECASE)
_FIELD = re.compile(r"([^:_]+?)\s*:\s*_{3,}")
_BLANK_LINE = re.compile(r"^_{3,}$")
_BOLD_LEAD = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$", re.DOTALL)
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_NUMBERED = re.compile(r"^(\d+)[.)]\s+(.*)$")
_SUB_ITEM = re.compile(r"^[a-z][.)]\s+")
_CHECK = re.compile(r"^[-*+]\s+\[[ xX]\]\s+(.*)$")
_BULLET = re.compile(r"^[-*+]\s+(.*)$")
_QUOTED = re.compile(r"\"([^\"]+)\"|“([^”]+)”")
_SIGNATURE_WORDS = re.compile(r"sign|witness|date", re.IGNORECASE)
_ORDINAL_PREFIX = re.compile(
    r"^([A-Za-z]+)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b",
    re.IGNORECASE)

FRONT_MATTER = "front matter"
BACK_MATTER = "back matter"


def parse_manuscript_file(path: str | Path) -> dict:
    """Read a manuscript file and parse it. See `parse_manuscript`."""
    return parse_manuscript(Path(path).read_text(encoding="utf-8"))


def parse_manuscript(text: str) -> dict:
    """Parse a manuscript into `{"pages": [...], "warnings": [...]}`.

    Each page is a plan-file entry: `{"title", "type", "chapter", "spec"}`,
    the spec holding `type`, `title`, `chapter`, `copy` and `illustration`.
    """
    warnings: list[str] = []
    parts = _split_parts(_COMMENT.sub("", text), warnings)
    pages: list[dict] = []
    for part in parts:
        sections = part["sections"]
        index = 0
        while index < len(sections):
            section = sections[index]
            where = _where(part, section["title"])
            elements = _elements(section["lines"])
            if not elements:
                warnings.append(f"{where}: the section is empty, so no page was planned for it.")
                index += 1
                continue
            following = sections[index + 1] if index + 1 < len(sections) else None
            if (following is not None and _panel_heading(following["title"])
                    and not _panel_heading(section["title"])
                    and len(elements) == 1 and elements[0][0] == "para"
                    and not _NOTE.match(elements[0][1])):
                intro = {"eyebrow": section["title"], "body": [_plain(elements[0][1])]}
                pages.append(_page_for(part, following, warnings, intro=intro))
                index += 2
                continue
            pages.append(_page_for(part, section, warnings, elements=elements))
            index += 1
    return {"pages": pages, "warnings": warnings}


# ---------------------------------------------------------------------------
# Splitting into parts (## headings) and sections (### headings)


def _split_parts(text: str, warnings: list[str]) -> list[dict]:
    parts: list[dict] = []
    preamble: list[str] = []
    current = None
    chapter = 0
    for line in text.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        level = len(heading.group(1)) if heading else 0
        if level == 2:
            name = heading.group(2).strip()
            kind = name.lower()
            if kind in (FRONT_MATTER, BACK_MATTER):
                number = None
            else:
                chapter += 1
                number = chapter
                kind = "chapter"
            current = {"name": name, "kind": kind, "chapter": number,
                       "sections": [], "lead": []}
            parts.append(current)
            continue
        if level == 3 and current is not None:
            current["sections"].append({"title": heading.group(2).strip(), "lines": []})
            continue
        if current is None:
            if level != 1:
                preamble.append(line)
            continue
        target = current["sections"][-1]["lines"] if current["sections"] else current["lead"]
        target.append(line)

    leftover = _without_template_note(preamble)
    if leftover.strip():
        warnings.append("Text before the first ## heading belongs to no chapter; "
                        "it was put on a page titled \"Notes\" at the front.")
        parts.insert(0, {"name": "Notes", "kind": FRONT_MATTER, "chapter": None,
                         "sections": [{"title": "Notes", "lines": leftover.splitlines()}],
                         "lead": []})
    for part in parts:
        if any(line.strip() for line in part["lead"]):
            title = f"{part['name']} (introduction)"
            warnings.append(f"## {part['name']}: text sits under the ## heading before any "
                            f"### section; it was put on its own page, \"{title}\".")
            part["sections"].insert(0, {"title": title, "lines": part["lead"]})
    return parts


def _without_template_note(lines: list[str]) -> str:
    """The preamble minus the manuscript template's own blockquote note."""
    text = "\n".join(lines)
    blocks = [block for block in re.split(r"\n\s*\n", text) if block.strip()]
    kept = [block for block in blocks
            if not block.strip().startswith("> The manuscript. Locked by")]
    return "\n\n".join(kept)


def _where(part: dict, title: str) -> str:
    return f"\"### {title}\" in \"## {part['name']}\""


def _panel_heading(title: str):
    return _PANEL.match(title)


# ---------------------------------------------------------------------------
# Elements: the markdown inside one section


def _elements(lines: list[str]) -> list[tuple]:
    """Group a section's lines into ("para" | "bullets" | "checks" | "numbered"
    | "table" | "quote", value) elements, in order."""
    elements: list[tuple] = []
    buffer: list[str] = []
    kind = None

    def flush():
        nonlocal buffer, kind
        if buffer:
            elements.append(_element(kind, buffer))
        buffer, kind = [], None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        indented = line[:1] in (" ", "\t")
        if stripped.startswith("|"):
            line_kind = "table"
        elif stripped.startswith(">"):
            line_kind = "quote"
        elif _CHECK.match(stripped) and not indented:
            line_kind = "checks"
        elif _BULLET.match(stripped) and not indented:
            line_kind = "bullets"
        elif _NUMBERED.match(stripped) and not indented:
            line_kind = "numbered"
        elif indented and kind in ("numbered", "bullets", "checks"):
            buffer.append(line)
            continue
        else:
            line_kind = "para"
        if line_kind != kind:
            flush()
            kind = line_kind
        buffer.append(line)
    flush()
    return elements


def _element(kind: str, lines: list[str]) -> tuple:
    if kind == "table":
        rows = []
        for line in lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            filled = [cell for cell in cells if cell]
            if filled and all(re.fullmatch(r":?-{3,}:?", cell) for cell in filled):
                continue  # the |---|---| separator; an all-blank row is a write-in row
            rows.append(cells)
        return ("table", rows)
    if kind == "quote":
        return ("quote", _join([re.sub(r"^\s*>\s?", "", line) for line in lines]))
    if kind in ("checks", "bullets"):
        pattern = _CHECK if kind == "checks" else _BULLET
        return (kind, _list_items(lines, pattern))
    if kind == "numbered":
        items = []
        for line in lines:
            match = _NUMBERED.match(line.strip())
            if match and not line[:1].isspace():
                items.append({"text": match.group(2).strip(), "subs": []})
            elif _SUB_ITEM.match(line.strip()):
                items[-1]["subs"].append(line.strip())
            elif items[-1]["subs"]:
                items[-1]["subs"][-1] += " " + line.strip()
            else:
                items[-1]["text"] += " " + line.strip()
        return ("numbered", items)
    return ("para", _join(lines))


def _list_items(lines: list[str], pattern) -> list[str]:
    items: list[str] = []
    for line in lines:
        match = pattern.match(line.strip())
        if match and not line[:1].isspace():
            items.append(match.group(1).strip())
        else:
            items[-1] += " " + line.strip()
    return items


def _join(lines: list[str]) -> str:
    return " ".join(line.strip() for line in lines if line.strip())


def _plain(text: str) -> str:
    """Copy as it is typeset: markdown bold markers removed."""
    return _BOLD.sub(r"\1", text).strip()


def _note(element: tuple) -> str | None:
    if element[0] != "para":
        return None
    match = _NOTE.match(element[1].strip())
    return match.group(1).strip() if match else None


def _fields(text: str) -> list[str] | None:
    """`Signed: ____ Date: ____` -> ["Signed", "Date"]; None if not a field line."""
    labels = [_plain(label).strip() for label in _FIELD.findall(text)]
    if not labels or _FIELD.sub("", text).strip(" _"):
        return None
    return labels


# ---------------------------------------------------------------------------
# Pages


def _page_for(part: dict, section: dict, warnings: list[str], *,
              elements: list[tuple] | None = None, intro: dict | None = None) -> dict:
    title = section["title"]
    where = _where(part, title)
    if elements is None:
        elements = _elements(section["lines"])
    lowered = title.lower()
    panel = _panel_heading(title)
    if part["kind"] == FRONT_MATTER and lowered == "title page":
        page = _title_page(title, elements, where, warnings)
    elif lowered in ("contents", "table of contents"):
        page = _contents_page(title, elements, where, warnings)
    elif lowered == "chapter opener":
        if part["kind"] == "chapter":
            page = _chapter_opener(part, elements, where, warnings)
        else:
            warnings.append(f"{where}: a chapter opener outside a chapter; "
                            "planned as an ordinary page.")
            page = _general_page(title, elements, where, warnings)
    elif panel:
        page = _panel_page(panel, elements, where, warnings)
    elif _is_certificate(title, elements):
        page = _certificate_page(title, elements, where, warnings)
    else:
        page = _general_page(title, elements, where, warnings)
    if intro:
        page["copy"].update(intro)
    chapter = part["chapter"]
    spec = {"type": page["type"], "title": page["title"], "chapter": chapter,
            "copy": page["copy"], "illustration": page.get("illustration")}
    return {"title": page["title"], "type": page["type"], "chapter": chapter, "spec": spec}


def _title_page(title, elements, where, warnings) -> dict:
    texts = _texts(elements, where, warnings)
    copy: dict = {}
    if texts:
        copy["heading"] = texts[0]
    if len(texts) > 1:
        copy["subheading"] = texts[1]
    if len(texts) > 2:
        copy["body"] = texts[2:]
    return {"type": "front_matter", "title": title, "copy": copy}


def _contents_page(title, elements, where, warnings) -> dict:
    items: list[str] = []
    other: list[tuple] = []
    for element in elements:
        if element[0] in ("bullets", "checks"):
            items.extend(_plain(item) for item in element[1])
        elif element[0] == "numbered":
            items.extend(_plain(item["text"]) for item in element[1])
        else:
            other.append(element)
    copy: dict = {"heading": title, "items": items}
    if other:
        warnings.append(f"{where}: a contents page holds only a list of entries; the other "
                        "text was kept in the page's body, which the contents layout does "
                        "not print.")
        copy["body"] = _texts(other, where, warnings)
    return {"type": "contents", "title": title, "copy": copy}


def _chapter_opener(part, elements, where, warnings) -> dict:
    name = part["name"]
    eyebrow, heading = _split_chapter_name(name)
    illustration = None
    texts: list[str] = []
    for element in elements:
        note = _note(element)
        if note and note.lower().startswith("picture:") and illustration is None:
            concept = note.split(":", 1)[1].strip()
            concept = re.sub(r"^chapter opener\.\s*", "", concept, flags=re.IGNORECASE)
            illustration = {"asset_id": _opener_asset_id(part), "concept": concept,
                            "placement": "inline"}
            continue
        if note and note.lower().startswith("picture:"):
            warnings.append(f"{where}: a second [Picture: ...] on one chapter opener; only "
                            "the first became artwork, the second was kept as text.")
        texts.extend(_texts([element], where, warnings))
    if texts and texts[0] == _plain(name):
        texts = texts[1:]
    copy: dict = {"eyebrow": eyebrow, "heading": heading}
    if texts:
        copy["subheading"] = texts[0]
    copy["body"] = texts[1:]
    if illustration is None:
        warnings.append(f"{where}: the chapter opener has no [Picture: ...] note, so no "
                        "opener artwork was planned.")
    return {"type": "chapter_opener", "title": name, "copy": copy,
            "illustration": illustration}


def _split_chapter_name(name: str) -> tuple[str | None, str]:
    if ":" in name:
        eyebrow, heading = name.split(":", 1)
        return eyebrow.strip(), heading.strip()
    return None, name


def _opener_asset_id(part: dict) -> str:
    """`art-stage-01-opener` for "Stage One: ...", `art-chapter-02-opener`
    for "Chapter 2 - ..." or a chapter with no numbered prefix."""
    match = _ORDINAL_PREFIX.match(part["name"])
    word = match.group(1).lower() if match else "chapter"
    word = re.sub(r"[^a-z0-9]+", "-", word).strip("-") or "chapter"
    return f"art-{word}-{part['chapter']:02d}-opener"


def _is_certificate(title: str, elements: list[tuple]) -> bool:
    if title.lower().startswith("certificate"):
        return True
    return any((_note(e) or "").lower().startswith("bordered") for e in elements)


def _certificate_page(title, elements, where, warnings) -> dict:
    body: list[str] = []
    items: list[str] = []
    for element in elements:
        note = _note(element)
        if note and (note.lower().startswith("bordered") or "certificate" in note.lower()):
            continue
        if element[0] == "para":
            labels = _fields(element[1])
            if labels:
                items.extend(labels)
                continue
            if _plain(element[1]) == title and not body:
                continue
        body.extend(_texts([element], where, warnings))
    return {"type": "certificate", "title": title,
            "copy": {"heading": title, "body": body, "items": items}}


def _general_page(title, elements, where, warnings) -> dict:
    if all(element[0] == "para" and not _note(element) and not _fields(element[1])
           for element in elements):
        return {"type": "text_illustration", "title": title,
                "copy": {"heading": title, "body": [_plain(e[1]) for e in elements]}}
    blocks = _blocks(elements, where, warnings, panel=False)
    return {"type": "activity", "title": title, "copy": {"heading": title, "blocks": blocks}}


def _panel_page(match, elements, where, warnings) -> dict:
    number, kind, heading = match.group(1), match.group(2).strip(), match.group(3).strip()
    copy: dict = {"panel_number": f"No. {int(number):02d}", "panel_kind": kind,
                  "heading": heading}
    rest = elements
    if (len(elements) > 1 and elements[0][0] == "para" and not _note(elements[0])
            and not _fields(elements[0][1]) and not _SCORE.match(elements[0][1].strip())):
        copy["instructions"] = _plain(elements[0][1])
        rest = elements[1:]
    copy["blocks"] = _blocks(rest, where, warnings, panel=True)
    if not copy["blocks"]:
        warnings.append(f"{where}: the panel has nothing but its instructions; they were "
                        "kept as the panel's only paragraph.")
        copy["blocks"] = [{"type": "prose", "text": copy.pop("instructions")}]
    return {"type": "activity", "title": heading, "copy": copy}


# ---------------------------------------------------------------------------
# Blocks


def _blocks(elements: list[tuple], where: str, warnings: list[str], *, panel: bool) -> list[dict]:
    blocks: list[dict] = []
    index = 0
    while index < len(elements):
        element = elements[index]
        kind, value = element
        nxt = elements[index + 1] if index + 1 < len(elements) else None
        note = _note(element)

        if note is not None:
            consumed = _note_block(note, nxt, elements, index, blocks, where, warnings)
            index += consumed
            continue

        if kind == "para":
            text = value.strip()
            score = _SCORE.match(text)
            if score:
                blocks.append({"type": "score", "label": score.group(1).capitalize(),
                               "out_of": int(score.group(2))})
            elif _fields(text):
                blocks.extend(_field_blocks(_fields(text)))
            else:
                blocks.append({"type": "prose", "text": _plain(text)})
        elif kind == "checks":
            blocks.append({"type": "checklist", "items": [_plain(i) for i in value]})
        elif kind == "bullets":
            blocks.append({"type": "prose", "text": [f"• {_plain(i)}" for i in value]})
        elif kind == "table":
            blocks.append(_table_block(value))
        elif kind == "quote":
            blocks.append(_quote_block(value, where, warnings))
        elif kind == "numbered":
            blocks.extend(_numbered_blocks(value, nxt, panel))
        index += 1
    return blocks


def _note_block(note, nxt, elements, index, blocks, where, warnings) -> int:
    """Map one [bracket note]; return how many elements it used."""
    lowered = note.lower()
    if lowered.startswith("typeset diagram:"):
        description = note.split(":", 1)[1].strip()
        if "gauge" in description.lower():
            bands = _gauge_bands(nxt)
            if bands:
                blocks.append({"type": "gauge", "bands": bands})
                return 2
            warnings.append(f"{where}: a gauge diagram needs a list of \"**range:** label\" "
                            "bands straight after it; none was found, so the diagram note "
                            "was kept as text.")
        elif "cycle" in description.lower():
            steps = _cycle_steps(description)
            if len(steps) >= 2:
                blocks.append({"type": "cycle", "steps": steps})
                return 1
            warnings.append(f"{where}: a cycle diagram needs its steps in quotation marks; "
                            "fewer than two were found, so the diagram note was kept as text.")
        else:
            warnings.append(f"{where}: unrecognised typeset diagram (only a gauge or a cycle "
                            "can be built); the note was kept as text: [" + note + "]")
        blocks.append({"type": "prose", "text": f"[{note}]"})
        return 1
    if "cut-out" in lowered or "cutout" in lowered:
        card: dict = {"type": "cutout"}
        text: list[str] = []
        used = 1
        for element in elements[index + 1:]:
            if element[0] != "para" or _note(element) or _fields(element[1]):
                break
            bold = _BOLD_LEAD.match(element[1].strip())
            if not text and "heading" not in card and bold and not bold.group(2).strip():
                card["heading"] = bold.group(1).strip()
            else:
                text.append(_plain(element[1]))
            used += 1
        card["text"] = text
        blocks.append(card)
        return used
    if lowered.startswith("picture:"):
        warnings.append(f"{where}: a picture outside a chapter opener was not planned as "
                        "artwork (the picture budget allows chapter openers only by "
                        "default); its note was kept as text: [" + note + "]")
    else:
        warnings.append(f"{where}: unrecognised layout note; it was kept as text: [{note}]")
    blocks.append({"type": "prose", "text": f"[{note}]"})
    return 1


def _gauge_bands(element) -> list[dict] | None:
    if not element or element[0] != "bullets":
        return None
    bands = []
    for item in element[1]:
        match = re.match(r"^\*\*(.+?):?\*\*:?\s*(.+)$", item.strip(), re.DOTALL)
        if not match:
            return None
        bands.append({"range": match.group(1).strip().rstrip(":"),
                      "label": _plain(match.group(2))})
    return bands


def _cycle_steps(description: str) -> list[str]:
    steps = [a or b for a, b in _QUOTED.findall(description)]
    if len(steps) > 2 and steps[-1] == steps[0]:
        steps = steps[:-1]
    return steps


def _field_blocks(labels: list[str]) -> list[dict]:
    if any(_SIGNATURE_WORDS.search(label) for label in labels):
        return [{"type": "signature", "fields": labels}]
    return [{"type": "lines", "count": 1, "label": label} for label in labels]


def _table_block(rows: list[list[str]]) -> dict:
    headers = [_plain(cell) for cell in rows[0]] if rows else []
    width = len(headers)
    body = []
    for row in rows[1:]:
        cells = [_plain(cell) for cell in row]
        cells = (cells + [""] * width)[:width] if width else cells
        body.append(cells)
    return {"type": "table", "headers": headers, "rows": body}


def _quote_block(text: str, where, warnings) -> dict:
    match = _BOLD_LEAD.match(text.strip())
    if match and match.group(2).strip():
        return {"type": "casenote", "label": match.group(1).strip().rstrip("."),
                "text": _plain(match.group(2))}
    warnings.append(f"{where}: a quoted passage with no bold label (\"> **Label.** text\") "
                    "could not be set as a case note; it was kept as a paragraph.")
    return {"type": "prose", "text": _plain(text)}


def _numbered_blocks(items: list[dict], nxt, panel: bool) -> list[dict]:
    if any(item["subs"] for item in items):
        blocks: list[dict] = []
        for number, item in enumerate(items, start=1):
            blocks.append({"type": "prose", "text": f"{number}. {_plain(item['text'])}"})
            if item["subs"]:
                blocks.append({"type": "checklist", "items": [_plain(s) for s in item["subs"]]})
        return blocks
    if all(_BLANK_LINE.match(item["text"].strip()) for item in items):
        return [{"type": "lines", "count": len(items)}]
    followed_by_score = bool(nxt and nxt[0] == "para" and _SCORE.match(nxt[1].strip()))
    if panel or followed_by_score:
        return [{"type": "ticks", "items": [_plain(item["text"]) for item in items]}]
    return [{"type": "prose",
             "text": [f"{n}. {_plain(item['text'])}" for n, item in enumerate(items, start=1)]}]


def _texts(elements: list[tuple], where: str, warnings: list[str]) -> list[str]:
    """Flatten elements to paragraphs of plain text, for page types that hold
    only paragraphs. Anything richer than a paragraph is flattened with a
    warning rather than dropped."""
    texts: list[str] = []
    for kind, value in elements:
        if kind == "para":
            texts.append(_plain(value))
            continue
        warnings.append(f"{where}: this page type holds only paragraphs; a {kind} element "
                        "was flattened into plain paragraphs.")
        if kind in ("bullets", "checks"):
            texts.extend(_plain(item) for item in value)
        elif kind == "numbered":
            for number, item in enumerate(value, start=1):
                texts.append(f"{number}. {_plain(item['text'])}")
                texts.extend(_plain(sub) for sub in item["subs"])
        elif kind == "table":
            texts.extend(" | ".join(_plain(c) for c in row) for row in value)
        elif kind == "quote":
            texts.append(_plain(value))
    return texts
