import re

import attr
import toml


@attr.s
class Config:
    version_regexp = attr.ib()
    files = attr.ib(default=None)


@attr.s
class File:
    src = attr.ib()
    search = attr.ib(default=None)
    assert_present = attr.ib(default=False)


def parse(cfg_path):
    parsed = None
    with cfg_path.open() as stream:
        parsed = toml.load(stream)
    version_regexp = re.compile(parsed["version"]["parse"], re.VERBOSE)
    config = Config(
        version_regexp=version_regexp
    )
    config.files = list()
    for file_dict in parsed["file"]:
        file = File(
            src=file_dict["src"],
            search=file_dict.get("search"),
            assert_present=file_dict.get("assert_present", False),
        )
        config.files.append(file)
    return config
