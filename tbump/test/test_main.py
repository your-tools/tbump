import subprocess
import textwrap

import toml
import path
import pytest
from ui.tests.conftest import message_recorder

import tbump.main
import tbump.git


def assert_in_file(file_name, expected_line):
    file_path = path.Path(file_name)
    for line in file_path.lines():
        if expected_line in line:
            return
    assert False, "No line found matching %s" % expected_line


def setup_test(test_path, tmp_path, monkeypatch):
    src_path = tmp_path.joinpath("src")
    src_path.mkdir()
    test_path.joinpath("tbump.toml").copy(src_path)
    src_path.joinpath("VERSION").write_text("1.2.41")
    src_path.joinpath("package.json").write_text(textwrap.dedent("""
    {
       "name": "foo",
       "version": "1.2.41",
       "dependencies": {
         "some-dep": "1.3",
         "other-dep": "1.2.41"
       }
    }
    """))
    tbump.git.run_git(src_path, "init")
    tbump.git.run_git(src_path, "add", ".")
    tbump.git.run_git(src_path, "commit", "--message", "initial commit")
    setup_remote(tmp_path)
    return src_path


def setup_remote(tmp_path):
    git_path = tmp_path.joinpath("git")
    git_path.mkdir()
    remote_path = git_path.joinpath("repo.git")
    remote_path.mkdir()
    tbump.git.run_git(remote_path, "init", "--bare")

    src_path = tmp_path.joinpath("src")
    tbump.git.run_git(src_path, "remote", "add", "origin", remote_path)
    tbump.git.run_git(src_path, "push", "-u", "origin", "master")


def test_replaces(tmp_path, test_path, monkeypatch):
    src_path = setup_test(test_path, tmp_path, monkeypatch)
    tbump.main.main(["-C", src_path, "1.2.42-alpha-1", "--non-interactive"])

    toml_path = src_path.joinpath("tbump.toml")
    new_toml = toml.loads(toml_path.text())
    assert new_toml["version"]["current"] == "1.2.42-alpha-1"

    assert_in_file("package.json", '"version": "1.2.42-alpha-1"')
    assert_in_file("package.json", '"other-dep": "1.2.41"')


def test_commit_and_tag(tmp_path, test_path, monkeypatch):
    src_path = setup_test(test_path, tmp_path, monkeypatch)
    tbump.main.main(["-C", src_path, "1.2.42-alpha-1", "--non-interactive"])

    rc, out = tbump.git.run_git(src_path, "log", "--oneline", raises=False)
    assert rc == 0
    assert "Bump to 1.2.42-alpha-1" in out

    rc, out = tbump.git.run_git(src_path, "tag", "--list", raises=False)
    assert rc == 0
    assert out == "v1.2.42-alpha-1"


def test_abort_if_dirty(tmp_path, test_path, monkeypatch, message_recorder):
    src_path = setup_test(test_path, tmp_path, monkeypatch)
    src_path.joinpath("VERSION").write_text("unstaged changes\n", append=True)

    with pytest.raises(SystemExit) as e:
        tbump.main.main(["-C", src_path, "1.2.42-alpha-1", "--non-interactive"])
    assert message_recorder.find("dirty")


def test_abort_if_tag_exists(tmp_path, test_path, monkeypatch, message_recorder):
    src_path = setup_test(test_path, tmp_path, monkeypatch)
    tbump.git.run_git(src_path, "tag", "v1.2.42")

    with pytest.raises(SystemExit) as e:
        tbump.main.main(["-C", src_path, "1.2.42", "--non-interactive"])
    assert message_recorder.find("1.2.42 already exists")


def test_abort_if_file_does_not_change(tmp_path, test_path, monkeypatch, message_recorder):
    src_path = setup_test(test_path, tmp_path, monkeypatch)
    invalid_src = src_path.joinpath("foo.txt")
    invalid_src.write_text("this is foo")
    tbump_path = src_path.joinpath("tbump.toml")
    tbump_path.write_text("""\
    [[file]]
    src = "foo.txt"
    """, append=True)
    tbump.git.run_git(src_path, "add", ".")
    tbump.git.run_git(src_path, "commit", "--message", "add foo.txt")

    with pytest.raises(SystemExit):
        tbump.main.main(["-C", src_path, "1.2.42", "--non-interactive"])
    assert "foo.txt did not change"


def test_interactive_push(tmp_path, test_path, monkeypatch, message_recorder, mock):
    src_path = setup_test(test_path, tmp_path, monkeypatch)
    ask_mock = mock.patch("ui.ask_yes_no")
    ask_mock.return_value = True
    tbump.main.main(["-C", src_path, "1.2.42"])
    ask_mock.assert_called_with("OK to push", default=False)
    rc, out = tbump.git.run_git(src_path, "ls-remote", raises=False)
    assert rc == 0
    assert "tags/v1.2.42" in out
