from typing import Any

from path import Path
import toml

import tbump.config
import tbump.main

import pytest
from ui.tests.conftest import message_recorder
from tbump.test.conftest import file_contains


def test_creates_config(test_repo: Path, mock: Any) -> None:
    tbump_path = test_repo / "tbump.toml"
    tbump_path.remove()
    current_version = "1.2.41-alpha1"

    tbump.main.main(["-C", test_repo, "init", current_version])

    assert tbump_path.exists()
    config = toml.loads(tbump_path.text())
    assert config["version"]["current"] == "1.2.41-alpha1"
    first_match = config["file"][0]
    assert file_contains(test_repo / first_match["src"], current_version)


def test_abort_if_tbump_toml_exists(test_repo: Path, message_recorder: message_recorder) -> None:
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "init", "1.2.41-alpha1"])
    assert message_recorder.find("already exists")
