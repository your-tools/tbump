import pytest

import tbump.file_bumper
from tbump.test.conftest import assert_in_file


def test_file_bumper(test_repo):
    bumper = tbump.file_bumper.FileBumper(test_repo)
    config = tbump.config.parse(test_repo.joinpath("tbump.toml"))
    assert bumper.working_path == test_repo
    bumper.set_config(config)
    changes = bumper.compute_changes(new_version="1.2.41-alpha-2")
    assert changes == [
        tbump.file_bumper.Change("tbump.toml", "1.2.41-alpha-1", "1.2.41-alpha-2"),
        tbump.file_bumper.Change(
            "package.json", "1.2.41-alpha-1", "1.2.41-alpha-2",
            search='"version": "1.2.41-alpha-1"',
        ),
        tbump.file_bumper.Change("VERSION", "1.2.41-alpha-1", "1.2.41-alpha-2"),
        tbump.file_bumper.Change("pub.js", "1.2.41", "1.2.41"),
    ]

    bumper.apply_changes(changes)

    assert_in_file(test_repo, "package.json", '"version": "1.2.41-alpha-2"')
    assert_in_file(test_repo, "package.json", '"other-dep": "1.2.41-alpha-1"')
    assert_in_file(test_repo, "pub.js", "PUBLIC_VERSION = '1.2.41'")
