"""Terminal output helpers.

Human output first: this tool is operated by someone who is not a programmer,
so the default output reads like a production report. `--json` gives agents the
same information with no parsing guesswork.
"""

from __future__ import annotations

import json
import os
import sys

_NO_COLOUR = os.environ.get("NO_COLOR") is not None or not sys.stdout.isatty()

BOLD = "" if _NO_COLOUR else "\033[1m"
DIM = "" if _NO_COLOUR else "\033[2m"
RED = "" if _NO_COLOUR else "\033[31m"
GREEN = "" if _NO_COLOUR else "\033[32m"
YELLOW = "" if _NO_COLOUR else "\033[33m"
BLUE = "" if _NO_COLOUR else "\033[34m"
RESET = "" if _NO_COLOUR else "\033[0m"

STATUS_COLOUR = {"pass": GREEN, "ok": GREEN, "warn": YELLOW, "fail": RED, "error": RED}


def emit_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def heading(text: str) -> None:
    print(f"{BOLD}{text}{RESET}")


def field(label: str, value, *, width: int = 16) -> None:
    print(f"{DIM}{label.upper():<{width}}{RESET}{value}")


def rule(char: str = "-", width: int = 58) -> None:
    print(f"{DIM}{char * width}{RESET}")


def blank() -> None:
    print()


def status_word(status: str) -> str:
    colour = STATUS_COLOUR.get(status, "")
    return f"{colour}{status.upper()}{RESET}"


def bullet(text: str, *, level: str = "info") -> None:
    marker = {"error": f"{RED}x{RESET}", "warning": f"{YELLOW}!{RESET}",
              "ok": f"{GREEN}v{RESET}", "info": f"{DIM}-{RESET}"}.get(level, "-")
    print(f"  {marker} {text}")


def error(message: str, remedy: str | None = None) -> None:
    print(f"{RED}{BOLD}ERROR{RESET} {message}", file=sys.stderr)
    if remedy:
        print(f"{DIM}      {remedy}{RESET}", file=sys.stderr)


def table(rows: list[list[str]], headers: list[str]) -> None:
    if not rows:
        return
    widths = [len(h) for h in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))
    header_line = "  ".join(f"{DIM}{h.upper():<{widths[i]}}{RESET}"
                            for i, h in enumerate(headers))
    print(header_line)
    for row in rows:
        print("  ".join(f"{str(cell):<{widths[i]}}" for i, cell in enumerate(row)))
