"""The one-time intake questionnaire.

A user gives Book Factory a single book idea. Before continuous production can
begin, ChatGPT asks exactly the questions in `QUESTIONNAIRE` - once, near the
start - and persists the answers into the repository. A fresh session must
never need to ask again; it reads `brief/intake.json` and `book.json.intake`
instead.

This module owns the question set and answer validation. It knows nothing
about tasks, gates or rendering.
"""

from __future__ import annotations

HUMOUR_LEVELS = ("mild", "medium", "fairly_savage", "custom")
VISUAL_FEELS = ("classic_editorial_caricature", "old_childrens_book",
                "modern_flat_editorial", "comic_cartoon", "let_book_factory_decide", "custom")
COLOUR_DIRECTIONS = ("muted", "colourful", "specified_palette", "let_book_factory_decide")
MAIN_CHARACTER_SOURCES = ("user_description", "book_factory_invents")
LENGTH_CHOICES = ("60", "80", "100", "system_decides")
PRODUCTION_POLICIES = ("autonomous", "visual_checkpoint", "checkpointed")
PRINT_COLOURS = ("colour", "black_and_white")
COVER_STYLES = ("big_lettering", "picture", "let_book_factory_decide")

#: The compact questionnaire. One entry per user-facing question. Order
#: matches the product spec, and it is deliberately short - this is meant to
#: read as one natural exchange, not a forty-question creative brief.
QUESTIONNAIRE = [
    {"key": "idea", "prompt": "In one or two sentences, what is the book?"},
    {"key": "title", "prompt": "What is the exact title, as it should appear on the cover?"},
    {"key": "buyer", "prompt": "Who will buy it?"},
    {"key": "recipient", "prompt": "Who is it for - the recipient or target reader?"},
    {"key": "recognition_trigger",
     "prompt": "What should make them think \"that's literally him/her\"?"},
    {"key": "humour_level", "prompt": "Humour level: mild, medium, fairly savage, or custom?",
     "choices": HUMOUR_LEVELS},
    {"key": "visual_feel",
     "prompt": ("Visual feel: classic editorial caricature, old children's-book illustration, "
                "modern flat editorial, comic/cartoon, let Book Factory decide, or custom?"),
     "choices": VISUAL_FEELS},
    {"key": "colour_direction",
     "prompt": "Colour direction: muted, colourful, a specified palette, or let Book Factory decide?",
     "choices": COLOUR_DIRECTIONS},
    {"key": "print_colour", "prompt": "Print colour: colour, or black and white?",
     "choices": PRINT_COLOURS},
    {"key": "cover_style",
     "prompt": ("Cover style: big lettering (a text-only cover with bold type and no picture), "
                "a picture cover, or let Book Factory decide?"),
     "choices": COVER_STYLES},
    {"key": "main_character",
     "prompt": "Main character: will you describe them, or should Book Factory invent one?",
     "choices": MAIN_CHARACTER_SOURCES},
    {"key": "main_character_details",
     "prompt": ("The main character's age, who they live with (family), and one or two fixed "
                "look details, e.g. \"Dave, 45, married to Sue, two kids under seven, a flat "
                "cap\". If Book Factory is inventing the character, give the age and family here "
                "anyway.")},
    {"key": "length", "prompt": "Approximate length: 60, 80, 100 pages, or let the system decide?",
     "choices": LENGTH_CHOICES},
    {"key": "must_include", "prompt": "Anything that must be included? (or \"none\")"},
    {"key": "must_avoid", "prompt": "Anything that must be avoided? (or \"none\")"},
    {"key": "production_policy",
     "prompt": ("Production policy: FULL AUTONOMOUS (continue without stopping unless blocked), "
                "VISUAL CHECKPOINT (show visual direction before mass production), or "
                "CHECKPOINTED (ask at every major creative gate)?"),
     "choices": PRODUCTION_POLICIES},
]

#: Keys that must be present and non-empty free text.
_REQUIRED_TEXT_KEYS = ("idea", "title", "buyer", "recipient", "recognition_trigger",
                       "main_character_details", "must_include", "must_avoid")

#: Optional free-text answers a "custom"/"specified_palette"/"user_description"
#: choice implies should also be present. Not enforced - a missing detail here
#: is a judgement call for whoever asks the follow-up, not a hard failure.
_CHOICE_KEYS = {
    "humour_level": HUMOUR_LEVELS,
    "visual_feel": VISUAL_FEELS,
    "colour_direction": COLOUR_DIRECTIONS,
    "main_character": MAIN_CHARACTER_SOURCES,
    "length": LENGTH_CHOICES,
    "print_colour": PRINT_COLOURS,
    "cover_style": COVER_STYLES,
    "production_policy": PRODUCTION_POLICIES,
}


def questionnaire_text() -> str:
    lines = ["Book Factory intake questionnaire:"]
    for index, question in enumerate(QUESTIONNAIRE, start=1):
        lines.append(f"{index}. {question['prompt']}")
    return "\n".join(lines)


def validate_answers(answers: dict) -> list[str]:
    """What is missing or invalid. Empty list means the answers are usable."""
    problems: list[str] = []
    for key in _REQUIRED_TEXT_KEYS:
        value = answers.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"'{key}' is required and must be a non-empty answer")
    for key, choices in _CHOICE_KEYS.items():
        value = str(answers.get(key, "")).strip().lower()
        if value not in choices:
            problems.append(f"'{key}' must be one of {', '.join(choices)}, got {answers.get(key)!r}")
    return problems


def validate_draft(answers: dict, unclear: list[str]) -> list[str]:
    """What is wrong with an agent's draft. Empty list means it can be saved.

    A draft may leave questions out, but only ones it lists as unclear, and
    every answer it does give must be valid. It may never answer
    `production_policy`: that is always the operator's own choice.
    """
    problems: list[str] = []
    keys = {question["key"] for question in QUESTIONNAIRE}
    if "production_policy" in answers:
        problems.append("'production_policy' is the operator's choice and cannot be drafted; "
                        "leave it out and ask the operator")
    for key in unclear:
        if key not in keys:
            problems.append(f"unclear lists {key!r}, which is not a question")
    for key in answers:
        if key not in keys:
            problems.append(f"{key!r} is not a question")
    for key in keys - {"production_policy"}:
        if key in unclear:
            continue
        if key not in answers:
            problems.append(f"'{key}' has no drafted answer; answer it or list it as unclear")
    full = {key: value for key, value in answers.items() if key not in unclear}
    for problem in validate_answers(full):
        key = problem.split("'")[1]
        if key in full:
            problems.append(problem)
    return problems


__all__ = [
    "QUESTIONNAIRE", "HUMOUR_LEVELS", "VISUAL_FEELS", "COLOUR_DIRECTIONS",
    "MAIN_CHARACTER_SOURCES", "LENGTH_CHOICES", "PRODUCTION_POLICIES",
    "PRINT_COLOURS", "COVER_STYLES",
    "questionnaire_text", "validate_answers", "validate_draft",
]
