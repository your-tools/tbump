import re
from pathlib import Path
from typing import Optional

import pytest

from tbump.config import get_config_file
from tbump.git import run_git, run_git_captured
from tbump.git_bumper import (
    GitBumper,
    GitBumperOptions,
    NotOnAnyBranch,
    NoTrackedBranch,
)


@pytest.fixture
def test_git_bumper(test_repo: Path, tag_message: Optional[str]) -> GitBumper:
    bump_options = GitBumperOptions(test_repo, tag_message)

    config_file = get_config_file(test_repo)
    config = config_file.get_config()
    git_bumper = GitBumper(
        bump_options, operations=["commit", "tag", "push_commit", "push_tag"]
    )
    git_bumper.set_config(config)
    return git_bumper


def test_git_bumper_happy_path(
    test_repo: Path, test_git_bumper: GitBumper, tag_message: Optional[str]
) -> None:
    new_version = "1.2.42"
    test_git_bumper.check_dirty()
    test_git_bumper.check_branch_state(new_version)
    # Make sure git add does not fail:
    # we could use file_bumper here instead
    (test_repo / "VERSION").write_text(new_version)
    commands = test_git_bumper.get_commands(new_version)
    for command in commands:
        command.run()
    _, out = run_git_captured(test_repo, "log", "--oneline")
    assert "Bump to %s" % new_version in out

    _, tag_out = run_git_captured(test_repo, "tag", "-n1")

    actual_tag = test_git_bumper.tag_template.format(new_version=new_version)
    if tag_message:
        pattern = r"{}\s+{}".format(actual_tag, tag_message)
    else:
        pattern = r"{}\s+{}".format(actual_tag, actual_tag)

    search = re.search(pattern, tag_out)
    assert search is not None


def test_git_bumper_no_tracking_ref(
    test_repo: Path, test_git_bumper: GitBumper
) -> None:
    run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(NoTrackedBranch):
        test_git_bumper.check_dirty()
        test_git_bumper.check_branch_state("1.2.42")


def test_not_on_any_branch(test_repo: Path, test_git_bumper: GitBumper) -> None:
    run_git(test_repo, "commit", "--message", "test", "--allow-empty")
    run_git(test_repo, "checkout", "HEAD~1")

    with pytest.raises(NotOnAnyBranch):
        test_git_bumper.check_dirty()
        test_git_bumper.check_branch_state("1.2.42")
