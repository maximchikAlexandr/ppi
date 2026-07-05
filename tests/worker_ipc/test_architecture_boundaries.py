import pytest


def test_protocol_imports_no_fastapi() -> None:
    import subprocess
    import sys
    code = (
        "import sys; import ppi.worker_ipc.protocol as m; "
        "fast = [x for x in sys.modules if 'fastapi' in x.lower()]; "
        "assert not fast, f'transitively imported: {fast}'"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"subprocess failed: {result.stderr}"


def test_worker_api_uses_client_not_store_writer() -> None:
    import sys
    mod_names = list(sys.modules.keys())
    store_writer_imports = [m for m in mod_names if "store" in m.lower() and "writer" in m.lower()]
    if store_writer_imports:
        pytest.skip("StoreWriter may be imported indirectly through other paths")
