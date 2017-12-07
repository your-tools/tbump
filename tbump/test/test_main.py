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
    toml_path = test_path.joinpath("tbump.toml").copy(tmp_path)
    tmp_path.joinpath("VERSION").write_text("1.2.41")
    tmp_path.joinpath("package.json").write_text(textwrap.dedent("""
    {
       "name": "foo",
       "version": "1.2.41",
       "dependencies": {
         "some-dep": "1.3",
         "other-dep": "1.2.41"
       }
    }
    """))
    tbump.git.run_git(tmp_path, "init")
    tbump.git.run_git(tmp_path, "add", ".")
    tbump.git.run_git(tmp_path, "commit", "--message", "initial commit")


def test_replaces(tmp_path, test_path, monkeypatch):
    setup_test(test_path, tmp_path, monkeypatch)
    tbump.main.main(["-C", tmp_path, "1.2.42-alpha-1"])

    toml_path = tmp_path.joinpath("tbump.toml")
    new_toml = toml.loads(toml_path.text())
    assert new_toml["version"]["current"] == "1.2.42-alpha-1"

    assert_in_file("package.json", '"version": "1.2.42-alpha-1"')
    assert_in_file("package.json", '"other-dep": "1.2.41"')


def test_commit_and_tag(tmp_path, test_path, monkeypatch):
    setup_test(test_path, tmp_path, monkeypatch)
    tbump.main.main(["-C", tmp_path, "1.2.42-alpha-1"])

    rc, out = tbump.git.run_git(tmp_path, "log", "--oneline", raises=False)
    assert rc == 0
    assert "Bump to 1.2.42-alpha-1" in out

    rc, out = tbump.git.run_git(tmp_path, "tag", "--list", raises=False)
    assert rc == 0
    assert out == "v1.2.42-alpha-1"


def test_abort_if_dirty(tmp_path, test_path, monkeypatch, message_recorder):
    setup_test(test_path, tmp_path, monkeypatch)
    tmp_path.joinpath("VERSION").write_text("unstaged changes\n", append=True)

    with pytest.raises(SystemExit) as e:
        tbump.main.main(["-C", tmp_path, "1.2.42-alpha-1"])
    assert message_recorder.find("dirty")
