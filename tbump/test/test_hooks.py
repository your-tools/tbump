import toml
import pytest

import tbump.git
import tbump.hooks
import tbump.main
from tbump.test.conftest import assert_in_file


@pytest.fixture
def working_hook(test_repo):
    return add_hook(test_repo, "fake yarn", "python yarn.py")


@pytest.fixture
def crashing_hook(test_repo):
    return add_hook(test_repo, "crash", "python nosuchfile.py")


def add_hook(test_repo, name, cmd):
    """ Patch the configuration file so that we can also test hooks.

    """
    cfg_path = test_repo / "tbump.toml"
    parsed = toml.loads(cfg_path.text())
    if "hook" not in parsed:
        parsed["hook"] = list()
    parsed["hook"].append({"cmd": cmd, "name": name})
    cfg_path.write_text(toml.dumps(parsed))
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(test_repo, "commit", "--message", "add yarn hook")


def test_end_to_end(test_repo, working_hook):
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])

    assert_in_file("yarn.lock", "1.2.41-alpha-2")


def test_hook_fails(test_repo, working_hook, crashing_hook):
    with pytest.raises(tbump.hooks.HookError):
        tbump.main.run(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])
