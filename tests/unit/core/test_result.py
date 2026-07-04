"""Tests proving src/ppi/core/result.py composes Expression Ok/Error and
Some/Nothing values without introducing incompatible Result or Option types."""

from __future__ import annotations

from ppi.core.result import Error, Nothing, Ok, Result, Some


def test_ok_holds_value() -> None:
    r: Result[int, str] = Ok(42)
    assert r.is_ok()
    assert r.ok == 42


def test_error_holds_error() -> None:
    r: Result[int, str] = Error("fail")
    assert r.is_error()
    assert r.error == "fail"


def test_some_holds_value() -> None:
    s = Some(42)
    assert s.is_some()


def test_nothing_has_no_value() -> None:
    n = Nothing
    assert n.is_none()
