"""Unit tests for domain value objects and runtime contracts."""

from __future__ import annotations

import pytest

from ppi.core.contracts_runtime import (
    ContractError,
    require,
    require_in_range,
    require_non_empty,
    require_non_empty_collection,
    require_non_negative,
    require_positive,
)
from ppi.core.value_objects import (
    AbsolutePathText,
    CommitHash,
    EdgeKind,
    EdgeKindGroup,
    FieldName,
    LineCategory,
    MethodName,
    ModelName,
    ModuleName,
    RelativeFilePath,
    SourceLine,
    edge_kind_group_of,
    edge_kind_of,
    line_category_of,
)

# --- CommitHash ----------------------------------------------------------


def test_commit_hash_ok():
    assert str(CommitHash.of("abc123")) == "abc123"
    assert str(CommitHash.of("0" * 40)) == "0" * 40


def test_commit_hash_parse_none():
    assert CommitHash.parse("nothex") is None
    assert CommitHash.parse("") is None


def test_commit_hash_rejects_non_hex():
    with pytest.raises(ContractError):
        CommitHash.of("xyz!")


# --- ModuleName ------------------------------------------------------------


def test_module_name_ok():
    assert str(ModuleName.of("sale")) == "sale"
    assert str(ModuleName.of("sale_management_2")) == "sale_management_2"


def test_module_name_parse_none():
    assert ModuleName.parse("bad name") is None
    assert ModuleName.parse("1starts_with_digit") is None


def test_module_name_rejects_invalid():
    with pytest.raises(ContractError):
        ModuleName.of("bad name")


# --- ModelName -------------------------------------------------------------


def test_model_name_ok():
    assert str(ModelName.of("sale.order")) == "sale.order"
    assert str(ModelName.of("res_partner")) == "res_partner"


def test_model_name_parse_none():
    assert ModelName.parse("not valid") is None


def test_model_name_rejects_invalid():
    with pytest.raises(ContractError):
        ModelName.of("not valid")


# --- FieldName / MethodName ------------------------------------------------


def test_field_name_ok():
    assert str(FieldName.of("partner_id")) == "partner_id"


def test_method_name_allows_underscore():
    assert str(MethodName.of("_compute_total")) == "_compute_total"


def test_method_name_rejects_invalid():
    with pytest.raises(ContractError):
        MethodName.of("has space")


# --- RelativeFilePath / AbsolutePathText -----------------------------------


def test_relative_file_path_ok():
    assert str(RelativeFilePath.of("models/order.py")) == "models/order.py"


def test_relative_file_path_rejects_absolute():
    with pytest.raises(ContractError):
        RelativeFilePath.of("/abs/path")


def test_absolute_path_text_ok():
    assert str(AbsolutePathText.of("/abs/path")) == "/abs/path"


def test_absolute_path_text_rejects_relative():
    with pytest.raises(ContractError):
        AbsolutePathText.of("rel")


# --- SourceLine ------------------------------------------------------------


def test_source_line_ok():
    assert int(SourceLine.of(7)) == 7


def test_source_line_or_none():
    assert SourceLine.or_none(0) is None
    assert SourceLine.or_none(5) is not None


def test_source_line_rejects_zero():
    with pytest.raises(ContractError):
        SourceLine.of(0)


# --- LineCategory ----------------------------------------------------------


def test_line_category_of_known():
    assert line_category_of("python_lines") is LineCategory.PYTHON
    assert line_category_of("xml_lines") is LineCategory.XML


def test_line_category_of_unknown():
    assert line_category_of("unknown") is None


def test_line_category_is_str_enum():
    assert LineCategory.PYTHON == "python_lines"


# --- EdgeKind --------------------------------------------------------------


def test_edge_kind_of_known():
    assert edge_kind_of("python__inherit") is EdgeKind.PYTHON_INHERIT
    assert edge_kind_of("xml_ref") is EdgeKind.XML_REF


def test_edge_kind_of_unknown():
    assert edge_kind_of("nope") is None


def test_edge_kind_group_mapping():
    assert edge_kind_group_of(EdgeKind.PYTHON_MANY2ONE) is EdgeKindGroup.MODEL_REUSE
    assert edge_kind_group_of(EdgeKind.XML_REF) is EdgeKindGroup.VIEW
    assert edge_kind_group_of(EdgeKind.PYTHON_FIELD_PROPERTY_ACCESS) is EdgeKindGroup.FIELD_PROPERTY
    assert edge_kind_group_of(EdgeKind.PYTHON_METHOD_CALL) is EdgeKindGroup.EXTENSION_OR_METHOD


# --- contracts_runtime helpers ---------------------------------------------


def test_require_passes():
    require(True, "ok")  # no raise


def test_require_fails():
    with pytest.raises(ContractError):
        require(False, "bad predicate")


def test_require_non_empty_ok():
    assert require_non_empty("x") == "x"


def test_require_non_empty_fails():
    with pytest.raises(ContractError):
        require_non_empty("")


def test_require_non_empty_collection_ok():
    assert list(require_non_empty_collection([1, 2])) == [1, 2]


def test_require_non_empty_collection_fails():
    with pytest.raises(ContractError):
        require_non_empty_collection([])


def test_require_non_negative_ok():
    assert require_non_negative(0) == 0


def test_require_non_negative_fails():
    with pytest.raises(ContractError):
        require_non_negative(-1)


def test_require_positive_ok():
    assert require_positive(1) == 1


def test_require_positive_fails():
    with pytest.raises(ContractError):
        require_positive(0)


def test_require_in_range_ok():
    assert require_in_range(5, 0, 10) == 5


def test_require_in_range_fails():
    with pytest.raises(ContractError):
        require_in_range(11, 0, 10)