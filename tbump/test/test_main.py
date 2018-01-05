import subprocess
import textwrap

import toml
import path
import pytest
from ui.tests.conftest import message_recorder
from tbump.test.conftest import assert_in_file

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

    rc, out = tbump.git.run_git(test_repo, "log", "--oneline", raises=False)
    assert rc == 0
    assert "Bump to 1.2.41-alpha-2" in out

    rc, out = tbump.git.run_git(test_repo, "tag", "--list", raises=False)
    assert rc == 0
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


def test_interactive_push(test_repo, message_recorder, mock):
    ask_mock = mock.patch("ui.ask_yes_no")
    ask_mock.return_value = True
    tbump.main.main(["-C", test_repo, "1.2.42"])
    ask_mock.assert_called_with("OK to push", default=False)
    rc, out = tbump.git.run_git(test_repo, "ls-remote", raises=False)
    assert rc == 0
    assert "tags/v1.2.42" in out


def test_do_not_add_untracked_files(test_repo):
    test_repo.joinpath("untracked.txt").write_text("please don't add me")
    tbump.main.main(["-C", test_repo, "1.2.42", "--non-interactive"])
    rc, out = tbump.git.run_git(test_repo, "show", "--stat", "HEAD", raises=False)
    assert rc == 0
    assert "untracked.txt" not in out


def test_dry_run(test_repo):
    tbump.main.main(["-C", test_repo, "1.2.41-alpha-2", "--dry-run"])

    toml_path = test_repo.joinpath("tbump.toml")
    assert_in_file("VERSION", "1.2.41-alpha-1")
