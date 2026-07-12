# Generated file. Do not edit manually.
# Source: contracts/errors.yaml
# Generator: errors

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class ErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    WORKSPACE_ERROR = "WORKSPACE_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    DEPRECATED_FEATURE = "DEPRECATED_FEATURE"
    STORE_NOT_READY = "STORE_NOT_READY"


@dataclass(frozen=True)
class ErrorSpec:
    code: ErrorCode
    category: str = ""
    default_message: str = ""
    retryable: bool = False
    stability: str = ""
    description: str = ""
    http_status: int | None = None
    rpc_code: str = ""
    cli_exit_category: str = ""
    webview_action_mapping: str = ""
    replacement: str = ""
    removal_note: str = ""


_HTTP_STATUS_MAP: dict[ErrorCode, int | None] = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.STORE_NOT_READY: 503,
}

_RETRYABLE: frozenset[ErrorCode] = frozenset({ErrorCode.INTERNAL_ERROR, ErrorCode.WORKSPACE_ERROR, ErrorCode.RATE_LIMITED, ErrorCode.STORE_NOT_READY})


def http_status_for(code: ErrorCode) -> int | None:
    return _HTTP_STATUS_MAP.get(code)


def is_retryable(code: ErrorCode) -> bool:
    return code in _RETRYABLE


invalid_request: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.INVALID_REQUEST,
    category="client",
    default_message="Invalid request.",
    retryable=False,
    stability="public",
    description="Request payload or parameters are invalid.",
    http_status=400,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="",
    removal_note="",
)
internal_error: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.INTERNAL_ERROR,
    category="server",
    default_message="An internal error occurred.",
    retryable=True,
    stability="internal",
    description="Unexpected server error.",
    http_status=500,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="",
    removal_note="",
)
not_found: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.NOT_FOUND,
    category="client",
    default_message="Resource not found.",
    retryable=False,
    stability="public",
    description="Requested resource does not exist.",
    http_status=404,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="",
    removal_note="",
)
validation_error: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.VALIDATION_ERROR,
    category="client",
    default_message="Validation error.",
    retryable=False,
    stability="public",
    description="Input validation failed.",
    http_status=422,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="",
    removal_note="",
)
workspace_error: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.WORKSPACE_ERROR,
    category="workspace",
    default_message="Workspace error.",
    retryable=True,
    stability="experimental",
    description="Workspace-related error.",
    http_status=None,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="",
    removal_note="",
)
rate_limited: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.RATE_LIMITED,
    category="transport",
    default_message="Rate limited.",
    retryable=True,
    stability="public",
    description="Request was rate limited.",
    http_status=429,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="",
    removal_note="",
)
deprecated_feature: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.DEPRECATED_FEATURE,
    category="runtime",
    default_message="This feature is deprecated.",
    retryable=False,
    stability="deprecated",
    description="Deprecated error.",
    http_status=None,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="USE_NEW_FEATURE",
    removal_note="",
)
store_not_ready: Final[ErrorSpec] = ErrorSpec(
    code=ErrorCode.STORE_NOT_READY,
    category="server",
    default_message="Storage is not ready.",
    retryable=True,
    stability="internal",
    description="Database or storage backend is unavailable.",
    http_status=503,
    rpc_code="",
    cli_exit_category="",
    webview_action_mapping="",
    replacement="",
    removal_note="",
)

ERRORS: dict[ErrorCode, ErrorSpec] = {
    ErrorCode.INVALID_REQUEST: invalid_request,
    ErrorCode.INTERNAL_ERROR: internal_error,
    ErrorCode.NOT_FOUND: not_found,
    ErrorCode.VALIDATION_ERROR: validation_error,
    ErrorCode.WORKSPACE_ERROR: workspace_error,
    ErrorCode.RATE_LIMITED: rate_limited,
    ErrorCode.DEPRECATED_FEATURE: deprecated_feature,
    ErrorCode.STORE_NOT_READY: store_not_ready
}
