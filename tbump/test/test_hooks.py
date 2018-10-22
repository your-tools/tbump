from path import Path
import toml
import pytest

import tbump.git
import tbump.hooks
import tbump.main
from tbump.test.conftest import file_contains


def add_hook(test_repo: Path, name: str, cmd: str, after_push: bool = False) -> None:
    """ Patch the configuration file so that we can also test hooks.

    """
    cfg_path = test_repo / "tbump.toml"
    parsed = toml.loads(cfg_path.text())
    if after_push:
        key = "after_push"
    else:
        key = "before_commit"
    if key not in parsed:
        parsed[key] = list()
    parsed[key].append({"cmd": cmd, "name": name})

    cfg_path.write_text(toml.dumps(parsed))
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(test_repo, "commit", "--message", "update hooks")


def add_working_hook(test_repo: Path) -> None:
    add_hook(test_repo, "fake yarn", "python yarn.py")


def add_crashing_hook(test_repo: Path) -> None:
    add_hook(test_repo, "crashing hook", "python nosuchfile.py")


def add_after_hook(test_repo: Path) -> None:
    add_hook(test_repo, "after hook", "python after.py", after_push=True)


def test_working_hook(test_repo: Path) -> None:
    add_working_hook(test_repo)
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])

    assert file_contains(test_repo / "yarn.lock", "1.2.41-alpha-2")


def test_hook_fails(test_repo: Path) -> None:
    add_working_hook(test_repo)
    add_crashing_hook(test_repo)
    with pytest.raises(tbump.hooks.HookError):
        tbump.main.run(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])


def test_hooks_after_push(test_repo: Path) -> None:
    add_working_hook(test_repo)
    add_after_hook(test_repo)
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])
