"""Pure file classification via mapping-table / structural pattern matching.

Replaces the ``if/elif`` suffix chain in the legacy ``classify_file`` with a
declarative suffix -> :class:`LineCategory` mapping and a ``match`` for the
Python test/prod split. No ``Path`` in signatures — callers pass a
module-relative posix path string and (for test detection) the relative parts.
"""

from __future__ import annotations

from ppi.core.value_objects import LineCategory

__all__ = [
    "CSS_FILE_SUFFIXES",
    "classify_file_by_suffix",
    "is_test_file_by_parts",
    "classify_relative_file",
]

CSS_FILE_SUFFIXES: frozenset[str] = frozenset({".css", ".scss", ".less", ".sass"})

_SUFFIX_TO_CATEGORY: dict[str, LineCategory] = {
    ".py": LineCategory.PYTHON,
    ".js": LineCategory.JS,
    ".xml": LineCategory.XML,
    ".html": LineCategory.HTML,
}


def _css_category(suffix: str) -> LineCategory | None:
    return LineCategory.CSS if suffix in CSS_FILE_SUFFIXES else None


def classify_file_by_suffix(suffix: str) -> LineCategory | None:
    """Return the line category for a lowercase file suffix, or ``None``."""
    match suffix:
        case ".py":
            return LineCategory.PYTHON
        case ".js":
            return LineCategory.JS
        case ".xml":
            return LineCategory.XML
        case ".html":
            return LineCategory.HTML
        case s if s in CSS_FILE_SUFFIXES:
            return LineCategory.CSS
        case _:
            return None


def is_test_file_by_parts(relative_parts: tuple[str, ...], file_name: str) -> bool:
    """Return True if a module-relative file should be counted as a test.

    ``relative_parts`` are the path segments relative to the module root;
    ``file_name`` is the lowercase file name. Pure — no filesystem access.
    """
    if "tests" in relative_parts or "__tests__" in relative_parts:
        return True
    if file_name.startswith("test_") or file_name.endswith("_test.py"):
        return True
    if file_name.endswith(".test.js") or file_name.endswith(".spec.js"):
        return True
    return False


def classify_relative_file(relative_path: str) -> LineCategory | None:
    """Classify a module-relative posix path into a line category (pure).

    Combines suffix classification with the Python test/prod split. The
    ``relative_path`` is the posix-style path relative to the module root
    (e.g. ``"tests/test_order.py"``, ``"models/order.py"``).
    """
    parts = tuple(relative_path.split("/"))
    name = parts[-1].lower() if parts else ""
    suffix = ("." + name.rsplit(".", 1)[1]) if "." in name else ""
    category = classify_file_by_suffix(suffix)
    if category is None:
        return None
    if category is LineCategory.PYTHON and is_test_file_by_parts(parts, name):
        return LineCategory.PYTHON_TEST
    return category
