import pytest
from ppi.devtools.codegen.errors import validate_errors


def test_duplicate_error_code_rejection():
    data = {
        "errors": [
            {"code": "DUPLICATE", "category": "client", "defaultMessage": "x", "retryable": False, "stability": "internal", "description": "x"},
            {"code": "DUPLICATE", "category": "client", "defaultMessage": "x", "retryable": False, "stability": "internal", "description": "x"},
        ],
    }
    issues = validate_errors(data)
    codes = [i.message for i in issues]
    assert any("duplicate" in m.lower() for m in codes)


def test_uppercase_snake_case_validation():
    data = {
        "errors": [
            {"code": "lowercase", "category": "client", "defaultMessage": "x", "retryable": False, "stability": "internal", "description": "x"},
        ],
    }
    issues = validate_errors(data)
    assert len(issues) == 1
    assert "uppercase snake case" in issues[0].message


def test_valid_errors_pass():
    data = {
        "errors": [
            {"code": "VALID_CODE", "category": "client", "defaultMessage": "x", "retryable": False, "stability": "internal", "description": "x"},
        ],
    }
    issues = validate_errors(data)
    assert len(issues) == 0


def test_invalid_category():
    data = {
        "errors": [
            {"code": "BAD_CAT", "category": "invalid_cat", "defaultMessage": "x", "retryable": False, "stability": "internal", "description": "x"},
        ],
    }
    issues = validate_errors(data)
    assert any("invalid category" in i.message for i in issues)


def test_stability_validation():
    data = {
        "errors": [
            {"code": "BAD_STAB", "category": "client", "defaultMessage": "x", "retryable": False, "stability": "unknown_stability", "description": "x"},
        ],
    }
    issues = validate_errors(data)
    assert any("invalid stability" in i.message for i in issues)


def test_deprecated_needs_replacement():
    data = {
        "errors": [
            {"code": "OLD_CODE", "category": "client", "defaultMessage": "x", "retryable": False, "stability": "deprecated", "description": "x"},
        ],
    }
    issues = validate_errors(data)
    assert any("replacement" in i.message.lower() or "removalNote" in i.message for i in issues)
