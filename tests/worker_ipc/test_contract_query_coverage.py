"""Contract test: allowed query names exactly match ppi.query.dispatch.QueryMethod values."""

from ppi.query.dispatch import QueryMethod
from ppi.worker_ipc.query_service import ALLOWED_QUERY_NAMES


def test_allowed_query_names_match_querymethod() -> None:
    enum_values = frozenset(m.value for m in QueryMethod)
    assert ALLOWED_QUERY_NAMES == enum_values, (
        f"Allowed query names {ALLOWED_QUERY_NAMES} do not match QueryMethod values {enum_values}"
    )


def test_contract_list_matches_enum() -> None:
    from ppi.query.dispatch import QueryMethod
    contract_names = {
        "commits",
        "metrics/timeseries",
        "hotspots",
        "graph",
        "ui/config",
        "snapshot/table/modules",
        "snapshot/table/files",
        "snapshot/relations",
        "project/info",
    }
    enum_names = frozenset(m.value for m in QueryMethod)
    assert contract_names == enum_names, (
        f"Contract names {contract_names} do not match QueryMethod values {enum_names}"
    )
