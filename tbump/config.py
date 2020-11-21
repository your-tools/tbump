import re
from typing import cast, Any, Dict, List, Optional, Pattern  # noqa

import attr
import schema
from pathlib import Path
import tomlkit

from .hooks import HOOKS_CLASSES, Hook


@attr.s
class Config:
    current_version = attr.ib()  # type: str
    version_regex = attr.ib()  # type: Pattern[str]

    git_tag_template = attr.ib()  # type: str
    git_message_template = attr.ib()  # type: str

    files = attr.ib()  # type: List[File]
    hooks = attr.ib()  # type: List[Hook]

    github_url = attr.ib()  # type: Optional[str]


@attr.s
class File:
    src = attr.ib()  # type: str
    search = attr.ib(default=None)  # type: Optional[str]
    version_template = attr.ib(default=None)  # type: Optional[str]


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


def validate_basic_schema(config: Dict[str, Any]) -> Config:
    """ First pass of validation, using schema """
    # Note: asserts that we won't get KeyError or invalid types
    # when building or initial Config instance
    file_schema = schema.Schema(
        {
            "src": str,
            schema.Optional("search"): str,
            schema.Optional("version_template"): str,
        }
    )

    hook_schema = schema.Schema({"name": str, "cmd": str})

    def validate_re(regex: str) -> str:
        re.compile(regex, re.VERBOSE)
        return regex

    tbump_schema = schema.Schema(
        {
            "version": {"current": str, "regex": schema.Use(validate_re)},
            "git": {"message_template": str, "tag_template": str},
            "file": [file_schema],
            schema.Optional("hook"): [hook_schema],  # retro-compat
            schema.Optional("before_push"): [hook_schema],  # retro-compat
            schema.Optional("before_commit"): [hook_schema],
            schema.Optional("after_push"): [hook_schema],
            schema.Optional("github_url"): str,
        }
    )
    return cast(Config, tbump_schema.validate(config))


def validate_config(cfg: Config) -> None:
    """ Second pass of validation, using the Config
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


def parse(cfg_path: Path) -> Config:
    parsed = tomlkit.loads(cfg_path.read_text())
    parsed = validate_basic_schema(parsed)
    current_version = parsed["version"]["current"]
    git_message_template = parsed["git"]["message_template"]
    git_tag_template = parsed["git"]["tag_template"]
    version_regex = re.compile(parsed["version"]["regex"], re.VERBOSE)
    files = []
    for file_dict in parsed["file"]:
        file_config = File(
            src=file_dict["src"],
            search=file_dict.get("search"),
            version_template=file_dict.get("version_template"),
        )
        files.append(file_config)

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
        files=files,
        hooks=hooks,
        github_url=github_url,
    )

    validate_config(config)

    return config
