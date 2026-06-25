"""Unit tests for the manifest value object and pure parser."""

from __future__ import annotations

import pytest

from ppi.core.odoo.manifest import (
    Manifest,
    ManifestParseError,
    ManifestParseFailed,
    ManifestPath,
    manifest_from_literal,
    parse_manifest_source,
)


def test_parse_manifest_source_dict_expr_ok():
    src = "{'name': 'demo', 'depends': ['base', 'sale']}\n"
    result = parse_manifest_source(src)
    assert result.is_ok()
    manifest = result.default_value(Manifest.empty())
    assert {m.value for m in manifest.depends} == {"base", "sale"}


def test_parse_manifest_source_assignment_ok():
    src = "__manifest__ = {'depends': ['base']}\n"
    result = parse_manifest_source(src, ManifestPath.of("m/__manifest__.py"))
    assert result.is_ok()
    manifest = result.default_value(Manifest.empty())
    assert {m.value for m in manifest.depends} == {"base"}


def test_parse_manifest_source_skips_docstring_then_finds_dict():
    src = '"""doc."""\n{\'depends\': [\'base\']}\n'
    result = parse_manifest_source(src)
    assert result.is_ok()
    manifest = result.default_value(Manifest.empty())
    assert {m.value for m in manifest.depends} == {"base"}


def test_parse_manifest_source_no_manifest_returns_error():
    result = parse_manifest_source("x = 1\n")
    assert result.is_error()
    assert result.error.reason == ManifestParseError.NO_ASSIGNMENT


def test_parse_manifest_source_not_dict_returns_error():
    result = parse_manifest_source("manifest = 42\n")
    assert result.is_error()
    assert result.error.reason == ManifestParseError.NO_ASSIGNMENT


def test_parse_manifest_source_syntax_error_returns_error():
    result = parse_manifest_source("{{invalid\n")
    assert result.is_error()
    assert result.error.reason == ManifestParseError.NO_LITERAL


def test_manifest_from_literal_non_dict_returns_error():
    result = manifest_from_literal(42)
    assert result.is_error()
    assert result.error.reason == ManifestParseError.NO_DICT


def test_manifest_from_literal_drops_non_string_depends():
    result = manifest_from_literal({"depends": ["base", 42, None, "sale"]})
    assert result.is_ok()
    manifest = result.default_value(Manifest.empty())
    assert {m.value for m in manifest.depends} == {"base", "sale"}
    assert manifest.raw is not None
    assert manifest.raw["_non_string_depends"] == [42, None]


def test_manifest_from_literal_invalid_module_name_dropped():
    result = manifest_from_literal({"depends": ["base", "bad name"]})
    assert result.is_ok()
    manifest = result.default_value(Manifest.empty())
    assert {m.value for m in manifest.depends} == {"base"}


def test_manifest_empty():
    m = Manifest.empty()
    assert m.depends == frozenset()
    assert m.depends_names == ()


def test_manifest_path_validates_suffix():
    with pytest.raises(ValueError):
        ManifestPath.of("not_a_manifest.py")


def test_manifest_parse_failed_path_text():
    failed = ManifestParseFailed(
        origin=ManifestPath.of("m/__manifest__.py"),
        reason=ManifestParseError.NO_DICT,
        message="bad",
    )
    assert failed.path_text == "m/__manifest__.py"


def test_manifest_parse_failed_path_text_none_origin():
    failed = ManifestParseFailed(origin=None, reason="x", message="bad")
    assert failed.path_text == ""


def test_manifest_depends_names_sorted():
    manifest = Manifest(depends=frozenset())
    assert manifest.depends_names == ()