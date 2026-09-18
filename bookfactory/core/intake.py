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

#: The compact questionnaire. One entry per user-facing question. Order
#: matches the product spec, and it is deliberately short - this is meant to
#: read as one natural exchange, not a forty-question creative brief.
QUESTIONNAIRE = [
    {"key": "idea", "prompt": "In one or two sentences, what is the book?"},
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
    {"key": "main_character",
     "prompt": "Main character: will you describe them, or should Book Factory invent one?",
     "choices": MAIN_CHARACTER_SOURCES},
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
_REQUIRED_TEXT_KEYS = ("idea", "buyer", "recipient", "recognition_trigger",
                       "must_include", "must_avoid")

#: Optional free-text answers a "custom"/"specified_palette"/"user_description"
#: choice implies should also be present. Not enforced - a missing detail here
#: is a judgement call for whoever asks the follow-up, not a hard failure.
_CHOICE_KEYS = {
    "humour_level": HUMOUR_LEVELS,
    "visual_feel": VISUAL_FEELS,
    "colour_direction": COLOUR_DIRECTIONS,
    "main_character": MAIN_CHARACTER_SOURCES,
    "length": LENGTH_CHOICES,
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


__all__ = [
    "QUESTIONNAIRE", "HUMOUR_LEVELS", "VISUAL_FEELS", "COLOUR_DIRECTIONS",
    "MAIN_CHARACTER_SOURCES", "LENGTH_CHOICES", "PRODUCTION_POLICIES",
    "questionnaire_text", "validate_answers",
]
