"""Book Factory - a production system for illustrated humour and gift books.

The repository is the source of truth. Everything this package does reads from
and writes to plain files on disk so that any agent - Claude, ChatGPT, or a
human - can resume a project from repository contents alone.
"""

__version__ = "1.0.0"
SCHEMA_VERSION = "1.0"

from bookfactory.core.errors import BookFactoryError  # noqa: E402,F401

__all__ = ["__version__", "SCHEMA_VERSION", "BookFactoryError"]
