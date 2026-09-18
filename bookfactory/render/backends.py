"""HTML-to-PDF backends.

HTML and CSS were chosen as the page description language because they give
exact 6x9 boxes, real typography, reusable templates, and - importantly - a page
you can open in a browser when something looks wrong. Debugging a layout by
reading HTML beats debugging a layout by squinting at a PDF.

Two backends are supported:

* **weasyprint** (default) - pure Python, no browser, deterministic output.
* **chromium** - fallback for anything WeasyPrint's CSS support cannot express.

Both are deterministic: SOURCE_DATE_EPOCH is pinned and the PDF is normalised
afterwards, so re-rendering an unchanged page produces the same bytes and the
same checksum.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from bookfactory.core.errors import RenderError

#: Pinned so repeated renders of unchanged input are byte-identical.
FIXED_EPOCH = "0"

CHROMIUM_CANDIDATES = (
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome",
)
CHROMIUM_EXTRA_PATHS = (
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
    "/usr/lib/chromium/chromium",
)


def _find_chromium() -> str | None:
    override = os.environ.get("BOOKFACTORY_CHROMIUM")
    if override and Path(override).exists():
        return override
    for name in CHROMIUM_CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    for pattern in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                    "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"):
        matches = sorted(Path("/").glob(pattern.lstrip("/")))
        if matches:
            return str(matches[-1])
    for path in CHROMIUM_EXTRA_PATHS:
        if Path(path).exists():
            return path
    return None


def weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401  - presence is the whole check
    except Exception:  # noqa: BLE001
        return False
    return True


def chromium_available() -> bool:
    return _find_chromium() is not None


def available_backends() -> list[str]:
    backends = []
    if weasyprint_available():
        backends.append("weasyprint")
    if chromium_available():
        backends.append("chromium")
    return backends


def default_backend() -> str:
    override = os.environ.get("BOOKFACTORY_RENDER_BACKEND")
    if override:
        return override
    backends = available_backends()
    if not backends:
        raise RenderError(
            "No HTML-to-PDF backend is available",
            remedy=("Install WeasyPrint (`pip install weasyprint`) or make a Chromium binary "
                    "available on PATH. See docs/RENDERING.md."),
        )
    return backends[0]


def render_html_to_pdf(html: str, destination: str | Path, *, base_url: str | Path,
                       backend: str | None = None) -> Path:
    backend = backend or default_backend()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if backend == "weasyprint":
        _weasyprint(html, destination, base_url)
    elif backend == "chromium":
        _chromium(html, destination, base_url)
    else:
        raise RenderError(
            f"Unknown render backend {backend!r}",
            remedy="Available: " + ", ".join(available_backends()),
        )
    normalise_pdf(destination)
    return destination


def _weasyprint(html: str, destination: Path, base_url: str | Path) -> None:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    try:
        from weasyprint import HTML

        HTML(string=html, base_url=str(base_url)).write_pdf(str(destination))
    except Exception as exc:  # noqa: BLE001
        raise RenderError(f"WeasyPrint failed: {exc}") from exc
    finally:
        if previous is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous


def _chromium(html: str, destination: Path, base_url: str | Path) -> None:
    binary = _find_chromium()
    if binary is None:
        raise RenderError("Chromium was requested but no binary was found")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(base_url) / f".bf-render-{os.getpid()}.html"
        source.write_text(html, encoding="utf-8")
        try:
            command = [
                binary, "--headless", "--disable-gpu", "--no-sandbox",
                f"--user-data-dir={tmp}",
                "--no-pdf-header-footer", "--disable-pdf-tagging",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=10000",
                f"--print-to-pdf={destination}",
                source.as_uri(),
            ]
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            if result.returncode != 0 or not destination.exists():
                raise RenderError(
                    f"Chromium failed (exit {result.returncode}): {result.stderr.strip()[:500]}"
                )
        finally:
            source.unlink(missing_ok=True)


def normalise_pdf(path: str | Path) -> Path:
    """Strip non-deterministic metadata so unchanged input keeps its checksum."""
    path = Path(path)
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, ByteStringObject, NameObject, TextStringObject
    except ImportError:  # pragma: no cover - pypdf is a hard dependency
        return path

    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    stable_id = ByteStringObject(b"BookFactoryStabl")
    writer._ID = ArrayObject([stable_id, stable_id])
    writer._info.update({
        NameObject("/Producer"): TextStringObject("Book Factory"),
        NameObject("/Creator"): TextStringObject("Book Factory deterministic renderer"),
    })
    for key in ("/CreationDate", "/ModDate"):
        if key in writer._info:
            del writer._info[NameObject(key)]
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("wb") as handle:
        writer.write(handle)
    tmp.replace(path)
    return path
