from ppi.worker_ipc import constants as c


def test_constants_exist() -> None:
    assert c.PROTOCOL_VERSION == "1.0"
    assert c.PROTOCOL_MAJOR == 1
    assert c.MAX_FRAME_BYTES == 16_777_216
    assert c.HEARTBEAT_INTERVAL_SECONDS == 5.0
    assert c.HEALTH_CHECK_TIMEOUT_SECONDS == 2.0
    assert c.WORKER_START_TIMEOUT_SECONDS == 10.0
    assert c.CLIENT_COMMAND_TIMEOUT_SECONDS == 30.0
    assert c.EVENT_QUEUE_MAXSIZE == 100


def test_package_importable() -> None:
    import ppi.worker_ipc  # noqa: F401
