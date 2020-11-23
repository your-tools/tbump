import os
import shutil
from pathlib import Path
from typing import Any, Iterator

import pytest
from cli_ui.tests import MessageRecorder

import tbump.git


@pytest.fixture()
def message_recorder() -> Iterator[MessageRecorder]:
    res = MessageRecorder()
    res.start()
    yield res
    res.stop()


@pytest.fixture()
def tmp_path(tmpdir: Any) -> Path:
    return Path(tmpdir)


@pytest.fixture
def test_data_path() -> Path:
    this_dir = Path(__file__).absolute().parent
    return this_dir / "data"


@pytest.fixture(autouse=True, scope="session")
def restore_cwd() -> Iterator[None]:
    old_cwd = os.getcwd()
    yield
    os.chdir(old_cwd)


def file_contains(path: Path, text: str) -> bool:
    for line in path.read_text().splitlines():
        if text in line:
            return True
    return False


def setup_repo(tmp_path: Path, test_data_path: Path) -> Path:
    src_path = tmp_path / "src"
    shutil.copytree(test_data_path, src_path)
    tbump.git.run_git(src_path, "init")
    tbump.git.run_git(src_path, "add", ".")
    tbump.git.run_git(src_path, "commit", "--message", "initial commit")
    tbump.git.run_git(
        src_path, "tag", "--annotate", "--message", "v1.2.41-alpha-1", "v1.2.41-alpha-1"
    )
    return src_path


def setup_remote(tmp_path: Path) -> Path:
    git_path = tmp_path / "git"
    git_path.mkdir()
    remote_path = git_path / "repo.git"
    remote_path.mkdir()
    tbump.git.run_git(remote_path, "init", "--bare")

    src_path = tmp_path / "src"
    tbump.git.run_git(src_path, "remote", "add", "origin", str(remote_path))
    tbump.git.run_git(src_path, "push", "-u", "origin", "master")
    return src_path


@pytest.fixture
def test_repo(tmp_path: Path, test_data_path: Path) -> Path:
    res = setup_repo(tmp_path, test_data_path)
    setup_remote(tmp_path)
    return res
