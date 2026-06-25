"""Filesystem adapter layer.

All direct access to ``Path``, ``open``, ``read_text``, ``rglob``, ``stat``
lives here. Core/domain code calls these functions or accepts pre-loaded data
and stays testable on strings/DTOs without a real filesystem.

The adapter returns plain strings/tuples and typed value-object inputs where
useful; it does not import ``ppi.core.odoo.pipeline`` domain logic so the
dependency direction stays adapter -> domain, never the reverse.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Self

from expression.core.result import Error, Ok, Result

from ppi.core.odoo.manifest import (
    Manifest,
    ManifestParseFailed,
    ManifestPath,
    parse_manifest_source,
)
from ppi.core.value_objects import AbsolutePathText, SourceLine

__all__ = [
    "AbsoluteDirectoryPath",
    "FilesystemError",
    "FilesystemSourceQuoteProvider",
    "ManifestFile",
    "SourceQuoteProvider",
    "count_file_lines",
    "find_manifest_paths",
    "read_file_lines",
    "read_file_text",
    "read_manifest_file",
    "resolve_directory",
    "rglob_files",
    "source_quote_for_line",
]


class FilesystemError(Exception):
    """Adapter-level filesystem error (OSError wrapper)."""


@dataclass(frozen=True, slots=True)
class AbsoluteDirectoryPath:
    """Absolute path to an existing directory, validated on construction.

    This is an adapter-layer value object: existence is checked here against
    the real filesystem, so it must not be constructed in pure domain code.
    """

    value: Path

    def __post_init__(self) -> None:
        if not isinstance(self.value, Path):
            raise TypeError(f"AbsoluteDirectoryPath requires Path, got {type(self.value).__name__}")
        if not self.value.is_absolute():
            raise FilesystemError(f"Path must be absolute: {self.value}")
        if not self.value.is_dir():
            raise FilesystemError(f"Path must be an existing directory: {self.value}")

    @classmethod
    def from_path(cls, path: Path | str) -> Self:
        """Build an absolute directory path from a path-like input, resolving it."""
        resolved = Path(path).resolve()
        return cls(resolved)

    def as_text(self) -> AbsolutePathText:
        """Return the path as a typed absolute path text."""
        return AbsolutePathText.of(str(self.value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ManifestFile:
    """A read manifest file: its path and source text."""

    path: ManifestPath
    source: str
    absolute_path: Path


def resolve_directory(path: Path | str) -> AbsoluteDirectoryPath:
    """Resolve and validate an existing directory; raise :class:`FilesystemError`."""
    return AbsoluteDirectoryPath.from_path(path)


def read_file_text(path: Path) -> str:
    """Read a file as UTF-8 text, replacing bad bytes; raise on OSError."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise FilesystemError(f"Cannot read {path}: {exc}") from exc


def read_file_text_strict(path: Path) -> Result[str, FilesystemError]:
    """Read a file as UTF-8 text strictly; return typed Result."""
    try:
        return Ok(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        return Error(FilesystemError(f"Cannot read {path}: {exc}"))


def read_file_lines(path: Path) -> tuple[str, ...]:
    """Read a file and return its lines as a tuple (UTF-8, replace)."""
    return tuple(read_file_text(path).splitlines())


def count_file_lines(path: Path) -> int:
    """Count physical lines in a text file by iterating without full load."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as file_obj:
            return sum(1 for _ in file_obj)
    except OSError as exc:
        raise FilesystemError(f"Cannot count lines in {path}: {exc}") from exc


def rglob_files(root: Path, pattern: str) -> Iterator[Path]:
    """Yield sorted files under ``root`` matching ``pattern``."""
    yield from sorted(root.rglob(pattern))


def rglob_all_files(root: Path) -> Iterator[Path]:
    """Yield sorted regular files under ``root`` (recursive)."""
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def find_manifest_paths(addons_paths: Iterable[Path]) -> tuple[Path, ...]:
    """Find all ``__manifest__.py`` files under the given addons paths."""
    found: list[Path] = []
    for root in addons_paths:
        found.extend(sorted(root.rglob("__manifest__.py")))
    return tuple(found)


def read_manifest_file(path: Path) -> Result[ManifestFile, ManifestParseFailed | FilesystemError]:
    """Read a manifest file from disk and return its source wrapped in a value.

    Pure parsing is left to :func:`ppi.core.odoo.manifest.parse_manifest_source`;
    this function only performs the filesystem read and wraps a possible
    :class:`FilesystemError` as a typed ``Error``.
    """
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return Error(FilesystemError(f"Cannot read manifest {path}: {exc}"))
    relative_text = path.parent.name + "/__manifest__.py"
    return Ok(
        ManifestFile(
            path=ManifestPath.of(relative_text),
            source=source,
            absolute_path=path,
        ),
    )


def read_and_parse_manifest(path: Path) -> Result[Manifest, ManifestParseFailed | FilesystemError]:
    """Read a manifest file from disk and parse it in one step (adapter helper)."""
    read_result = read_manifest_file(path)
    if read_result.is_error():
        return read_result  # type: ignore[return-value]
    manifest_file = read_result.default_value(None)  # type: ignore[union-attr, arg-type]
    return parse_manifest_source(manifest_file.source, origin=manifest_file.path)  # type: ignore[union-attr]


# --- Source quote provider (PPI-052) ---------------------------------------


class SourceQuoteProvider:
    """Protocol-ish provider of source-quote lines for evidence.

    Pure domain edge/fact builders accept this as a dependency instead of
    reading the filesystem directly.
    """

    def quote(self, file_path: Path, line: SourceLine) -> str:
        """Return the trimmed source line at ``line`` for ``file_path``."""
        raise NotImplementedError


class FilesystemSourceQuoteProvider(SourceQuoteProvider):
    """Filesystem-backed source quote provider with an mtime-keyed line cache.

    ``ponytail: lru_cache keyed by (posix_path, mtime_ns)`` — sufficient for a
    single analysis run; if very large repos stress memory, move to a bounded
    cache keyed by path only with mtime invalidation.
    """

    def quote(self, file_path: Path, line: SourceLine) -> str:
        line_no = int(line)
        if line_no <= 0:
            return ""
        try:
            stat = file_path.stat()
        except OSError:
            return ""
        lines = _cached_lines(file_path.as_posix(), stat.st_mtime_ns)
        if line_no > len(lines):
            return ""
        return lines[line_no - 1].strip()


@lru_cache(maxsize=4096)
def _cached_lines(path: str, mtime_ns: int) -> tuple[str, ...]:
    """Return file lines keyed by path and modification time."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ()
    return tuple(text.splitlines())


def source_quote_for_line(file_path: Path, line: int) -> str:
    """Standalone adapter helper: source quote for a 1-based line number."""
    if line <= 0:
        return ""
    sl = SourceLine.or_none(line)
    if sl is None:
        return ""
    return FilesystemSourceQuoteProvider().quote(file_path, sl)
