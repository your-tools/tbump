import subprocess
import textwrap

import toml
import path
import pytest

import tbump.main


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
    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "--message", "initial commit"])

    monkeypatch.chdir(tmp_path)


def test_main(tmp_path, test_path, monkeypatch):
    setup_test(test_path, tmp_path, monkeypatch)
    tbump.main.main(["1.2.42-alpha-1"])

    toml_path = tmp_path.joinpath("tbump.toml")
    new_toml = toml.loads(toml_path.text())
    assert new_toml["version"]["current"] == "1.2.42-alpha-1"

    assert_in_file("package.json", '"version": "1.2.42-alpha-1"')
    assert_in_file("package.json", '"other-dep": "1.2.41"')


def test_git(tmp_path, test_path, monkeypatch):
    setup_test(test_path, tmp_path, monkeypatch)

    tbump.main.main(["1.2.42-alpha-1"])
