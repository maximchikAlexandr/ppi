from ppi.devtools.codegen.errors import generate_errors_py


def test_deterministic_error_python_generation():
    errors = [{"code": "TEST_ERROR"}]
    result = generate_errors_py(errors, "test.yaml", "test")
    assert "class ErrorCode(str, Enum):" in result
    assert "TEST_ERROR = \"TEST_ERROR\"" in result
    assert "Generated file. Do not edit manually." in result


def test_error_generation_is_deterministic():
    errors = [{"code": "A"}, {"code": "B"}]
    r1 = generate_errors_py(errors, "x.yaml", "x")
    r2 = generate_errors_py(errors, "x.yaml", "x")
    assert r1 == r2
