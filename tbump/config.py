import abc
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union

import cli_ui as ui
import schema
import tomlkit
from tomlkit.toml_document import TOMLDocument

from tbump.action import Action
from tbump.error import Error
from tbump.hooks import HOOKS_CLASSES, Hook


@dataclass
class File:
    src: str
    search: Optional[str] = None
    version_template: Optional[str] = None


@dataclass
class Field:
    name: str
    default: Optional[Union[str, int]] = None


@dataclass
class Config:
    current_version: str
    version_regex: Pattern[str]

    git_tag_template: str
    git_message_template: str
    atomic_push: bool

    files: List[File]
    hooks: List[Hook]
    fields: List[Field]

    github_url: Optional[str]


class ConfigFileUpdater(Action, metaclass=abc.ABCMeta):
    """Base class representing a config file"""

    def __init__(self, project_path: Path, path: Path, doc: TOMLDocument):
        self.project_path = project_path
        self.path = path
        self.doc = doc

    @property
    def relative_path(self) -> Path:
        return self.path.relative_to(self.project_path)

    def print_self(self) -> None:
        from tbump.cli import print_diff

        old_text = self.path.read_text()
        new_text = tomlkit.dumps(self.doc)

        lineno = 1
        for old_line, new_line in zip(old_text.splitlines(), new_text.splitlines()):
            if old_line != new_line:
                print_diff(
                    str(self.relative_path),
                    lineno + 1,
                    old_line.strip(),
                    new_line.strip(),
                )
            lineno += 1

    def do(self) -> None:
        new_text = tomlkit.dumps(self.doc)
        self.path.write_text(new_text)

    @abc.abstractmethod
    def get_parsed(self) -> dict:
        """Return a plain dictionary, suitable for validation
        by the `schema` library
        """

    @abc.abstractmethod
    def set_new_version(self, version: str) -> None:
        pass

    def get_config(self) -> Config:
        """Return a validated Config instance"""
        parsed = self.get_parsed()
        res = from_parsed_config(parsed)
        validate_config(res)
        return res


class TbumpTomlUpdater(ConfigFileUpdater):
    """Represent config inside a tbump.toml file"""

    def __init__(self, project_path: Path, path: Path, doc: TOMLDocument):
        super().__init__(project_path, path, doc)

    def get_parsed(self) -> dict:
        # Document -> dict
        return self.doc.value

    def set_new_version(self, version: str) -> None:
        self.doc["version"]["current"] = version  # type: ignore[index]


class PyprojectUpdater(ConfigFileUpdater):
    """Represent a config inside a pyproject.toml file,
    under the [tool.tbump] key
    """

    def __init__(self, project_path: Path, path: Path, doc: TOMLDocument):
        super().__init__(project_path, path, doc)

    @staticmethod
    def unwrap_data(data: Any) -> Any:
        if hasattr(data, "unwrap") and callable(data.unwrap):
            return data.unwrap()
        else:
            return data

    def get_parsed(self) -> dict:
        try:
            tool_section = PyprojectUpdater.unwrap_data(
                self.doc["tool"]["tbump"]  # type: ignore[index]
            )
        except KeyError as e:
            raise InvalidConfig(parse_error=e)

        return tool_section  # type: ignore[no-any-return]

    def set_new_version(self, new_version: str) -> None:
        self.doc["tool"]["tbump"]["version"]["current"] = new_version  # type: ignore[index]


def validate_template(name: str, pattern: str, value: str) -> None:
    if pattern not in value:
        message = "%s should contain the string %s" % (name, pattern)
        raise schema.SchemaError(message)


def validate_git_tag_template(value: str) -> None:
    validate_template("git.tag_template", "{new_version}", value)


def validate_git_message_template(value: str) -> None:
    validate_template("git.message_template", "{new_version}", value)


def validate_version_template(
    src: str, version_template: str, known_groups: Dict[str, str]
) -> None:
    try:
        version_template.format(**known_groups)
    except KeyError as e:
        message = "version template for '%s' contains unknown group: %s" % (src, e)
        raise schema.SchemaError(message)


def validate_hook_cmd(cmd: str) -> None:
    try:
        cmd.format(new_version="dummy", current_version="dummy")
    except KeyError as e:
        message = "hook cmd: '%s' uses unknown placeholder: %s" % (cmd, e)
        raise schema.SchemaError(message)


def validate_basic_schema(config: dict) -> None:
    """First pass of validation, using schema"""
    # Note: asserts that we won't get KeyError or invalid types
    # when building or initial Config instance
    file_schema = schema.Schema(
        {
            "src": str,
            schema.Optional("search"): str,
            schema.Optional("version_template"): str,
        }
    )

    field_schema = schema.Schema(
        {
            "name": str,
            schema.Optional("default"): schema.Or(str, int),
        }
    )

    hook_schema = schema.Schema({"name": str, "cmd": str})

    def validate_re(regex: str) -> str:
        re.compile(regex, re.VERBOSE)
        return regex

    tbump_schema = schema.Schema(
        {
            "version": {"current": str, "regex": schema.Use(validate_re)},
            "git": {
                "message_template": str,
                "tag_template": str,
                schema.Optional("atomic_push"): bool,
            },
            "file": [file_schema],
            schema.Optional("field"): [field_schema],
            schema.Optional("hook"): [hook_schema],  # retro-compat
            schema.Optional("before_push"): [hook_schema],  # retro-compat
            schema.Optional("before_commit"): [hook_schema],
            schema.Optional("after_push"): [hook_schema],
            schema.Optional("github_url"): str,
        }
    )
    tbump_schema.validate(config)


def validate_config(cfg: Config) -> None:
    """Second pass of validation, using the Config
    class.

    """
    # Note: separated from validate_basic_schema to keep error
    # messages user friendly

    current_version = cfg.current_version

    validate_git_message_template(cfg.git_message_template)
    validate_git_tag_template(cfg.git_tag_template)

    match = cfg.version_regex.fullmatch(current_version)
    if not match:
        message = "Current version: %s does not match version regex" % current_version
        raise schema.SchemaError(message)
    current_version_regex_groups = match.groupdict()

    for file_config in cfg.files:
        version_template = file_config.version_template
        if version_template:
            validate_version_template(
                file_config.src, version_template, current_version_regex_groups
            )

    for hook in cfg.hooks:
        validate_hook_cmd(hook.cmd)


def get_config_file(
    project_path: Path, *, specified_config_path: Optional[Path] = None
) -> ConfigFileUpdater:
    try:
        config_type, config_path = _get_config_path_and_type(
            project_path, specified_config_path
        )
        res = _get_config_file(project_path, config_type, config_path)
        # Make sure config is correct before returning it
        res.get_config()
        return res
    except IOError as io_error:
        raise InvalidConfig(io_error=io_error)
    except schema.SchemaError as parse_error:
        raise InvalidConfig(parse_error=parse_error)


def _get_config_path_and_type(
    project_path: Path, specified_config_path: Optional[Path] = None
) -> Tuple[str, Path]:
    if specified_config_path:
        return "tbump.toml", specified_config_path

    toml_path = project_path / "tbump.toml"
    if toml_path.exists():
        return "tbump.toml", toml_path

    pyproject_path = project_path / "pyproject.toml"
    if pyproject_path.exists():
        return "pyproject.toml", pyproject_path

    raise ConfigNotFound(project_path)


def _get_config_file(
    project_path: Path, config_type: str, config_path: Path
) -> ConfigFileUpdater:
    if config_type == "tbump.toml":
        doc = tomlkit.loads(config_path.read_text())
        return TbumpTomlUpdater(project_path, config_path, doc)
    elif config_type == "pyproject.toml":
        doc = tomlkit.loads(config_path.read_text())
        return PyprojectUpdater(project_path, config_path, doc)
    raise ValueError("unknown config_type: {config_type}")


def from_parsed_config(parsed: dict) -> Config:
    validate_basic_schema(parsed)
    current_version = parsed["version"]["current"]
    git_message_template = parsed["git"]["message_template"]
    git_tag_template = parsed["git"]["tag_template"]
    atomic_push = parsed["git"].get("atomic_push", True)
    version_regex = re.compile(parsed["version"]["regex"], re.VERBOSE)
    files = []
    for file_dict in parsed["file"]:
        file_config = File(
            src=file_dict["src"],
            search=file_dict.get("search"),
            version_template=file_dict.get("version_template"),
        )
        files.append(file_config)
    fields = []
    for field_dict in parsed.get("field", []):
        field_config = Field(
            name=field_dict["name"],
            default=field_dict.get("default"),
        )
        fields.append(field_config)
    hooks = []
    for hook_type in ("hook", "before_push", "before_commit", "after_push"):
        cls = HOOKS_CLASSES[hook_type]
        if hook_type in parsed:
            for hook_dict in parsed[hook_type]:
                hook = cls(hook_dict["name"], hook_dict["cmd"])
                hooks.append(hook)

    github_url = parsed.get("github_url")

    config = Config(
        current_version=current_version,
        version_regex=version_regex,
        git_message_template=git_message_template,
        git_tag_template=git_tag_template,
        atomic_push=atomic_push,
        fields=fields,
        files=files,
        hooks=hooks,
        github_url=github_url,
    )

    validate_config(config)

    return config


class ConfigNotFound(Error):
    def __init__(self, project_path: Path):
        self.project_path = project_path

    def print_error(self) -> None:
        ui.error("No configuration for tbump found in", self.project_path)
        ui.info("Please run `tbump init` to create a tbump.toml file")
        ui.info("Or add a [tool.tbump] section in the pyproject.toml file")


class InvalidConfig(Error):
    def __init__(
        self,
        io_error: Optional[IOError] = None,
        parse_error: Optional[Exception] = None,
    ):
        super().__init__()
        self.io_error = io_error
        self.parse_error = parse_error

    def print_error(self) -> None:
        if self.io_error:
            ui.error("Could not read config file:", self.io_error)
        if self.parse_error:
            ui.error("Invalid config:", self.parse_error)
