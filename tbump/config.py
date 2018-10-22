import re
from typing import cast, Any, Dict, List, Optional, Pattern  # noqa

import attr
import schema
from path import Path
import toml

from .hooks import HOOKS_CLASSES, Hook, BeforeCommitHook, AfterPushHook  # noqa


@attr.s
class Config:
    current_version = attr.ib()  # type: str
    version_regex = attr.ib()  # type: Pattern
    tag_template = attr.ib(default="")  # type: str
    message_template = attr.ib(default=None)  # type: str
    files = attr.ib(default=list())  # type: List[File]
    hooks = attr.ib(default=list())  # type: List[Hook]


@attr.s
class File:
    src = attr.ib()  # type: str
    search = attr.ib(default=None)  # type: Optional[str]
    version_template = attr.ib(default=None)  # type: Optional[str]


class ValidTemplate():
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


def validate_version_template(src: str, version_template: str,
                              known_groups: Dict[str, str]) -> None:
    try:
        version_template.format(**known_groups)
    except KeyError as e:
        message = "version template for '%s' contains unknown group: %s" % (src, e)
        raise schema.SchemaError(message)


def validate(config: Dict[str, Any]) -> Config:
    file_schema = schema.Schema({
        "src": str,
        schema.Optional("search"): str,
        schema.Optional("version_template"): str,
    })

    hook_schema = schema.Schema({
        "name": str,
        "cmd": str,
    })

    def compile_re(regex: str) -> Pattern:
        return re.compile(regex, re.VERBOSE)

    tbump_schema = schema.Schema(
        {
            "version":  {
                "current": str,
                "regex": schema.Use(compile_re),
            },
            "git": {
                "message_template": ValidMessage(),
                "tag_template": ValidTag(),
            },
            "file": [file_schema],
            schema.Optional("hook"): [hook_schema],    # retro-compat
            schema.Optional("before_push"): [hook_schema],    # retro-compat
            schema.Optional("before_commit"): [hook_schema],
            schema.Optional("after_push"): [hook_schema],
            }
    )
    return cast(Config, tbump_schema.validate(config))


def parse(cfg_path: Path) -> Config:
    parsed = None
    with cfg_path.open() as stream:
        parsed = toml.load(stream)

    parsed = validate(parsed)  # type: ignore
    current_version = parsed["version"]["current"]
    version_regex = parsed["version"]["regex"]
    match = version_regex.fullmatch(current_version)
    if not match:
        message = "Current version: %s does not match version regex" % current_version
        raise schema.SchemaError(message)
    current_groups = match.groupdict()
    config = Config(
        current_version=current_version,
        version_regex=version_regex
    )

    config.tag_template = parsed["git"]["tag_template"]
    config.message_template = parsed["git"]["message_template"]

    config.files = list()
    for file_dict in parsed["file"]:
        file_config = File(
            src=file_dict["src"],
            search=file_dict.get("search"),
            version_template=file_dict.get("version_template"),
        )
        if file_config.version_template:
            validate_version_template(
                file_config.src,
                file_config.version_template,
                current_groups
            )
        config.files.append(file_config)

    config.hooks = list()
    for hook_type in ("hook", "before_push", "before_commit", "after_push"):
        cls = HOOKS_CLASSES[hook_type]
        if hook_type in parsed:
            for hook_dict in parsed[hook_type]:
                hook = cls(hook_dict["name"], hook_dict["cmd"])
                config.hooks.append(hook)
    return config
