import pytest


def test_generated_modules_do_not_import_ppi_query():
    import importlib
    from ppi import generated
    mod_names = [name for name in dir(generated) if not name.startswith("_")]
    for name in mod_names:
        try:
            mod = importlib.import_module(f"ppi.generated.{name}")
            src = mod.__file__ or ""
        except Exception:
            continue
        with open(src, encoding="utf-8") as f:
            content = f.read()
        assert "from ppi.query" not in content, f"{name} imports ppi.query"
        assert "import ppi.query" not in content, f"{name} imports ppi.query"


def test_runtime_modules_do_not_import_devtools_codegen():
    import importlib
    try:
        mod = importlib.import_module("ppi.runtime.progress")
    except Exception:
        return
    src = mod.__file__ or ""
    with open(src, encoding="utf-8") as f:
        content = f.read()
    assert "ppi.devtools.codegen" not in content
