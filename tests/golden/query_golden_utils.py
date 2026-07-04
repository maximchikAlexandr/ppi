"""Golden comparison utilities for legacy SQL vs Ibis outputs."""

from __future__ import annotations

from typing import Any


def compare_query_results(
    legacy: list[dict[str, Any]] | dict[str, Any],
    ibis_result: list[dict[str, Any]] | dict[str, Any],
    *,
    check_columns: bool = True,
    check_row_count: bool = True,
    check_values: bool = True,
) -> list[str]:
    differences: list[str] = []
    if check_columns:
        _check_columns(legacy, ibis_result, differences)
    if check_row_count:
        _check_row_count(legacy, ibis_result, differences)
    if check_values:
        _check_values(legacy, ibis_result, differences)
    return differences


def _check_columns(
    legacy: Any,
    ibis_result: Any,
    differences: list[str],
) -> None:
    if isinstance(legacy, dict) and isinstance(ibis_result, dict):
        l_keys = set(legacy.keys())
        i_keys = set(ibis_result.keys())
        _diff_keys(l_keys, i_keys, "top-level", differences)
        if "rows" in legacy and "rows" in ibis_result:
            l_rows = legacy.get("rows", [])
            i_rows = ibis_result.get("rows", [])
            for idx, (lr, ir) in enumerate(zip(l_rows, i_rows)):
                l_cells = lr.get("cells", lr)
                i_cells = ir.get("cells", ir)
                if isinstance(l_cells, dict) and isinstance(i_cells, dict):
                    _diff_keys(set(l_cells.keys()), set(i_cells.keys()), f"rows[{idx}]", differences)
    elif isinstance(legacy, list) and isinstance(ibis_result, list):
        for idx, (lr, ir) in enumerate(zip(legacy, ibis_result)):
            if isinstance(lr, dict) and isinstance(ir, dict):
                _diff_keys(set(lr.keys()), set(ir.keys()), f"items[{idx}]", differences)


def _diff_keys(
    legacy_keys: set[str],
    ibis_keys: set[str],
    label: str,
    differences: list[str],
) -> None:
    only_legacy = legacy_keys - ibis_keys
    only_ibis = ibis_keys - legacy_keys
    if only_legacy:
        differences.append(f"{label}: missing in Ibis: {only_legacy}")
    if only_ibis:
        differences.append(f"{label}: extra in Ibis: {only_ibis}")


def _check_row_count(
    legacy: Any,
    ibis_result: Any,
    differences: list[str],
) -> None:
    if isinstance(legacy, list) and isinstance(ibis_result, list):
        if len(legacy) != len(ibis_result):
            differences.append(f"row count: legacy={len(legacy)} ibis={len(ibis_result)}")
    if isinstance(legacy, dict) and isinstance(ibis_result, dict):
        l_rows = legacy.get("rows")
        i_rows = ibis_result.get("rows")
        if l_rows is not None and i_rows is not None:
            if len(l_rows) != len(i_rows):
                differences.append(f"row count: legacy={len(l_rows)} ibis={len(i_rows)}")


def _check_values(
    legacy: Any,
    ibis_result: Any,
    differences: list[str],
) -> None:
    if isinstance(legacy, list) and isinstance(ibis_result, list):
        for idx, (lr, ir) in enumerate(zip(legacy, ibis_result)):
            if lr != ir:
                differences.append(f"items[{idx}] differ")
                break
