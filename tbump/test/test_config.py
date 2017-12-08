import re

import path
import pytest
import schema

import tbump.config


def test_happy_parse(monkeypatch):
    this_dir = path.Path(__file__).parent
    monkeypatch.chdir(this_dir)
    config = tbump.config.parse(path.Path("tbump.toml"))
    foo_json = tbump.config.File(
        src="package.json",
        search='"version": "{current_version}"'
    )
    version_txt = tbump.config.File(src="VERSION")

    assert config.files == [
        foo_json,
        version_txt,
    ]

    assert config.current_version == "1.2.41"


def test_wrong_syntax():
    this_dir = path.Path(__file__).parent
    invalid_path = this_dir.abspath().joinpath("invalid.toml")

    with pytest.raises(schema.SchemaError) as e:
        tbump.config.parse(invalid_path)
    assert "should contain" in e.value.args[0]
