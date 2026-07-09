"""Canonical profile entity-kind ids.

The active analysis profile (Python/Odoo by default) declares its
primary entity kinds. Generic backend code MUST NOT branch on these
strings directly; route through the values exposed here.
"""
from __future__ import annotations

PYTHON_MODULE_KIND: str = "python.module"
PYTHON_FILE_KIND: str = "python.file"

PYTHON_KIND_SUFFIXES: tuple[str, str] = (".module", ".file")

LEVEL_MODULE: str = "module"
LEVEL_FILE: str = "file"


def is_module_kind(kind: str) -> bool:
    return kind == PYTHON_MODULE_KIND or kind.endswith(".module")


def is_file_kind(kind: str) -> bool:
    return kind == PYTHON_FILE_KIND or kind.endswith(".file")
