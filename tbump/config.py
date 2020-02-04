import re
from typing import cast, Any, Dict, List, Optional, Pattern  # noqa

import attr
import schema
from path import Path
import tomlkit

from .hooks import HOOKS_CLASSES, Hook, BeforeCommitHook, AfterPushHook  # noqa


@attr.s
class Config:
    current_version = attr.ib()  # type: str
    version_regex = attr.ib()  # type: Pattern[str]
    message_template = attr.ib()  # type: str
    files = attr.ib()  # type: List[File]
    hooks = attr.ib()  # type: List[Hook]
    tag_template = attr.ib()  # type: str


@attr.s
class File:
    src = attr.ib()  # type: str
    search = attr.ib(default=None)  # type: Optional[str]
    version_template = attr.ib(default=None)  # type: Optional[str]


class ValidTemplate:
    def __init__(self, name: str, pattern: str):
        self.name = name
        self.pattern = pattern
        self.message = "%s should contain the string %s" % (name, pattern)

    def validate(self, value: str) -> str:
        if self.pattern not in value:
            raise schema.SchemaError(self.message)
        return value


class ValidTag(ValidTemplate):
    def __init__(self) -> None:
        super().__init__("tag_template", "{new_version}")


class ValidMessage(ValidTemplate):
    def __init__(self) -> None:
        super().__init__("message_template", "{new_version}")


def validate_version_template(
    src: str, version_template: str, known_groups: Dict[str, str]
) -> None:
    try:
        version_template.format(**known_groups)
    except KeyError as e:
        message = "version template for '%s' contains unknown group: %s" % (src, e)
        raise schema.SchemaError(message)


def validate(config: Dict[str, Any]) -> Config:
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
            "git": {"message_template": ValidMessage(), "tag_template": ValidTag()},
            "file": [file_schema],
            schema.Optional("hook"): [hook_schema],  # retro-compat
            schema.Optional("before_push"): [hook_schema],  # retro-compat
            schema.Optional("before_commit"): [hook_schema],
            schema.Optional("after_push"): [hook_schema],
        }
    )
    return cast(Config, tbump_schema.validate(config))


def parse(cfg_path: Path) -> Config:
    parsed = tomlkit.loads(cfg_path.text())
    parsed = validate(parsed)
    current_version = parsed["version"]["current"]
    version_regex = re.compile(parsed["version"]["regex"], re.VERBOSE)
    match = version_regex.fullmatch(current_version)
    if not match:
        message = "Current version: %s does not match version regex" % current_version
        raise schema.SchemaError(message)
    current_groups = match.groupdict()
    message_template = parsed["git"]["message_template"]
    tag_template = parsed["git"]["tag_template"]
    files = []
    for file_dict in parsed["file"]:
        file_config = File(
            src=file_dict["src"],
            search=file_dict.get("search"),
            version_template=file_dict.get("version_template"),
        )
        if file_config.version_template:
            validate_version_template(
                file_config.src, file_config.version_template, current_groups
            )
        files.append(file_config)

    hooks = []
    for hook_type in ("hook", "before_push", "before_commit", "after_push"):
        cls = HOOKS_CLASSES[hook_type]
        if hook_type in parsed:
            for hook_dict in parsed[hook_type]:
                hook = cls(hook_dict["name"], hook_dict["cmd"])
                hooks.append(hook)

    config = Config(
        current_version=current_version,
        version_regex=version_regex,
        message_template=message_template,
        tag_template=tag_template,
        files=files,
        hooks=hooks,
    )

    return config
