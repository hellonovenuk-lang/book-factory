"""Template loading.

Two template families, both plain files in `templates/` at the repository root
so a non-programmer can read and edit them:

* `templates/project/` - the Markdown documents scaffolded into a new book.
* `templates/pages/`   - the HTML page templates the renderer uses.
"""

from __future__ import annotations

import functools
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from bookfactory.core.errors import RenderError


@functools.lru_cache(maxsize=1)
def templates_root() -> Path:
    from bookfactory.core.paths import repo_root

    candidates = [repo_root() / "templates"]
    here = Path(__file__).resolve()
    candidates.extend(parent / "templates" for parent in here.parents[:4])
    for candidate in candidates:
        if (candidate / "project").is_dir() and (candidate / "pages").is_dir():
            return candidate
    raise RenderError(
        "Cannot find the templates/ directory",
        remedy="Run from inside the Book Factory repository, or set BOOKFACTORY_ROOT.",
    )


@functools.lru_cache(maxsize=1)
def project_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_root() / "project")),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,
    )


@functools.lru_cache(maxsize=1)
def page_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(templates_root() / "pages")),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=select_autoescape(["html", "xml", "j2"], default_for_string=True),
    )
    env.filters["paragraphs"] = _paragraphs
    env.globals["fail"] = _fail
    return env


def _fail(message: str):
    """Raise from inside a template (Jinja has no raise tag)."""
    raise RenderError(message, remedy="Fix the block's \"type\" in the page spec.")


def _paragraphs(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [block.strip() for block in value.split("\n\n") if block.strip()]
    return [str(v) for v in value]


def project_template_names() -> list[str]:
    return sorted(p.name for p in (templates_root() / "project").glob("*.md"))


def render_project_template(name: str, context: dict) -> str:
    return project_env().get_template(name).render(**context)


def page_template_names() -> list[str]:
    return sorted(p.stem.replace(".html", "")
                  for p in (templates_root() / "pages").glob("*.html.j2")
                  if not p.name.startswith("_"))


def render_page_template(page_type: str, context: dict) -> str:
    name = f"{page_type}.html.j2"
    try:
        template = page_env().get_template(name)
    except Exception as exc:  # noqa: BLE001
        raise RenderError(
            f"No page template for type '{page_type}'",
            remedy="Available templates: " + ", ".join(page_template_names()),
        ) from exc
    return template.render(**context)
