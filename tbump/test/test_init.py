from pathlib import Path

import pytest
import tomlkit
from cli_ui.tests import MessageRecorder

import tbump.config
import tbump.main


def test_creates_config(test_repo: Path) -> None:
    tbump_path = test_repo / "tbump.toml"
    tbump_path.unlink()
    current_version = "1.2.41-alpha1"

    tbump.main.main(["-C", str(test_repo), "init", current_version])

    assert tbump_path.exists()
    config = tomlkit.loads(tbump_path.read_text())
    assert config["version"]["current"] == "1.2.41-alpha1"


def test_abort_if_tbump_toml_exists(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "init", "1.2.41-alpha1"])
    assert message_recorder.find("already exists")
