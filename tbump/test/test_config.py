import re

import path

import tbump.config


def test_parse_config():
    this_dir = path.Path(__file__).parent
    test_cfg_path = this_dir.abspath().joinpath("tbump.toml")
    config = tbump.config.parse(test_cfg_path)

    foo_json = tbump.config.File(
        src="package.json",
        search='"version": "{current_version}"'
    )
    version_txt = tbump.config.File(src="VERSION")

    assert config.files == [
        foo_json,
        version_txt,
    ]

    assert config.current_version == "1.2.41"
