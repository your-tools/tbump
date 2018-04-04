import tbump.config
import tbump.git
import tbump.git_bumper

import pytest


def test_git_bumper_happy_path(test_repo):
    config = tbump.config.parse(test_repo.joinpath("tbump.toml"))
    git_bumper = tbump.git_bumper.GitBumper(test_repo)
    git_bumper.set_config(config)
    git_bumper.check_state("1.2.42")
    test_repo.joinpath("VERSION").write_text("1.2.42")
    git_bumper.bump("1.2.42")
    rc, out = tbump.git.run_git(test_repo, "log", "--oneline", raises=False)
    assert rc == 0
    assert "Bump to 1.2.42" in out


def test_git_bumper_no_tracking_ref(test_repo):
    config = tbump.config.parse(test_repo.joinpath("tbump.toml"))
    git_bumper = tbump.git_bumper.GitBumper(test_repo)
    git_bumper.set_config(config)
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(tbump.git_bumper.NoTrackedBranch):
        git_bumper.check_state("1.2.42")
