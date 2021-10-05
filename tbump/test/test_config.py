import re
import textwrap
from pathlib import Path

import pytest
import schema
import tomlkit

from tbump.config import (
    Config,
    Field,
    File,
    InvalidConfig,
    TbumpTomlConfig,
    from_parsed_config,
    get_config_file,
    validate_basic_schema,
    validate_config,
)
from tbump.hooks import HOOKS_CLASSES, BeforeCommitHook


def test_happy_parse(test_project: Path) -> None:
    config_file = get_config_file(test_project)
    config = config_file.get_config()
    foo_json = File(src="package.json", search='"version": "{current_version}"')
    version_txt = File(src="VERSION")
    pub_js = File(src="pub.js", version_template="{major}.{minor}.{patch}")
    glob = File(src="glob*.?", search='version_[a-z]+ = "{current_version}"')
    version_info = File(
        src="version_info.py",
        search="version_info = {current_version}",
        version_template='({major}, {minor}, {patch}, "{channel}", {release})',
    )

    channel = Field(
        name="channel",
        default="",
    )
    release = Field(
        name="release",
        default=0,
    )

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
  (
    \+
    (?P<build>[a-z0-9\.]+)
  )?
  """

    assert config.version_regex.pattern == expected_pattern

    assert config.files == [foo_json, version_txt, pub_js, glob, version_info]
    assert config.fields == [channel, release]

    assert config.current_version == "1.2.41-alpha-1"


def test_uses_pyproject_if_tbump_toml_is_missing(
    test_project: Path, tmp_path: Path
) -> None:

    expected_file = get_config_file(test_project)
    parsed_config = expected_file.get_parsed()
    tools_config = tomlkit.table()
    tools_config.add("tbump", parsed_config)

    pyproject_config = tomlkit.document()
    pyproject_config["tool"] = tools_config
    to_write = tomlkit.dumps(pyproject_config)

    pyproject_toml = tmp_path / "pyproject.toml"
    pyproject_toml.write_text(to_write)

    actual_file = get_config_file(tmp_path)
    assert actual_file.get_config() == expected_file.get_config()


def test_complain_if_pyproject_does_not_contain_tbump_config(tmp_path: Path) -> None:
    pyproject_toml = tmp_path / "pyproject.toml"
    to_write = textwrap.dedent(
        r"""
    [tool.isort]
    profile = "black"
    """
    )
    pyproject_toml.write_text(to_write)

    with pytest.raises(InvalidConfig):
        get_config_file(tmp_path)


def test_use_specified_path(tmp_path: Path, test_project: Path) -> None:
    other_path = tmp_path / "other.toml"
    test_toml = test_project / "tbump.toml"
    other_path.write_text(test_toml.read_text())
    expected_file = get_config_file(tmp_path, specified_config_path=other_path)
    assert isinstance(expected_file, TbumpTomlConfig)


def test_raise_when_specified_path_does_not_exists(tmp_path: Path) -> None:
    with pytest.raises(InvalidConfig):
        get_config_file(tmp_path, specified_config_path=tmp_path / "no-such.toml")


def test_validate_schema_in_pyproject_toml(tmp_path: Path) -> None:
    pyproject_toml = tmp_path / "pyproject.toml"
    to_write = textwrap.dedent(
        r"""
        [[tool.tbump.file]]
        search = '"version": "{current_version}"'
        src = "package.json"

        [tool.tbump.git]
        message_template = "Bump to {new_version}"
        tag_template = "v{new_version}"

        [tool.tbump.version]
        # Note: missing 'current'
        regex = '''
          (?P<major>\d+)
          \.
          (?P<minor>\d+)
          \.
          (?P<patch>\d+)
          '''
       """
    )
    pyproject_toml.write_text(to_write)

    with pytest.raises(InvalidConfig) as e:
        get_config_file(tmp_path)
    assert "'current'" in str(e.value.parse_error)


def assert_validation_error(config: Config, expected_message: str) -> None:
    try:
        validate_config(config)
        pytest.fail("should have raised schema error")
    except schema.SchemaError as error:
        assert expected_message in error.args[0]


@pytest.fixture
def test_config(test_project: Path) -> Config:
    config_file = get_config_file(test_project)
    return config_file.get_config()


def test_invalid_commit_message(test_config: Config) -> None:
    test_config.git_message_template = "invalid message"
    assert_validation_error(
        test_config, "git.message_template should contain the string {new_version}"
    )


def test_invalid_hook_cmd(test_config: Config) -> None:
    invalid_cmd = "grep -q {version} Changelog.rst"
    invalid_hook = BeforeCommitHook(name="check changelog", cmd=invalid_cmd)
    test_config.hooks.append(invalid_hook)
    assert_validation_error(
        test_config,
        "hook cmd: 'grep -q {version} Changelog.rst' uses unknown placeholder: 'version'",
    )


def test_current_version_does_not_match_expected_regex(test_config: Config) -> None:
    test_config.version_regex = re.compile(r"(\d+)\.(\d+)\.(\d+)")
    test_config.current_version = "1.42a1"
    assert_validation_error(
        test_config, "Current version: 1.42a1 does not match version regex"
    )


def test_invalid_regex() -> None:
    contents = textwrap.dedent(
        r"""
        [version]
        current = '1.42a1'
        regex = '(unbalanced'

        [git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "VERSION"
        """
    )
    data = tomlkit.loads(contents)
    with pytest.raises(schema.SchemaError) as e:
        validate_basic_schema(data.value)
    print(e)


def test_invalid_custom_template(test_config: Config) -> None:
    first_file = test_config.files[0]
    first_file.src = "pub.js"
    first_file.version_template = "{major}.{minor}.{no_such_group}"
    assert_validation_error(
        test_config,
        "version template for 'pub.js' contains unknown group: 'no_such_group'",
    )


def test_parse_hooks() -> None:
    contents = textwrap.dedent(
        r"""
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
    """
    )
    parsed = tomlkit.loads(contents)
    config = from_parsed_config(parsed.value)
    first_hook = config.hooks[0]
    assert first_hook.name == "Check changelog"
    assert first_hook.cmd == "grep -q {new_version} Changelog.md"
    expected_class = HOOKS_CLASSES["before_commit"]
    assert isinstance(first_hook, expected_class)

    second_hook = config.hooks[1]
    expected_class = HOOKS_CLASSES["after_push"]
    assert isinstance(second_hook, expected_class)


def test_retro_compat_hooks() -> None:
    contents = textwrap.dedent(
        r"""
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
      """
    )
    parsed = tomlkit.parse(contents)
    config = from_parsed_config(parsed.value)
    first_hook = config.hooks[0]
    assert isinstance(first_hook, BeforeCommitHook)
