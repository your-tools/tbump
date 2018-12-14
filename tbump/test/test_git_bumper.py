from path import Path

import tbump.config
import tbump.git
import tbump.git_bumper
from tbump.git_bumper import GitBumper

import pytest


@pytest.fixture
def test_git_bumper(test_repo: Path) -> GitBumper:
    config = tbump.config.parse(test_repo / "tbump.toml")
    git_bumper = tbump.git_bumper.GitBumper(test_repo)
    git_bumper.set_config(config)
    return git_bumper


def test_git_bumper_happy_path(test_repo: Path, test_git_bumper: GitBumper) -> None:
    new_version = "1.2.42"
    test_git_bumper.check_state(new_version)
    # Make sure git add does not fail:
    # we could use file_bumper here instead
    (test_repo / "VERSION").write_text(new_version)
    commands = test_git_bumper.get_commands(new_version)
    for command in commands:
        command.run()
    _, out = tbump.git.run_git_captured(test_repo, "log", "--oneline")
    assert "Bump to %s" % new_version in out


def test_git_bumper_no_tracking_ref(test_repo: Path, test_git_bumper: GitBumper) -> None:
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(tbump.git_bumper.NoTrackedBranch):
        test_git_bumper.check_state("1.2.42")


def test_not_on_any_branch(test_repo: Path, test_git_bumper: GitBumper) -> None:
    tbump.git.run_git(test_repo, "commit", "--message", "test", "--allow-empty")
    tbump.git.run_git(test_repo, "checkout", "HEAD~1")

    with pytest.raises(tbump.git_bumper.NotOnAnyBranch):
        test_git_bumper.check_state("1.2.42")
