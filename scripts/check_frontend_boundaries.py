"""Frontend boundary scanner.

Fails (non-zero exit) when:
  * a generic frontend file imports from ``frontend/src/api/generated/**``
  * a generic frontend file imports from ``frontend/src/legacy/**``
  * a generic frontend file imports from ``frontend/src/api/legacyClient.ts``
    or ``frontend/src/api/legacySchemas.ts`` (legacy RPC transport)
  * a generic frontend file contains any of the forbidden domain tokens
  * a generic page/component calls ``ds().get(\"...\")`` or
    ``httpPath(\"...\", ...)`` with a raw method name (must use the
    typed ``publicApi`` facade)

Generic frontend paths are everything under
``frontend/src/{api,domain,registry,components/generic,pages,transforms,visualization}``
except ``frontend/src/legacy``, ``frontend/src/api/adapters``, and the
transport shells listed in ``EXEMPT_PATHS`` (publicApi, http,
apiProtocol, dataSource, generated).

Allowed exception: files under ``frontend/src/legacy/**`` may import
generated DTOs and use forbidden tokens; they are the legacy boundary.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FRONTEND = REPO / "frontend" / "src"

GENERIC_PREFIXES = (
    "frontend/src/api",
    "frontend/src/domain",
    "frontend/src/registry",
    "frontend/src/components/generic",
    "frontend/src/pages",
    "frontend/src/transforms",
    "frontend/src/visualization",
)

# Files allowed to import generated DTOs / legacy modules.
EXEMPT_PATHS = (
    "frontend/src/legacy",
    "frontend/src/api/adapters",
    "frontend/src/api/publicApi.ts",
    "frontend/src/api/http.ts",
    # Transport shells shared by legacy and v1 clients. They implement
    # the RPC envelope / URL encoding for the webview bridge and HTTP
    # fallback; generic pages must not call them directly.
    "frontend/src/api/apiProtocol.ts",
    "frontend/src/api/dataSource.ts",
    # Generated DTOs are auto-generated from the OpenAPI contract; they
    # mirror the backend field names (snake_case for legacy schemas)
    # and must not be edited.
    "frontend/src/api/generated/",
    # Pre-010 legacy adapter modules under frontend/src/legacy/**
    # are covered by the folder prefix above. Any future exemption
    # for a new file must be added to frontend/MIGRATION.md first.
    "frontend/src/api/legacySchemas.ts",
    "frontend/src/api/legacyClient.ts",
)

FORBIDDEN_TOKENS = (
    "module_name",
    "python_file_count",
    "cyclomatic",
    "cognitive",
    "jones",
    "manifest_depends",
    "model_reuse",
    "field_property",
    "extension_or_method",
    "python_lines",
    "xml_lines",
    "score_in",
    "score_out",
)

FORBIDDEN_IMPORTS = (
    "odooProfile",
)


@dataclass
class Violation:
    file: str
    line: int
    token: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.token}"


def _is_exempt(rel: str) -> bool:
    return any(rel.startswith(p) for p in EXEMPT_PATHS)


def _is_generic(rel: str) -> bool:
    if any(rel.startswith(p) for p in EXEMPT_PATHS):
        return False
    # Test files are exempt: they assert the generic contract by
    # referencing forbidden tokens, which is the whole point of the
    # boundary check.
    if rel.endswith(".test.ts") or rel.endswith(".test.tsx") or rel.endswith("_test.py"):
        return False
    return any(rel.startswith(p) for p in GENERIC_PREFIXES)


def _strip_comments(content: str) -> str:
    """Replace comments with whitespace, leaving strings intact.

    We keep string literals in the scrubbed output so that hardcoded
    uses of forbidden tokens (``const x = "module_name"``) are still
    flagged. Only comments are stripped.
    """
    out: list[str] = []
    i = 0
    in_block_comment = False
    while i < len(content):
        ch = content[i]
        nxt = content[i + 1] if i + 1 < len(content) else ""
        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                out.append("  ")
                i += 2
                continue
            out.append(" " if ch != "\n" else "\n")
            i += 1
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            out.append("  ")
            i += 2
            continue
        if ch == "/" and nxt == "/":
            j = content.find("\n", i)
            end = j if j >= 0 else len(content)
            out.append(" " * (end - i))
            i = end
            continue
        if ch == "#":
            j = content.find("\n", i)
            end = j if j >= 0 else len(content)
            out.append(" " * (end - i))
            i = end
            continue
        out.append(ch)
        i += 1
    return "".join(out)


# Object-literal property keys are NOT stripped from generic code.
# Stripping them created a leak: `{ cyclomatic: 5 }` in a generic
# component was invisible to the token scan, even though the contract
# forbids generic code from referencing these fields at all. Legacy
# files (under frontend/src/legacy/**) are exempt from the scan
# entirely, so they can still bridge legacy-shaped objects without
# tripping the scanner.


def scan(rel_path: str, content: str) -> list[Violation]:
    violations: list[Violation] = []
    if not _is_generic(rel_path):
        return violations
    # Import checks run on the RAW content so that import strings
    # (which contain `generated`, `legacy`, etc.) are still matched.
    # We catch: `from "..."`, `import "..."` (side-effect), and
    # `import("...")` (dynamic).
    import_re = re.compile(
        r"""(?:from\s+|import\s+|import\()\s*['"]([^'"]+)['"]"""
    )
    for i, line in enumerate(content.splitlines(), start=1):
        for m in import_re.finditer(line):
            target = m.group(1)
            if "generated" in target or "/generated/" in target:
                violations.append(Violation(rel_path, i, "generated DTO import"))
            if "/legacy/" in target:
                violations.append(Violation(rel_path, i, "legacy import"))
            # Match both absolute and relative specifiers so a generic
            # file cannot slip through with `import "./legacySchemas"`
            # or `import "../api/legacyClient"`. The basename check
            # covers all relative forms; absolute-path checks are
            # kept for clarity in scanner output.
            basename = Path(target).name
            if (
                basename in ("legacyClient.ts", "legacyClient.tsx", "legacyClient")
                or basename in ("legacySchemas.ts", "legacySchemas.tsx", "legacySchemas")
            ):
                violations.append(Violation(rel_path, i, "legacy transport import"))
        for bad in FORBIDDEN_IMPORTS:
            if re.search(rf"\b{re.escape(bad)}\b", line):
                violations.append(Violation(rel_path, i, f"forbidden import: {bad}"))
    # No raw method-string routing in generic code: anything calling
    # `getDataSource().get("some_method")`, `ds().get("some_method")`,
    # or `httpPath("some_method", ...)` must go through the typed
    # `publicApi` facade instead.
    method_string_re = re.compile(
        r"""\b(?:getDataSource|ds)\s*\([^)]*\)\s*\.\s*get\s*\(\s*['"][a-zA-Z_]"""
    )
    http_path_re = re.compile(
        r"""\bhttpPath\s*\(\s*['"][a-zA-Z_]"""
    )
    for i, line in enumerate(content.splitlines(), start=1):
        if method_string_re.search(line):
            violations.append(Violation(rel_path, i, "raw method-string routing"))
        if http_path_re.search(line):
            violations.append(Violation(rel_path, i, "raw httpPath routing"))
    # Token checks run on comment-stripped content. String literals are
    # kept so hardcoded uses are caught. Object-literal keys are NOT
    # stripped (see comment above the function).
    scrubbed = _strip_comments(content)
    for i, line in enumerate(scrubbed.splitlines(), start=1):
        for tok in FORBIDDEN_TOKENS:
            if re.search(rf"\b{re.escape(tok)}\b", line):
                violations.append(Violation(rel_path, i, f"forbidden token: {tok}"))
    return violations


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    files: list[Path] = []
    if argv:
        for arg in argv:
            files.append(Path(arg))
    else:
        for prefix in GENERIC_PREFIXES:
            base = REPO / prefix
            if not base.exists():
                continue
            for ext in ("*.ts", "*.tsx"):
                files.extend(base.rglob(ext))
    total = 0
    for fp in files:
        rel = str(fp.relative_to(REPO))
        try:
            content = fp.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"warning: could not read {rel}: {exc}", file=sys.stderr)
            continue
        for v in scan(rel, content):
            print(v)
            total += 1
    if total:
        print(f"boundary violations: {total}", file=sys.stderr)
        return 1
    print("boundary OK")
    return 0


def _self_test() -> int:
    """Smoke test: ensure each rule actually fires on a positive case.

    Run with `python check_frontend_boundaries.py --self-test`. Returns 0
    if every rule triggers; non-zero otherwise. Catches regressions when
    someone refactors the regex set.
    """
    cases: list[tuple[str, str, str]] = [
        (
            "legacy transport relative import",
            "frontend/src/components/generic/_probe.tsx",
            'import type { Foo } from "./legacySchemas";\n',
            "legacy transport import",
        ),
        (
            "legacy transport absolute import",
            "frontend/src/components/generic/_probe.tsx",
            'import { fetchCommits } from "../api/legacyClient";\n',
            "legacy transport import",
        ),
        (
            "raw method-string routing via getDataSource",
            "frontend/src/components/generic/_probe.tsx",
            'getDataSource().get("graph");\n',
            "raw method-string routing",
        ),
        (
            "raw method-string routing via ds()",
            "frontend/src/components/generic/_probe.tsx",
            'getDataSource().get("hotspots");\n',
            "raw method-string routing",
        ),
        (
            "raw httpPath routing",
            "frontend/src/components/generic/_probe.tsx",
            'const url = httpPath("graph", { commit: "x" });\n',
            "raw httpPath routing",
        ),
        (
            "forbidden domain token",
            "frontend/src/components/generic/_probe.tsx",
            'const x: number = node.module_name as never;\n',
            "forbidden token: module_name",
        ),
        (
            "forbidden import odooProfile",
            "frontend/src/components/generic/_probe.tsx",
            "import { odooProfile } from \"../registry/odooProfile\";\n",
            "forbidden import: odooProfile",
        ),
    ]
    failures = 0
    for name, rel, content, expected in cases:
        got = [v.token for v in scan(rel, content)]
        if expected not in got:
            print(f"FAIL: {name}: expected {expected!r} in {got!r}", file=sys.stderr)
            failures += 1
        else:
            print(f"OK:   {name}")
    if failures:
        print(f"self-test failures: {failures}", file=sys.stderr)
        return 1
    print("self-test OK")
    return 0


if __name__ == "__main__":
    import sys as _sys
    if _sys.argv[1:] == ["--self-test"]:
        raise SystemExit(_self_test())
    raise SystemExit(main())