from pathlib import Path
from typing import Any

import pytest
import tomlkit
from cli_ui.tests import MessageRecorder

import tbump.git
import tbump.hooks
import tbump.main
from tbump.test.conftest import file_contains


def files_bumped(test_repo: Path, using_pyproject: bool = False) -> bool:
    if using_pyproject:
        cfg_path = test_repo / "pyproject.toml"
        new_toml = tomlkit.loads(cfg_path.read_text())
        current_version = new_toml["tool"]["tbump"]["version"]["current"]
    else:
        cfg_path = test_repo / "tbump.toml"
        new_toml = tomlkit.loads(cfg_path.read_text())
        current_version = new_toml["version"]["current"]

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
    assert new_toml["version"]["current"] == "1.2.41-alpha-1"

    return all(
        (
            file_contains(test_repo / "package.json", '"version": "1.2.41-alpha-1"'),
            file_contains(test_repo / "package.json", '"other-dep": "1.2.41-alpha-1"'),
            file_contains(test_repo / "pub.js", "PUBLIC_VERSION = '1.2.41'"),
        )
    )


def commit_created(test_repo: Path) -> bool:
    _, out = tbump.git.run_git_captured(test_repo, "log", "--oneline")
    return "Bump to 1.2.41-alpha-2" in out


def tag_created(test_repo: Path) -> bool:
    _, out = tbump.git.run_git_captured(test_repo, "tag", "--list")
    return "v1.2.41-alpha-2" in out


def tag_pushed(test_repo: Path) -> bool:
    rc, _ = tbump.git.run_git_captured(
        test_repo,
        "ls-remote",
        "--exit-code",
        "origin",
        "refs/tags/v1.2.41-alpha-2",
        check=False,
    )
    return rc == 0


def branch_pushed(test_repo: Path, previous_commit: str) -> bool:
    _, local_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    _, out = tbump.git.run_git_captured(
        test_repo, "ls-remote", "origin", "refs/heads/master"
    )
    remote_commit = out.split()[0]
    return remote_commit != previous_commit
    return remote_commit == local_commit


def bump_done(
    test_repo: Path, previous_commit: str, *, using_pyproject: bool = False
) -> bool:
    return all(
        (
            files_bumped(test_repo, using_pyproject=using_pyproject),
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
    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])

    assert bump_done(test_repo, previous_commit)


def test_end_to_end_using_pyproject_toml(test_repo: Path) -> None:
    tbump_toml_path = test_repo / "tbump.toml"

    # Convert tbump config to a config inside a tool.tbump section:
    tbump_config = tomlkit.loads(tbump_toml_path.read_text())
    tools_config = tomlkit.table()
    tools_config.add("tbump", tbump_config)
    pyproject_config = tomlkit.table()
    pyproject_config.add("tool", tools_config)
    to_write = tomlkit.dumps(pyproject_config)

    # Write the pyproject.toml and remove tbump.toml
    pyproject_toml_path = test_repo / "pyproject.toml"
    pyproject_toml_path.write_text(to_write)
    tbump_toml_path.unlink()
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(
        test_repo, "commit", "--message", "move tbump config inside pyproject.toml"
    )

    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])

    assert bump_done(test_repo, previous_commit, using_pyproject=True)


def test_dry_run_interactive(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-2", "--dry-run"])
    assert bump_not_done(test_repo, previous_commit)


def test_dry_run_non_interactive(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    tbump.main.main(
        ["-C", str(test_repo), "1.2.41-alpha-2", "--dry-run", "--non-interactive"]
    )

    assert bump_not_done(test_repo, previous_commit)


def test_only_patch(test_repo: Path) -> None:
    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    tbump.main.main(
        ["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive", "--only-patch"]
    )

    assert only_patch_done(test_repo, previous_commit)


def test_on_outdated_branch(test_repo: Path) -> None:
    """ Make sure no tag is pushed when running tbump on an outdated branch"""
    # See https://github.com/TankerHQ/tbump/issues/20 ¨ for details

    # Make sure the branch is out of date
    tbump.git.run_git(
        test_repo, "commit", "--message", "commit I did not make", "--allow-empty"
    )
    tbump.git.run_git(test_repo, "push", "origin", "master")
    tbump.git.run_git(test_repo, "reset", "--hard", "HEAD~1")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])
    assert not tag_pushed(test_repo)


def test_tbump_toml_not_found(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    toml_path = test_repo / "tbump.toml"
    toml_path.unlink()
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.42", "--non-interactive"])
    assert message_recorder.find("No configuration for tbump")


def test_tbump_toml_bad_syntax(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    toml_path = test_repo / "tbump.toml"
    bad_toml = tomlkit.loads(toml_path.read_text())
    del bad_toml["git"]
    toml_path.write_text(tomlkit.dumps(bad_toml))
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.42", "--non-interactive"])
    assert message_recorder.find("Invalid config")


def test_new_version_does_not_match(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.41a2", "--non-interactive"])
    assert message_recorder.find("Could not parse 1.2.41a2")


def test_abort_if_file_does_not_exist(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    (test_repo / "package.json").unlink()
    tbump.git.run_git(test_repo, "add", "--update")
    tbump.git.run_git(test_repo, "commit", "--message", "remove package.json")
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])
    assert message_recorder.find("package.json does not exist")


def test_interactive_abort(test_repo: Path, mocker: Any) -> None:
    ask_mock = mocker.patch("cli_ui.ask_yes_no")
    ask_mock.return_value = False

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-2"])

    ask_mock.assert_called_with("Looking good?", default=False)
    assert file_contains(test_repo / "VERSION", "1.2.41-alpha-1")
    rc, out = tbump.git.run_git_captured(test_repo, "tag", "--list")
    assert "v1.2.42-alpha-2" not in out


def test_abort_if_dirty(test_repo: Path, message_recorder: MessageRecorder) -> None:
    version_path = test_repo / "VERSION"
    with version_path.open("a") as f:
        f.write("unstaged changes\n")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive"])
    assert message_recorder.find("dirty")


def test_abort_if_tag_exists(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    tbump.git.run_git(test_repo, "tag", "v1.2.42")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.42", "--non-interactive"])
    assert message_recorder.find("1.2.42 already exists")


def test_abort_if_file_does_not_match(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
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
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(test_repo, "commit", "--message", "add foo.txt")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.42", "--non-interactive"])
    assert message_recorder.find("not found")
    assert file_contains(test_repo / "VERSION", "1.2.41-alpha-1")


def test_no_tracked_branch_but_ref_exists(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.41-alpha-1"])
    assert message_recorder.find("already exists")


def test_no_tracked_branch_non_interactive(
    test_repo: Path, message_recorder: MessageRecorder
) -> None:
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.42", "--non-interactive"])
    assert message_recorder.find("Cannot push")


def test_interactive_proceed(test_repo: Path, mocker: Any) -> None:
    ask_mock = mocker.patch("cli_ui.ask_yes_no")

    ask_mock.return_value = [True]
    tbump.main.main(["-C", str(test_repo), "1.2.42"])
    ask_mock.assert_called_with("Looking good?", default=False)
    _, out = tbump.git.run_git_captured(test_repo, "ls-remote")
    assert "tags/v1.2.42" in out


def test_do_not_add_untracked_files(test_repo: Path) -> None:
    (test_repo / "untracked.txt").write_text("please don't add me")
    tbump.main.main(["-C", str(test_repo), "1.2.42", "--non-interactive"])
    _, out = tbump.git.run_git_captured(test_repo, "show", "--stat", "HEAD")
    assert "untracked.txt" not in out


def test_bad_substitution(test_repo: Path, message_recorder: MessageRecorder) -> None:
    toml_path = test_repo / "tbump.toml"
    new_toml = tomlkit.loads(toml_path.read_text())
    new_toml["file"][0]["version_template"] = "{release}"
    toml_path.write_text(tomlkit.dumps(new_toml))
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(test_repo, "commit", "--message", "update repo")
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", str(test_repo), "1.2.42"])
    assert message_recorder.find("refusing to replace by version containing 'None'")


def test_no_push(test_repo: Path) -> None:
    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    # We're not supposed to push anything, so we should not even check that the
    # current branch tracks something.
    tbump.git.run_git(test_repo, "branch", "--unset-upstream")

    tbump.main.main(
        ["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive", "--no-push"]
    )

    assert commit_created(test_repo)
    assert tag_created(test_repo)
    assert not branch_pushed(test_repo, previous_commit)


def test_no_tag(test_repo: Path) -> None:
    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")

    tbump.main.main(
        ["-C", str(test_repo), "1.2.41-alpha-2", "--non-interactive", "--no-tag"]
    )

    assert commit_created(test_repo)
    assert not tag_created(test_repo)


def test_no_tag_no_push(test_repo: Path) -> None:
    _, previous_commit = tbump.git.run_git_captured(test_repo, "rev-parse", "HEAD")
    tbump.git.run_git(test_repo, "branch", "--unset-upstream")

    tbump.main.main(
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
