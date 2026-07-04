"""Canonical PPI wrapper around Expression Result/Option.

Re-exports ``Result``, ``Ok``, ``Error``, ``Option``, ``Some``, ``Nothing``
from ``expression``.

This module MUST NOT define a second incompatible Result or Option type.
"""

from __future__ import annotations

from expression.core import Error as _ExprError
from expression.core import Nothing as _ExprNothing
from expression.core import Ok as _ExprOk
from expression.core import Option as _ExprOption
from expression.core import Result as _ExprResult
from expression.core import Some as _ExprSome

Result = _ExprResult
Ok = _ExprOk
Error = _ExprError
Option = _ExprOption
Some = _ExprSome
Nothing = _ExprNothing

__all__ = [
    "Result",
    "Ok",
    "Error",
    "Option",
    "Some",
    "Nothing",
]
