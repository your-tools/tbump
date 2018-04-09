import tbump.config
import tbump.git
import tbump.git_bumper

import pytest


@pytest.fixture
def test_git_bumper(test_repo):
    config = tbump.config.parse(test_repo.joinpath("tbump.toml"))
    git_bumper = tbump.git_bumper.GitBumper(test_repo)
    git_bumper.set_config(config)
    return git_bumper


def test_git_bumper_happy_path(test_repo, test_git_bumper):
    test_git_bumper.check_state("1.2.42")
    test_repo.joinpath("VERSION").write_text("1.2.42")
    test_git_bumper.bump("1.2.42")
    _, out = tbump.git.run_git_captured(test_repo, "log", "--oneline")
    assert "Bump to 1.2.42" in out


def test_git_bumper_no_tracking_ref(test_repo, test_git_bumper):
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(tbump.git_bumper.NoTrackedBranch):
        test_git_bumper.check_state("1.2.42")


def test_not_on_any_branch(test_repo, test_git_bumper):
    tbump.git.run_git(test_repo, "commit", "--message", "test", "--allow-empty")
    tbump.git.run_git(test_repo, "checkout", "HEAD~1")

    with pytest.raises(tbump.git_bumper.NotOnAnyBranch):
        test_git_bumper.check_state("1.2.42")
