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


class ValidTag():
    message = "tag_template should contain the string {new_version}"

    def validate(self, value):
        if "{new_version}" not in value:
            raise schema.SchemaError(self.message)
        return True


def validate(config):
    file_schema = schema.Schema({
        "src": str,
        schema.Optional("search"): str,
        schema.Optional("version_template"): str,
    })
    tbump_schema = schema.Schema(
      {
        "version":  {
          "current": str,
          "regex": str,
        },
        "git": {
          "message_template": str,
          "tag_template": ValidTag(),
        },
        "file": [file_schema],
        }
    )
    tbump_schema.validate(config)


def parse(cfg_path):
    parsed = None
    with cfg_path.open() as stream:
        parsed = toml.load(stream)

    validate(parsed)
    config = Config(
        current_version=parsed["version"]["current"],
        version_regex=re.compile(parsed["version"].get("regex"), re.VERBOSE)
    )
    config.tag_template = parsed["git"]["tag_template"]
    config.message_template = parsed["git"]["message_template"]

    config.files = list()
    for file_dict in parsed["file"]:
        file = File(
            src=file_dict["src"],
            search=file_dict.get("search"),
            version_template=file_dict.get("version_template"),
        )
        config.files.append(file)
    return config
