from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click
import yaml

from ppi.devtools.codegen.types import ValidationIssue
from ppi.devtools.codegen.validate import load_yaml


@click.group(name="dev")
def dev_group() -> None:
    """Developer tooling: contract generation, validation, and freshness."""


def _validate_one(label: str, path: Path, run: Callable[[], list[ValidationIssue]]) -> bool:
    click.echo(f"{label}: ", nl=False)
    all_ok = True
    if path.is_file() or path.is_dir():
        try:
            errs = run()
            if errs:
                click.echo("FAIL")
                for e in errs:
                    click.echo(f"  - {e.message}")
                all_ok = False
            else:
                click.echo("ok")
        except (ValueError, OSError, yaml.YAMLError) as exc:
            click.echo(f"FAIL ({exc})")
            all_ok = False
    else:
        click.echo("ok (not found)")
    return all_ok


@dev_group.command(name="validate-contracts")
def validate_contracts() -> None:
    """Validate all contract sources without writing generated files."""
    all_ok = _run_validation(Path.cwd())
    if all_ok:
        click.echo("\nAll contract sources validated.")
    else:
        click.echo("\nSome contract sources have errors.")
        raise click.ClickException("validation failed")


def _run_validation(repo_root: Path) -> bool:
    from ppi.devtools.codegen.errors import validate_errors
    from ppi.devtools.codegen.webview import validate_webview_schema

    entries: list[tuple[str, Path, Callable[[], list[ValidationIssue]]]] = []

    errors_path = repo_root / "contracts" / "errors.yaml"
    entries.append((str(errors_path), errors_path, lambda: validate_errors(load_yaml(errors_path))))

    webview_path = repo_root / "contracts" / "webview-protocol.schema.json"
    entries.append((str(webview_path), webview_path, lambda: validate_webview_schema(webview_path)))

    results = [_validate_one(label, path, run) for label, path, run in entries]
    return all(results)


@dev_group.command(name="generate-contracts")
def generate_contracts() -> None:
    """Generate all contract artifacts from validated sources."""
    repo_root = Path.cwd()

    if not _run_validation(repo_root):
        click.echo("Validation failed. Run 'ppi dev validate-contracts' first.")
        raise click.ClickException("validation failed")

    click.echo("\nGenerating artifacts...")
    _generate_all(repo_root)
    click.echo("\nAll artifacts generated.")


@dev_group.command(name="check-generated")
def check_generated() -> None:
    """Check that committed generated artifacts are fresh."""
    repo_root = Path.cwd()

    if not _run_validation(repo_root):
        click.echo("Validation failed. Cannot check freshness.")
        raise click.ClickException("validation failed")

    from ppi.devtools.codegen.freshness import FreshnessReport, check_file_freshness

    expected: list[Path] = _expected_outputs(repo_root)
    stale: list[Path] = []
    missing: list[Path] = []

    for path in expected:
        if not path.is_file():
            missing.append(path)
            continue
        regenerated = _regenerate_content(repo_root, path)
        if regenerated is not None and not check_file_freshness(path, regenerated):
            stale.append(path)

    report = FreshnessReport(
        status="stale" if stale or missing else "fresh",
        stale_files=tuple(stale),
        missing_files=tuple(missing),
    )

    if report.passed:
        click.echo("\nAll generated contract artifacts are fresh.")
    else:
        for p in stale:
            click.echo(f"  STALE: {p}")
        for p in missing:
            click.echo(f"  MISSING: {p}")
        click.echo(f"\nRun: {report.remediation_command}")
        raise click.ClickException("generated artifacts are stale or missing")


@dataclass
class _GenEntry:
    source_id: str
    source_path: str
    generator: str
    rel_paths: dict[str, Callable[[Path], str | None]]


def _regen_yaml(path: Path, key: str, gen_fn: Callable[[list[dict]], str]) -> str | None:
    if not path.is_file():
        return None
    return gen_fn(load_yaml(path).get(key, []))


def _safe_regen(fn: Callable[[], str | None]) -> str | None:
    try:
        return fn()
    except ImportError:
        return None


def _regen_errors_py(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.errors import generate_errors_py
    return _regen_yaml(repo_root / "contracts/errors.yaml", "errors",
                        lambda items: generate_errors_py(items, "contracts/errors.yaml", "errors"))


def _regen_errors_docs(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.errors import generate_errors_docs
    return _regen_yaml(repo_root / "contracts/errors.yaml", "errors",
                        lambda items: generate_errors_docs(items, "contracts/errors.yaml", "errors"))


def _regen_progress_json(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.progress import build_progress_schema
    return _safe_regen(lambda: json.dumps(build_progress_schema(), indent=2))


def _regen_progress_py(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.progress import build_progress_schema, generate_progress_schema_py
    return _safe_regen(lambda: generate_progress_schema_py(
        build_progress_schema(), "ppi.runtime.progress::ProgressEvent", "progress"))


def _regen_progress_docs(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.progress import generate_progress_docs
    from importlib import import_module
    return _safe_regen(lambda: generate_progress_docs(
        getattr(import_module("ppi.runtime.progress"), "ProgressEvent").__args__,
        "ppi.runtime.progress::ProgressEvent", "progress"))


def _regen_errors_ts(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.errors import generate_errors_ts
    return _regen_yaml(repo_root / "contracts/errors.yaml", "errors",
                        lambda items: generate_errors_ts(items, "contracts/errors.yaml", "errors"))


def _regen_progress_ts(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.progress import generate_progress_ts
    from importlib import import_module
    return _safe_regen(lambda: generate_progress_ts(
        getattr(import_module("ppi.runtime.progress"), "ProgressEvent").__args__,
        "ppi.runtime.progress::ProgressEvent", "progress"))


def _regen_progress_validator(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.progress import build_progress_schema, generate_progress_validator_ts
    return _safe_regen(lambda: generate_progress_validator_ts(
        build_progress_schema(), "ppi.runtime.progress::ProgressEvent", "progress"))


def _regen_webview_protocol_ts(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.webview import generate_webview_protocol_ts
    path = repo_root / "contracts/webview-protocol.schema.json"
    if not path.is_file():
        return None
    return generate_webview_protocol_ts(
        json.loads(path.read_text(encoding="utf-8")), "contracts/webview-protocol.schema.json", "webview")


def _regen_webview_docs(repo_root: Path) -> str | None:
    from ppi.devtools.codegen.webview import generate_webview_docs
    path = repo_root / "contracts/webview-protocol.schema.json"
    if not path.is_file():
        return None
    return generate_webview_docs(
        json.loads(path.read_text(encoding="utf-8")), "contracts/webview-protocol.schema.json", "webview")


_GENERATORS: list[_GenEntry] = [
    _GenEntry("errors", "contracts/errors.yaml", "errors", {
        "src/ppi/generated/errors.py": _regen_errors_py,
        "docs/generated/errors.md": _regen_errors_docs,
    }),
    _GenEntry("errors-ts", "contracts/errors.yaml", "errors", {
        "vscode-extension/src/generated/errorCodes.ts": _regen_errors_ts,
    }),
    _GenEntry("progress-events", "src/ppi/runtime/progress.py::ProgressEvent", "progress", {
        "contracts/progress-events.schema.json": _regen_progress_json,
        "src/ppi/generated/progress_events_schema.py": _regen_progress_py,
        "docs/generated/progress-events.md": _regen_progress_docs,
    }),
    _GenEntry("progress-events-ts", "src/ppi/runtime/progress.py::ProgressEvent", "progress", {
        "vscode-extension/src/generated/progressEvents.ts": _regen_progress_ts,
    }),
    _GenEntry("progress-events-validator", "src/ppi/runtime/progress.py::ProgressEvent", "progress", {
        "vscode-extension/src/generated/progressEventValidators.ts": _regen_progress_validator,
    }),
    _GenEntry("webview-protocol", "contracts/webview-protocol.schema.json", "webview", {
        "docs/generated/webview-protocol.md": _regen_webview_docs,
    }),
    _GenEntry("webview-protocol-ts", "contracts/webview-protocol.schema.json", "webview", {
        "vscode-extension/src/generated/webviewProtocol.ts": _regen_webview_protocol_ts,
    }),
    # webview-protocol-validator removed per K4 — no runtime consumer (Zod validates webview messages)
]


def _regenerate_content(repo_root: Path, path: Path) -> str | None:
    rel = str(path.relative_to(repo_root))
    for entry in _GENERATORS:
        fn = entry.rel_paths.get(rel)
        if fn:
            return fn(repo_root)
    return None


def _expected_outputs(repo_root: Path) -> list[Path]:
    seen: set[Path] = set()
    for entry in _GENERATORS:
        for rel in entry.rel_paths:
            seen.add(repo_root / rel)
    return sorted(seen)


def _generate_all(repo_root: Path) -> None:
    from ppi.devtools.codegen.paths import assert_within_allowed
    for path in _expected_outputs(repo_root):
        rel = str(path.relative_to(repo_root))
        assert_within_allowed(rel)
        content = _regenerate_content(repo_root, path)
        if content is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            click.echo(f"  generated: {rel}")
    click.echo("All generators completed.")
