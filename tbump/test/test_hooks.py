import toml
import pytest

import tbump.git
import tbump.hooks
import tbump.main
from tbump.test.conftest import assert_in_file


@pytest.fixture
def fake_yarn_hook(test_repo):
    """ Patch the configuration file so that we can also test hooks.

    """
    cfg_path = test_repo / "tbump.toml"
    parsed = toml.loads(cfg_path.text())
    parsed["hook"] = list()
    parsed["hook"].append({"cmd": "python yarn.py", "name": "fake yarn"})
    cfg_path.write_text(toml.dumps(parsed))
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(test_repo, "commit", "--message", "add yarn hook")


def test_end_to_end(test_repo, fake_yarn_hook):
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])

    assert_in_file("yarn.lock", "1.2.41-alpha-2")
