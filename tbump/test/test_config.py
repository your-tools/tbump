import re

import path

import tbump.config


def test_parse_config():
    this_dir = path.Path(__file__).parent
    test_cfg_path = this_dir.abspath().joinpath("tbump.toml")
    config = tbump.config.parse(test_cfg_path)
    assert config.version_regexp == re.compile("""\
  (?P<major>\d+)
  \.
  (?P<minor>\d+)
  \.
  (?P<patch>\d+)
  (
    -
    (?P<channel>alpha|beta)
    -
    (?P<release>\d+)
  )?""", re.VERBOSE)

    foo_json = tbump.config.File(
        src="package.json",
        search='"version": "{current_version}"'
    )
    version_txt = tbump.config.File(src="VERSION")
    changelog_md = tbump.config.File(src="Changelog.md", assert_present=True)

    assert config.files == [
        foo_json,
        version_txt,
        changelog_md,
    ]
