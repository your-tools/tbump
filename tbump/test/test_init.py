import textwrap
from pathlib import Path

import pytest
import tomlkit

from tbump.cli import run as run_tbump
from tbump.init import TbumpTomlAlreadyExists


def test_creates_tbump_toml_config(test_repo: Path) -> None:
    tbump_path = test_repo / "tbump.toml"
    tbump_path.unlink()
    current_version = "1.2.41-alpha1"

    run_tbump(["-C", str(test_repo), "init", current_version])

    assert tbump_path.exists()
    config = tomlkit.loads(tbump_path.read_text())
    assert config["version"]["current"] == "1.2.41-alpha1"  # type: ignore


def test_append_to_pyproject(test_repo: Path) -> None:
    cfg_path = test_repo / "pyproject.toml"
    isort_config = textwrap.dedent(
        """
        [tool.isort]
        profile = "black"
        """
    )
    cfg_path.write_text(isort_config)
    current_version = "1.2.41-alpha1"

    run_tbump(["-C", str(test_repo), "init", "--pyproject", current_version])

    assert cfg_path.exists()
    config = tomlkit.loads(cfg_path.read_text())
    assert config["tool"]["tbump"]["version"]["current"] == "1.2.41-alpha1"  # type: ignore
    assert config["tool"]["isort"]["profile"] == "black"  # type: ignore


def test_abort_if_tbump_toml_exists(
    test_repo: Path,
) -> None:
    with pytest.raises(TbumpTomlAlreadyExists):
        run_tbump(["-C", str(test_repo), "init", "1.2.41-alpha1"])


def test_use_specified_path(
    test_repo: Path,
) -> None:
    # fmt: off
    run_tbump(
        [
            "-C", str(test_repo),
            "--config", str(test_repo / "other.toml"),
            "init",
            "1.2.41-alpha1",
        ]
    )
    # fmt: on
    assert (test_repo / "other.toml").exists()
