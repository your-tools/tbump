from typing import Any
import os

from path import Path
import pytest

import tbump.git

from ui.tests.conftest import message_recorder # noqa


@pytest.fixture()  # type: ignore
def tmp_path(tmpdir: Any) -> Path:
    return Path(tmpdir)


@pytest.fixture  # type: ignore
def test_data_path() -> Path:
    this_dir = Path(__file__).abspath().parent
    return this_dir / "data"


@pytest.fixture(autouse=True, scope="session")  # type: ignore
def restore_cwd() -> None:
    old_cwd = os.getcwd()
    yield
    os.chdir(old_cwd)


def file_contains(path: Path, text: str) -> bool:
    for line in path.lines():
        if text in line:
            return True
    return False


def setup_repo(tmp_path: Path, test_data_path: Path) -> Path:
    src_path = tmp_path / "src"
    test_data_path.copytree(src_path)
    tbump.git.run_git(src_path, "init")
    tbump.git.run_git(src_path, "add", ".")
    tbump.git.run_git(src_path, "commit", "--message", "initial commit")
    tbump.git.run_git(src_path, "tag",
                      "--annotate",
                      "--message", "v1.2.41-alpha-1",
                      "v1.2.41-alpha-1")
    return src_path


def setup_remote(tmp_path: Path) -> Path:
    git_path = tmp_path / "git"
    git_path.mkdir()
    remote_path = git_path / "repo.git"
    remote_path.mkdir()
    tbump.git.run_git(remote_path, "init", "--bare")

    src_path = tmp_path / "src"
    tbump.git.run_git(src_path, "remote", "add", "origin", remote_path)
    tbump.git.run_git(src_path, "push", "-u", "origin", "master")
    return src_path


@pytest.fixture  # type: ignore
def test_repo(tmp_path: Path, test_data_path: Path) -> Path:
    res = setup_repo(tmp_path, test_data_path)
    setup_remote(tmp_path)
    return res
