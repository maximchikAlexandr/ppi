from ppi.worker_ipc.runtime_paths import Endpoint


def test_endpoint_dataclass() -> None:
    ep = Endpoint(transport="unix", path="/tmp/sock")
    assert ep.transport == "unix"
    assert ep.path == "/tmp/sock"
    assert ep.uri() == "unix:///tmp/sock"
