import re

from path import Path
import schema
import pytest

from tbump.hooks import HOOKS_CLASSES, BeforeCommitHook
import tbump.config
from tbump.config import Config


def assert_validation_error(config: Config, expected_message: str) -> None:
    try:
        tbump.config.validate_config(config)
        assert False, "shoud have raise schema error"
    except schema.SchemaError as error:
        assert expected_message in error.args[0]


@pytest.fixture(params=["tbump.toml", "pyproject.toml"])
def test_config(request, test_data_path: Path) -> Config:  # type: ignore
    return tbump.config.parse(test_data_path / request.param)


def test_happy_parse(test_config: Config) -> None:
    foo_json = tbump.config.File(
        src="package.json", search='"version": "{current_version}"'
    )
    version_txt = tbump.config.File(src="VERSION")
    pub_js = tbump.config.File(src="pub.js", version_template="{major}.{minor}.{patch}")
    glob = tbump.config.File(
        src="glob*.?", search='version_[a-z]+ = "{current_version}"'
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
  """

    assert test_config.version_regex.pattern == expected_pattern

    assert test_config.files == [foo_json, version_txt, pub_js, glob]

    assert test_config.current_version == "1.2.41-alpha-1"


def test_invalid_custom_template(test_config: Config) -> None:
    first_file = test_config.files[0]
    first_file.src = "pub.js"
    first_file.version_template = "{major}.{minor}.{no_such_group}"
    assert_validation_error(
        test_config,
        "version template for 'pub.js' contains unknown group: 'no_such_group'",
    )


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


# --------------------------------------------

INVALID_REGEX_CONFIG_TEMPLATE = r"""
        [@key_prefix@version]
        current = '1.42a1'
        regex = '(unbalanced'

        [@key_prefix@git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[@key_prefix@file]]
        src = "VERSION"
"""


@pytest.fixture()
def invalid_regex_tbump_toml_config() -> str:
    return INVALID_REGEX_CONFIG_TEMPLATE.replace("@key_prefix@", "")


@pytest.fixture()
def invalid_regex_pyproject_toml_config() -> str:
    return INVALID_REGEX_CONFIG_TEMPLATE.replace("@key_prefix@", "tool.tbump.")


@pytest.mark.parametrize(
    "config_filename,config_contents",
    # fmt: off
    [
        pytest.param("tbump.toml", pytest.lazy_fixture("invalid_regex_tbump_toml_config"), id="tbump.toml"),  # type: ignore  # noqa
        pytest.param("pyproject.toml", pytest.lazy_fixture("invalid_regex_pyproject_toml_config"), id="pyproject.toml")  # type: ignore  # noqa
    ]
    # fmt: on
)
def test_invalid_regex(
    tmp_path: Path, config_filename: str, config_contents: str
) -> None:
    toml_path = tmp_path / config_filename
    toml_path.write_text(config_contents)
    with pytest.raises(schema.SchemaError) as e:
        tbump.config.parse(toml_path)
    print(e)


# --------------------------------------------

HOOK_TEMPLATE = r"""
        [@key_prefix@version]
        current = "1.2.3"
        regex = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'

        [@key_prefix@git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[@key_prefix@file]]
        src = "pub.js"

        [[@key_prefix@before_commit]]
        name = "Check changelog"
        cmd = "grep -q {new_version} Changelog.md"

        [[@key_prefix@after_push]]
        name = "After push"
        cmd = "cargo publish"
"""


@pytest.fixture()
def hook_tbump_toml_config() -> str:
    return HOOK_TEMPLATE.replace("@key_prefix@", "")


@pytest.fixture()
def hook_pyproject_toml_config() -> str:
    return HOOK_TEMPLATE.replace("@key_prefix@", "tool.tbump.")


@pytest.mark.parametrize(
    "config_filename,config_contents",
    # fmt: off
    [
        pytest.param("tbump.toml", pytest.lazy_fixture("hook_tbump_toml_config"), id="tbump.toml"),  # type: ignore  # noqa
        pytest.param("pyproject.toml", pytest.lazy_fixture("hook_pyproject_toml_config"), id="pyproject.toml"),  # type: ignore  # noqa
    ]
    # fmt: on
)
def test_parse_hooks(
    tmp_path: Path, config_filename: str, config_contents: str
) -> None:
    toml_path = tmp_path / config_filename
    toml_path.write_text(config_contents)
    config = tbump.config.parse(toml_path)
    first_hook = config.hooks[0]
    assert first_hook.name == "Check changelog"
    assert first_hook.cmd == "grep -q {new_version} Changelog.md"
    expected_class = HOOKS_CLASSES["before_commit"]
    assert isinstance(first_hook, expected_class)

    second_hook = config.hooks[1]
    expected_class = HOOKS_CLASSES["after_push"]
    assert isinstance(second_hook, expected_class)


# --------------------------------------------

RETRO_COMPAT_HOOK_CONFIG_TEMPLATE = r"""
        [@key_prefix@version]
        current = "1.2.3"
        regex = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'

        [@key_prefix@git]
        message_template = "Bump to  {new_version}"
        tag_template = "v{new_version}"

        [[@key_prefix@file]]
        src = "pub.js"

        [[@key_prefix@hook]]
        name = "very old name"
        cmd = "old command"

        [[@key_prefix@before_push]]
        name = "deprecated name"
        cmd = "deprecated command"
"""


@pytest.fixture()
def retro_hook_compat_tbump_toml_config() -> str:
    return RETRO_COMPAT_HOOK_CONFIG_TEMPLATE.replace("@key_prefix@", "")


@pytest.fixture()
def retro_hook_compat_pyproject_toml_config() -> str:
    return RETRO_COMPAT_HOOK_CONFIG_TEMPLATE.replace("@key_prefix@", "tool.tbump.")


@pytest.mark.parametrize(
    "config_filename,config_contents",
    # fmt: off
    [
        pytest.param("tbump.toml", pytest.lazy_fixture("retro_hook_compat_tbump_toml_config"), id="tbump.toml"),  # type: ignore  # noqa
        pytest.param("pyproject.toml", pytest.lazy_fixture("retro_hook_compat_pyproject_toml_config"), id="pyproject.toml"),  # type: ignore  # noqa
    ]
    # fmt: on
)
def test_retro_compat_hooks(
    tmp_path: Path, config_filename: str, config_contents: str
) -> None:
    toml_path = tmp_path / config_filename
    toml_path.write_text(config_contents)
    config = tbump.config.parse(toml_path)
    first_hook = config.hooks[0]
    assert isinstance(first_hook, tbump.hooks.BeforeCommitHook)
