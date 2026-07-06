"""Regression test for spec 009 R-022.

Verifies that RpcRequest.params uses default_factory so two requests
do not share a mutable dict.
"""
from ppi.query.contracts import RpcRequest


def test_rpc_request_params_are_not_shared() -> None:
    first = RpcRequest(method="a")
    second = RpcRequest(method="b")
    first.params["x"] = 1
    assert "x" not in second.params
    assert second.params == {}


def test_rpc_request_default_params_is_empty_dict() -> None:
    req = RpcRequest(method="a")
    assert req.params == {}
    assert req.id == 0


def test_rpc_request_is_frozen() -> None:
    import pytest
    req = RpcRequest(method="a")
    with pytest.raises(Exception):
        req.method = "b"
