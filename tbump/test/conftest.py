import re
import os

import path
import pytest

import tbump.git

from ui.tests.conftest import message_recorder
message_recorder  # silence pyflakes


@pytest.fixture()
def tmp_path(tmpdir):
    return path.Path(tmpdir)


@pytest.fixture
def test_path():
    this_dir = path.Path(__file__).parent
    return this_dir.abspath()


@pytest.fixture
def complex_version_regex():
    pattern = """\
  (?P<major>\d+)
  \.
  (?P<minor>\d+)
  \.
  (?P<patch>\d+)
  (
    -
    (?P<channel>alpha|beta)
    -
    (?P<release>\d+)
  )?
  """
    return re.compile(pattern, re.VERBOSE)


@pytest.fixture(autouse=True, scope="session")
def restore_cwd():
    old_cwd = os.getcwd()
    yield
    os.chdir(old_cwd)


def assert_in_file(*args):
    parts = args[0:-1]
    first = parts[0]
    rest = parts[1:]
    last = parts[-1]
    expected_line = args[-1]
    file_path = path.Path(first).joinpath(*rest)
    for line in file_path.lines():
        if expected_line in line:
            return
    assert False, "No line found matching %s in %s" % (expected_line, last)


def setup_repo(tmp_path, test_path):
    src_path = tmp_path.joinpath("src")
    src_path.mkdir()
    test_path.joinpath("tbump.toml").copy(src_path)
    test_path.joinpath("VERSION").copy(src_path)
    test_path.joinpath("package.json").copy(src_path)
    test_path.joinpath("pub.js").copy(src_path)
    tbump.git.run_git(src_path, "init")
    tbump.git.run_git(src_path, "add", ".")
    tbump.git.run_git(src_path, "commit", "--message", "initial commit")
    return src_path


def setup_remote(tmp_path):
    git_path = tmp_path.joinpath("git")
    git_path.mkdir()
    remote_path = git_path.joinpath("repo.git")
    remote_path.mkdir()
    tbump.git.run_git(remote_path, "init", "--bare")

    src_path = tmp_path.joinpath("src")
    tbump.git.run_git(src_path, "remote", "add", "origin", remote_path)
    tbump.git.run_git(src_path, "push", "-u", "origin", "master")
    return src_path


@pytest.fixture
def test_repo(tmp_path, test_path):
    res = setup_repo(tmp_path, test_path)
    setup_remote(tmp_path)
    return res
