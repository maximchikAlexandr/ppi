from ppi.worker_ipc.ide_contract import SUPPORTED_IDE_WORKER_COMMANDS


def test_supported_ide_commands_are_strings() -> None:
    assert all(isinstance(c, str) for c in SUPPORTED_IDE_WORKER_COMMANDS)


def test_supported_ide_commands_set() -> None:
    expected = {
        "worker.health",
        "workspace.info",
        "analysis.status",
        "analysis.start",
        "analysis.cancel",
        "query.execute",
        "events.subscribe",
    }
    assert set(SUPPORTED_IDE_WORKER_COMMANDS) == expected


def test_supported_ide_commands_are_unique() -> None:
    assert len(SUPPORTED_IDE_WORKER_COMMANDS) == len(set(SUPPORTED_IDE_WORKER_COMMANDS))
