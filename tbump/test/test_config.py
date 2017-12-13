import re

import path
import pytest
import schema

import tbump.config


def test_happy_parse(monkeypatch, complex_version_regex):
    this_dir = path.Path(__file__).parent
    monkeypatch.chdir(this_dir)
    config = tbump.config.parse(path.Path("tbump.toml"))
    foo_json = tbump.config.File(
        src="package.json",
        search='"version": "{current_version}"'
    )
    version_txt = tbump.config.File(src="VERSION")
    pub_js = tbump.config.File(
        src="pub.js",
        version_template="{major}.{minor}.{patch}")

    assert config.version_regex.pattern == complex_version_regex.pattern

    assert config.files == [
        foo_json,
        version_txt,
        pub_js,
    ]

    assert config.current_version == "1.2.41-alpha-1"


def test_wrong_syntax():
    this_dir = path.Path(__file__).parent
    invalid_path = this_dir.abspath().joinpath("invalid.toml")

    with pytest.raises(schema.SchemaError) as e:
        tbump.config.parse(invalid_path)
    assert "should contain" in e.value.args[0]
