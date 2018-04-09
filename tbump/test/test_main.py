import toml
from tbump.test.conftest import assert_in_file

import pytest

import tbump.main
import tbump.git


def test_replaces(test_repo):
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])

    toml_path = test_repo.joinpath("tbump.toml")
    new_toml = toml.loads(toml_path.text())
    assert new_toml["version"]["current"] == "1.2.41-alpha-2"

    assert_in_file("package.json", '"version": "1.2.41-alpha-2"')
    assert_in_file("package.json", '"other-dep": "1.2.41-alpha-1"')
    assert_in_file("pub.js", "PUBLIC_VERSION = '1.2.41'")


def test_tbump_toml_not_found(test_repo, message_recorder):
    toml_path = test_repo.joinpath("tbump.toml")
    toml_path.remove()
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.42", "--non-interactive"])
    assert message_recorder.find("No such file")


def test_tbump_toml_bad_syntax(test_repo, message_recorder):
    toml_path = test_repo.joinpath("tbump.toml")
    bad_toml = toml.loads(toml_path.text())
    del bad_toml["git"]
    toml_path.write_text(toml.dumps(bad_toml))
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.42", "--non-interactive"])
    assert message_recorder.find("Missing keys")


def test_new_version_does_not_match(test_repo, message_recorder):
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.41a2", "--non-interactive"])
    assert message_recorder.find("Could not parse 1.2.41a2")


def test_abort_if_file_does_not_exist(test_repo, message_recorder):
    test_repo.joinpath("package.json").remove()
    tbump.git.run_git(test_repo, "add", "--update")
    tbump.git.run_git(test_repo, "commit", "--message", "remove package.json")
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])
    assert message_recorder.find("package.json does not exist")


def test_commit_and_tag(test_repo):
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])

    _, out = tbump.git.run_git_captured(test_repo, "log", "--oneline")
    assert "Bump to 1.2.41-alpha-2" in out

    _, out = tbump.git.run_git_captured(test_repo, "tag", "--list")
    assert out == "v1.2.41-alpha-2"


def test_abort_if_dirty(test_repo, message_recorder):
    test_repo.joinpath("VERSION").write_text("unstaged changes\n", append=True)

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--non-interactive"])
    assert message_recorder.find("dirty")


def test_abort_if_tag_exists(test_repo, message_recorder):
    tbump.git.run_git(test_repo, "tag", "v1.2.42")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.42", "--non-interactive"])
    assert message_recorder.find("1.2.42 already exists")


def test_abort_if_file_does_not_match(test_repo, message_recorder):
    invalid_src = test_repo.joinpath("foo.txt")
    invalid_src.write_text("this is foo")
    tbump_path = test_repo.joinpath("tbump.toml")
    tbump_path.write_text("""\
    [[file]]
    src = "foo.txt"
    """, append=True)
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(test_repo, "commit", "--message", "add foo.txt")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.42", "--non-interactive"])
    assert message_recorder.find("did not match")
    assert message_recorder.find("foo\.txt")
    assert_in_file("VERSION", "1.2.41-alpha-1")


def test_no_tracked_branch_proceed_and_skip_push(test_repo, mock):
    ask_mock = mock.patch("ui.ask_yes_no")
    ask_mock.return_value = True
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    tbump.main.main(["-C", test_repo, "1.2.42"])

    ask_mock.assert_called_with("Continue anyway?", default=False)
    assert_in_file("VERSION", "1.2.42")


def test_no_tracked_branch_cancel(test_repo, mock, message_recorder):
    ask_mock = mock.patch("ui.ask_yes_no")
    ask_mock.return_value = False
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.42"])

    ask_mock.assert_called_with("Continue anyway?", default=False)
    assert_in_file("VERSION", "1.2.41")
    assert message_recorder.find("Cancelled")


def test_no_tracked_branch_non_interactive(test_repo,  message_recorder):
    tbump.git.run_git(test_repo, "checkout", "-b", "devel")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.42", "--non-interactive"])
    assert message_recorder.find("Cannot push")


def test_interactive_push(test_repo, mock):
    ask_mock = mock.patch("ui.ask_yes_no")
    ask_mock.return_value = True
    tbump.main.main(["-C", test_repo, "1.2.42"])
    ask_mock.assert_called_with("OK to push", default=False)
    _, out = tbump.git.run_git_captured(test_repo, "ls-remote")
    assert "tags/v1.2.42" in out


def test_do_not_add_untracked_files(test_repo):
    test_repo.joinpath("untracked.txt").write_text("please don't add me")
    tbump.main.main(["-C", test_repo, "1.2.42", "--non-interactive"])
    _, out = tbump.git.run_git_captured(test_repo, "show", "--stat", "HEAD")
    assert "untracked.txt" not in out


def test_dry_run(test_repo):
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--dry-run"])
    assert_in_file("VERSION", "1.2.41-alpha-1")


def test_bad_subsitiution(test_repo, message_recorder):
    toml_path = test_repo.joinpath("tbump.toml")
    new_toml = toml.loads(toml_path.text())
    new_toml["file"][0]["version_template"] = "{release}"
    toml_path.write_text(toml.dumps(new_toml))
    tbump.git.run_git(test_repo, "add", ".")
    tbump.git.run_git(test_repo, "commit", "--message", "update repo")
    with pytest.raises(SystemExit):
        tbump.main.main(["-C", test_repo, "1.2.42", "--dry-run"])
    assert message_recorder.find("refusing to replace by version containing 'None'")
