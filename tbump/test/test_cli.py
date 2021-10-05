from pathlib import Path
from typing import Any, Optional

import pytest
import tomlkit

from tbump.cli import run as run_tbump
from tbump.config import ConfigNotFound, InvalidConfig
from tbump.error import Error
from tbump.file_bumper import (
    BadSubstitution,
    CurrentVersionNotFound,
    InvalidVersion,
    SourceFileNotFound,
)
from tbump.git import run_git, run_git_captured
from tbump.git_bumper import DirtyRepository, NoTrackedBranch, RefAlreadyExists
from tbump.test.conftest import file_contains


def files_bumped(test_repo: Path, config_path: Optional[Path] = None) -> bool:
    config_path = config_path or test_repo / "tbump.toml"
    new_toml = tomlkit.loads(config_path.read_text())
    current_version = new_toml["version"]["current"]  # type: ignore

    assert current_version == "1.2.41-alpha-2"

    return all(
        (
            file_contains(test_repo / "package.json", '"version": "1.2.41-alpha-2"'),
            file_contains(test_repo / "package.json", '"other-dep": "1.2.41-alpha-1"'),
            file_contains(test_repo / "pub.js", "PUBLIC_VERSION = '1.2.41'"),
        )
    )


def files_not_bumped(test_repo: Path) -> bool:
    toml_path = test_repo / "tbump.toml"
    new_toml = tomlkit.loads(toml_path.read_text())
    assert new_toml["version"]["current"] == "1.2.41-alpha-1"  # type: ignore

    return all(
        (
            file_contains(test_repo / "package.json", '"version": "1.2.41-alpha-1"'),
            file_contains(test_repo / "package.json", '"other-dep": "1.2.41-alpha-1"'),
            file_contains(test_repo / "pub.js", "PUBLIC_VERSION = '1.2.41'"),
        )
    )


def commit_created(test_repo: Path) -> bool:
    _, out = run_git_captured(test_repo, "log", "--oneline")
    return "Bump to 1.2.41-alpha-2" in out


def tag_created(test_repo: Path) -> bool:
    _, out = run_git_captured(test_repo, "tag", "--list")
    return "v1.2.41-alpha-2" in out


def tag_pushed(test_repo: Path) -> bool:
    rc, _ = run_git_captured(
        test_repo,
        "ls-remote",
        "--exit-code",
        "origin",
        "refs/tags/v1.2.41-alpha-2",
        check=False,
    )
    return rc == 0


def branch_pushed(test_repo: Path, previous_commit: str) -> bool:
    _, local_commit = run_git_captured(test_repo, "rev-parse", "HEAD")
    _, out = run_git_captured(test_repo, "ls-remote", "origin", "refs/heads/master")
    remote_commit = out.split()[0]
    return remote_commit != previous_commit
    return remote_commit == local_commit


def bump_done(
    test_repo: Path,
    previous_commit: str,
) -> bool:
    return all(
        (
            files_bumped(test_repo),
            commit_created(test_repo),
            tag_created(test_repo),
            branch_pushed(test_repo, previous_commit),
            tag_pushed(test_repo),
        )
    )


def bump_not_done(test_repo: Path, previous_commit: str) -> bool:
    return all(
        (
            files_not_bumped(test_repo),
            not commit_created(test_repo),
            not tag_created(test_repo),
            not branch_pushed(test_repo, previous_commit),
            not tag_pushed(test_repo),
        )
    )


def only_patch_done(test_repo: Path, previous_commit: str) -> bool:
    return all(
        (
            files_bumped(test_repo),
            not commit_created(test_repo),
            not tag_created(test_repo),
            not branch_pushed(test_repo, previous_commit),
            not tag_pushed(test_repo),
        )
    )


def test_end_to_end_using_tbump_toml(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")
    run_tbump(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])

    assert bump_done(test_repo, previous_commit)


def test_end_to_end_using_pyproject_toml(test_pyproject_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_pyproject_repo, "rev-parse", "HEAD")

    run_tbump(["-C", str(test_pyproject_repo), "0.2.0", "--non-interactive"])

    pyproject_toml = test_pyproject_repo / "pyproject.toml"
    doc = tomlkit.loads(pyproject_toml.read_text())
    assert doc["tool"]["tbump"]["version"]["current"] == "0.2.0"  # type: ignore
    assert doc["tool"]["poetry"]["version"] == "0.2.0"  # type: ignore

    foo_py = test_pyproject_repo / "foo" / "__init__.py"
    actual = foo_py.read_text()
    assert "0.2.0" in actual


def test_using_specified_path(
    test_repo: Path,
) -> None:
    run_git(test_repo, "mv", "tbump.toml", "other.toml")
    run_git(test_repo, "commit", "--message", "rename tbump.toml -> other.toml")
    config_path = test_repo / "other.toml"

    # fmt: off
    run_tbump(
        [
            "-C", str(test_repo),
            "--config", str(config_path),
            "--only-patch",
            "--non-interactive",
            "1.2.41-alpha-2",
        ]
    )
    # fmt: on

    assert files_bumped(test_repo, config_path=config_path)


def test_dry_run_interactive(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")
    run_tbump(["-C", str(test_repo), "1.2.41-alpha-2", "--dry-run"])
    assert bump_not_done(test_repo, previous_commit)


def test_dry_run_non_interactive(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")
    run_tbump(
        ["-C", str(test_repo), "1.2.41-alpha-2", "--dry-run", "--non-interactive"]
    )

    assert bump_not_done(test_repo, previous_commit)


def test_only_patch(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")
    run_tbump(
        ["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive", "--only-patch"]
    )

    assert only_patch_done(test_repo, previous_commit)


def test_on_outdated_branch(test_repo: Path) -> None:
    """Make sure no tag is pushed when running tbump on an outdated branch"""
    # See https://github.com/dmerejkowsky/tbump/issues/20 ¨ for details

    # Make sure the branch is out of date
    run_git(test_repo, "commit", "--message", "commit I did not make", "--allow-empty")
    run_git(test_repo, "push", "origin", "master")
    run_git(test_repo, "reset", "--hard", "HEAD~1")

    with pytest.raises(Error):
        run_tbump(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])
    assert not tag_pushed(test_repo)


def test_tbump_toml_not_found(test_repo: Path) -> None:
    toml_path = test_repo / "tbump.toml"
    toml_path.unlink()
    with pytest.raises(ConfigNotFound):
        run_tbump(["-C", str(test_repo), "1.2.42", "--non-interactive"])


def test_tbump_toml_bad_syntax(test_repo: Path) -> None:
    toml_path = test_repo / "tbump.toml"
    bad_toml = tomlkit.loads(toml_path.read_text())
    del bad_toml["git"]
    toml_path.write_text(tomlkit.dumps(bad_toml))
    with pytest.raises(InvalidConfig):
        run_tbump(["-C", str(test_repo), "1.2.42", "--non-interactive"])


def test_new_version_does_not_match(test_repo: Path) -> None:
    with pytest.raises(InvalidVersion):
        run_tbump(["-C", str(test_repo), "1.2.41a2", "--non-interactive"])


def test_abort_if_file_does_not_exist(test_repo: Path) -> None:
    (test_repo / "package.json").unlink()
    run_git(test_repo, "add", "--update")
    run_git(test_repo, "commit", "--message", "remove package.json")
    with pytest.raises(SourceFileNotFound):
        run_tbump(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])


def test_interactive_abort(test_repo: Path, mocker: Any) -> None:
    ask_mock = mocker.patch("cli_ui.ask_yes_no")
    ask_mock.return_value = False

    with pytest.raises(Error):
        run_tbump(["-C", str(test_repo), "1.2.41-alpha-2"])

    ask_mock.assert_called_with("Looking good?", default=False)
    assert file_contains(test_repo / "VERSION", "1.2.41-alpha-1")
    rc, out = run_git_captured(test_repo, "tag", "--list")
    assert "v1.2.42-alpha-2" not in out


def test_abort_if_dirty(test_repo: Path) -> None:
    version_path = test_repo / "VERSION"
    with version_path.open("a") as f:
        f.write("unstaged changes\n")

    with pytest.raises(DirtyRepository):
        run_tbump(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])


def test_abort_if_tag_exists(test_repo: Path) -> None:
    run_git(test_repo, "tag", "v1.2.42")

    with pytest.raises(RefAlreadyExists):
        run_tbump(["-C", str(test_repo), "1.2.42", "--non-interactive"])


def test_abort_if_file_does_not_contain_current_version(test_repo: Path) -> None:
    invalid_src = test_repo / "foo.txt"
    invalid_src.write_text("this is foo")
    tbump_path = test_repo / "tbump.toml"
    with tbump_path.open("a") as f:
        f.write(
            """\
        [[file]]
        src = "foo.txt"
        """
        )
    run_git(test_repo, "add", ".")
    run_git(test_repo, "commit", "--message", "add foo.txt")

    with pytest.raises(CurrentVersionNotFound):
        run_tbump(["-C", str(test_repo), "1.2.42", "--non-interactive"])


def test_no_tracked_branch_but_ref_exists(test_repo: Path) -> None:
    run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(RefAlreadyExists):
        run_tbump(["-C", str(test_repo), "1.2.41-alpha-1"])


def test_no_tracked_branch_non_interactive(test_repo: Path) -> None:
    run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(NoTrackedBranch):
        run_tbump(["-C", str(test_repo), "1.2.42", "--non-interactive"])


def test_interactive_proceed(test_repo: Path, mocker: Any) -> None:
    ask_mock = mocker.patch("cli_ui.ask_yes_no")

    ask_mock.return_value = [True]
    run_tbump(["-C", str(test_repo), "1.2.42"])
    ask_mock.assert_called_with("Looking good?", default=False)
    _, out = run_git_captured(test_repo, "ls-remote")
    assert "tags/v1.2.42" in out


def test_do_not_add_untracked_files(test_repo: Path) -> None:
    (test_repo / "untracked.txt").write_text("please don't add me")
    run_tbump(["-C", str(test_repo), "1.2.42", "--non-interactive"])
    _, out = run_git_captured(test_repo, "show", "--stat", "HEAD")
    assert "untracked.txt" not in out


def test_bad_substitution(test_repo: Path) -> None:
    toml_path = test_repo / "tbump.toml"
    new_toml = tomlkit.loads(toml_path.read_text())
    new_toml["file"][0]["version_template"] = "{build}"  # type: ignore
    toml_path.write_text(tomlkit.dumps(new_toml))
    run_git(test_repo, "add", ".")
    run_git(test_repo, "commit", "--message", "update repo")
    with pytest.raises(BadSubstitution):
        run_tbump(["-C", str(test_repo), "1.2.42"])


def test_no_push(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")
    # We're not supposed to push anything, so we should not even check that the
    # current branch tracks something.
    run_git(test_repo, "branch", "--unset-upstream")

    run_tbump(
        ["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive", "--no-push"]
    )

    assert commit_created(test_repo)
    assert tag_created(test_repo)
    assert not branch_pushed(test_repo, previous_commit)


def test_no_tag(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")

    run_tbump(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive", "--no-tag"])

    assert commit_created(test_repo)
    assert not tag_created(test_repo)


def test_no_tag_no_push(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")
    run_git(test_repo, "branch", "--unset-upstream")

    run_tbump(
        [
            "-C",
            str(test_repo),
            "1.2.41-alpha-2",
            "--non-interactive",
            "--no-tag",
            "--no-push",
        ]
    )

    assert commit_created(test_repo)
    assert not tag_created(test_repo)


def test_create_tag_but_do_not_push_it(test_repo: Path) -> None:
    _, previous_commit = run_git_captured(test_repo, "rev-parse", "HEAD")

    run_tbump(
        [
            "-C",
            str(test_repo),
            "1.2.41-alpha-2",
            "--non-interactive",
            "--no-tag-push",
        ]
    )

    assert tag_created(test_repo)
    assert not tag_pushed(test_repo)
