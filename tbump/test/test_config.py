from typing import Any
from path import Path
import schema

from tbump.hooks import HOOKS_CLASSES
import tbump.config


def test_happy_parse(test_data_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(test_data_path)
    config = tbump.config.parse(test_data_path / "tbump.toml")
    foo_json = tbump.config.File(
        src="package.json",
        search='"version": "{current_version}"'
    )
    version_txt = tbump.config.File(src="VERSION")
    pub_js = tbump.config.File(
        src="pub.js",
        version_template="{major}.{minor}.{patch}")

    expected_pattern = r"""  (?P<major>\d+)
  \.
  (?P<minor>\d+)
  \.
  (?P<patch>\d+)
  (
    -
    (?P<channel>alpha|beta)
    -
    (?P<release>\d+)
  )?
  """

    assert config.version_regex.pattern == expected_pattern

    assert config.files == [
        foo_json,
        version_txt,
        pub_js,
    ]

    assert config.current_version == "1.2.41-alpha-1"


def check_error(tmp_path: Path, contents: str, expected_message: str) -> None:
    cfg_path = tmp_path / "tbump.toml"
    cfg_path.write_text(contents)
    try:
        tbump.config.parse(cfg_path)
        assert False, "shoud have raise schema error"
    except schema.SchemaError as error:
        assert expected_message in error.args[0]


def test_invalid_commit_message(tmp_path: Path) -> None:
    check_error(
        tmp_path,
        r"""
        [version]
        current = '1.2'
        regex = ".*"

        [git]
        message_template = "invalid message"
        tag_template = "v{new_version}"

        [[file]]
        src = "VERSION"
        """,
        "message_template should contain the string {new_version}"
    )


def test_current_version_does_not_match_expected_regex(tmp_path: Path) -> None:
    check_error(
        tmp_path,
        r"""
        [version]
        current = '1.42a1'
        regex = '(\d+)\.(\d+)\.(\d+)'

        [git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "VERSION"
        """,
        "Current version: 1.42a1 does not match version regex"
    )


def test_invalid_regex(tmp_path: Path) -> None:
    check_error(
        tmp_path,
        r"""
        [version]
        current = '1.42a1'
        regex = '(unbalanced'

        [git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "VERSION"
        """,
        "Key 'regex' error"
    )


def test_invalid_custom_template(tmp_path: Path) -> None:
    check_error(
        tmp_path,
        r"""
        [version]
        current = "1.2.3"
        regex = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'

        [git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "pub.js"
        version_template = "{major}.{minor}.{no_such_group}"
        """,
        "version template for 'pub.js' contains unknown group: 'no_such_group'"
    )


def test_parse_hooks(tmp_path: Path) -> None:
    toml_path = tmp_path / "tbump.toml"
    toml_path.write_text(r"""
        [version]
        current = "1.2.3"
        regex = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'

        [git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "pub.js"

        [[before_commit]]
        name = "Check changelog"
        cmd = "grep -q {new_version} Changelog.md"

        [[after_push]]
        name = "After push"
        cmd = "cargo publish"
    """)
    config = tbump.config.parse(toml_path)
    first_hook = config.hooks[0]
    assert first_hook.name == "Check changelog"
    assert first_hook.cmd == "grep -q {new_version} Changelog.md"
    expected_class = HOOKS_CLASSES["before_commit"]
    assert isinstance(first_hook, expected_class)

    second_hook = config.hooks[1]
    expected_class = HOOKS_CLASSES["after_push"]
    assert isinstance(second_hook, expected_class)


def test_retro_compat_hooks(tmp_path: Path) -> None:
    toml_path = tmp_path / "tbump.toml"
    toml_path.write_text(r"""
        [version]
        current = "1.2.3"
        regex = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'

        [git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "pub.js"

        [[hook]]
        name = "very old name"
        cmd = "old command"

        [[before_push]]
        name = "deprecated name"
        cmd = "deprecated command"
      """)
    config = tbump.config.parse(toml_path)
    first_hook = config.hooks[0]
    assert isinstance(first_hook, tbump.hooks.BeforeCommitHook)
