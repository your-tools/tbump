import re

import attr
import toml


@attr.s
class Config:
    current_version = attr.ib()
    files = attr.ib(default=None)


@attr.s
class File:
    src = attr.ib()
    search = attr.ib(default=None)


def parse(cfg_path):
    parsed = None
    with cfg_path.open() as stream:
        parsed = toml.load(stream)
    config = Config(
        current_version=parsed["version"]["current"]
    )
    config.files = list()
    for file_dict in parsed["file"]:
        file = File(
            src=file_dict["src"],
            search=file_dict.get("search"),
        )
        config.files.append(file)
    return config
