"""Verify scripts/check_frontend_boundaries.py catches generic-code violations."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


SCANNER = Path(__file__).resolve().parents[2] / "scripts" / "check_frontend_boundaries.py"


@pytest.fixture()
def scanner():
    spec = importlib.util.spec_from_file_location("scanner", SCANNER)
    module = importlib.util.module_from_spec(spec)
    # Python 3.14's dataclass requires the module to be present in
    # sys.modules before spec.loader.exec_module runs.
    sys.modules["scanner"] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop("scanner", None)
    return module


def test_scanner_detects_generated_dto_import(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/components/generic/values/Fake.tsx",
        'import { paths } from "../../../api/generated/schema";\n',
    )
    assert any("generated" in v.token for v in violations)


def test_scanner_detects_legacy_import(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/domain/fake.ts",
        'import { legacyGraphToGenericGraph } from "../legacy/legacyGraphAdapter";\n',
    )
    assert any("legacy" in v.token for v in violations)


def test_scanner_detects_forbidden_token(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/components/generic/values/Fake.tsx",
        'const x = "module_name";\n',
    )
    assert any("forbidden" in v.token for v in violations)


def test_scanner_allows_legacy_directory(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/legacy/legacyGraphAdapter.ts",
        'import { paths } from "../api/generated/schema";\nconst x = "module_name";\n',
    )
    assert violations == []


def test_scanner_includes_file_path_and_line(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/domain/fake.ts",
        'import { foo } from "../legacy/legacyApiTypes";\n',
    )
    assert violations
    v = violations[0]
    assert "fake.ts" in v.file
    assert v.line == 1


def test_scanner_flags_forbidden_object_key_in_generic(scanner) -> None:
    """Constructing an object keyed by a forbidden token is a violation.

    Regression: an earlier version stripped object-literal keys before
    the token scan, which silently let `{ cyclomatic: 5 }` through in
    generic code. The strip was a leak; it is gone now.
    """
    violations = scanner.scan(
        "frontend/src/components/generic/graph/Fake.tsx",
        "const metric = { cyclomatic: 5 };\n",
    )
    assert any("cyclomatic" in v.token for v in violations)


def test_scanner_flags_side_effect_import_of_generated(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/domain/fake.ts",
        'import "../api/generated/schema";\n',
    )
    assert any("generated" in v.token for v in violations)


def test_scanner_flags_dynamic_import_of_legacy(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/domain/fake.ts",
        'const m = await import("../legacy/legacyApiTypes");\n',
    )
    assert any("legacy" in v.token for v in violations)


def test_scanner_scans_visualization_path(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/visualization/fake.ts",
        'const x = "cyclomatic";\n',
    )
    assert any("cyclomatic" in v.token for v in violations)


def test_scanner_flags_forbidden_import(scanner) -> None:
    violations = scanner.scan(
        "frontend/src/pages/fake.tsx",
        'import { odooProfile } from "../registry/odooProfile";\n',
    )
    assert any("odooProfile" in v.token for v in violations)
