import os
import shutil
from pathlib import Path
from typing import Any, Iterator

import pytest

from tbump.git import run_git


@pytest.fixture()
def tmp_path(tmpdir: Any) -> Path:
    return Path(tmpdir)


@pytest.fixture
def test_project() -> Path:
    this_dir = Path(__file__).absolute().parent
    return this_dir / "project"


@pytest.fixture
def test_pyproject() -> Path:
    this_dir = Path(__file__).absolute().parent
    return this_dir / "pyproject"


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


def setup_repo(tmp_path: Path, test_project: Path) -> Path:
    src_path = tmp_path / "src"
    shutil.copytree(test_project, src_path)
    run_git(src_path, "init", "--initial-branch", "master")
    run_git(src_path, "add", ".")
    run_git(src_path, "commit", "--message", "initial commit")
    run_git(
        src_path, "tag", "--annotate", "--message", "v1.2.41-alpha-1", "v1.2.41-alpha-1"
    )
    return src_path


def setup_remote(tmp_path: Path) -> Path:
    git_path = tmp_path / "git"
    git_path.mkdir()
    remote_path = git_path / "repo.git"
    remote_path.mkdir()
    run_git(remote_path, "init", "--bare", "--initial-branch", "master")

    src_path = tmp_path / "src"
    run_git(src_path, "remote", "add", "origin", str(remote_path))
    run_git(src_path, "push", "-u", "origin", "master")
    return src_path


@pytest.fixture
def test_repo(tmp_path: Path, test_project: Path) -> Path:
    res = setup_repo(tmp_path, test_project)
    setup_remote(tmp_path)
    return res


@pytest.fixture
def test_pyproject_repo(tmp_path: Path, test_pyproject: Path) -> Path:
    res = setup_repo(tmp_path, test_pyproject)
    setup_remote(tmp_path)
    return res
