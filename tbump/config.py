import os
import re

import attr
import schema
import toml
import ui


@attr.s
class Config:
    current_version = attr.ib()
    version_regex = attr.ib()
    tag_template = attr.ib(default=None)
    message_template = attr.ib(default=None)
    files = attr.ib(default=None)


@attr.s
class File:
    src = attr.ib()
    search = attr.ib(default=None)
    version_template = attr.ib(default=None)


class ValidTemplate():
    def __init__(self, name, pattern):
        self.name = name
        self.pattern = pattern
        self.message = "%s should contain the string %s" % (name, pattern)

    def validate(self, value):
        if self.pattern not in value:
            raise schema.SchemaError(self.message)
        return value


class ValidTag(ValidTemplate):
    def __init__(self):
        super().__init__("tag_template", "{new_version}")


class ValidMessage(ValidTemplate):
    def __init__(self):
        super().__init__("message_template", "{new_version}")


def validate_version_template(src, version_template, known_groups):
    try:
        version_template.format(**known_groups)
    except KeyError as e:
        message = "version template for '%s' contains unknown group: %s" % (src, e)
        raise schema.SchemaError(message)


def validate(config):
    file_schema = schema.Schema({
        "src": str,
        schema.Optional("search"): str,
        schema.Optional("version_template"): str,
    })

    def compile_re(regex):
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
        }
    )
    return tbump_schema.validate(config)


def parse(cfg_path):
    parsed = None
    with cfg_path.open() as stream:
        parsed = toml.load(stream)

    parsed = validate(parsed)
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
    return config
