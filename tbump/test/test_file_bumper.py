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


def test_looking_for_empty_groups(tmp_path):
    tbump_path = tmp_path.joinpath("tbump.toml")
    tbump_path.write_text(
        """
        [version]
        current = "1.2"
        regex = '''
            (?P<major>\d+)
            \.
            (?P<minor>\d+)
            (
              \.
              (?P<patch>\d+)
            )?
        '''

        [git]
        message_template = "Bump to {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "foo"
        version_template = "{major}.{minor}.{patch}"

        """
    )
    foo_path = tmp_path.joinpath("foo")
    foo_path.write_text(
        """
        version = "1.2"
        """
    )
    config = tbump.config.parse(tbump_path)
    bumper = tbump.file_bumper.FileBumper(tmp_path)
    bumper.set_config(config)
    with pytest.raises(tbump.file_bumper.BadSubstitution) as e:
        bumper.compute_changes(new_version="1.3.1")
    assert e.value.src == "foo"
    assert e.value.groups == {"major": "1", "minor": "2", "patch": None}


def test_replacing_with_empty_groups(tmp_path):
    tbump_path = tmp_path.joinpath("tbump.toml")
    tbump_path.write_text(
        """
        [version]
        current = "1.2.3"
        regex = '''
            (?P<major>\d+)
            \.
            (?P<minor>\d+)
            (
              \.
              (?P<patch>\d+)
            )?
        '''

        [git]
        message_template = "Bump to {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "foo"
        version_template = "{major}.{minor}.{patch}"

        """
    )
    foo_path = tmp_path.joinpath("foo")
    foo_path.write_text(
        """
        version = "1.2.3"
        """
    )

    bumper = tbump.file_bumper.FileBumper(tmp_path)
    config = tbump.config.parse(tbump_path)
    bumper.set_config(config)
    with pytest.raises(tbump.file_bumper.BadSubstitution) as e:
        bumper.compute_changes(new_version="1.3")
    assert e.value.groups == {"major": "1", "minor": "3", "patch": None}


def test_changing_same_file_twice(tmp_path):
    tbump_path = tmp_path.joinpath("tbump.toml")
    tbump_path.write_text(
        """
        [version]
        current = "1.2.3"
        regex = '''
            (?P<major>\d+)
            \.
            (?P<minor>\d+)
            (
              \.
              (?P<patch>\d+)
            )?
        '''

        [git]
        message_template = "Bump to {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "foo.c"
        version_template = "{major}.{minor}"
        search = "PUBLIC_VERSION"

        [[file]]
        src = "foo.c"
        search = "FULL_VERSION"

        """
    )

    foo_c = tmp_path.joinpath("foo.c")
    foo_c.write_text(
        """
        #define FULL_VERSION "1.2.3"
        #define PUBLIC_VERSION "1.2"
        """
    )
    bumper = tbump.file_bumper.FileBumper(tmp_path)
    config = tbump.config.parse(tbump_path)
    bumper.set_config(config)
    changes = bumper.compute_changes(new_version="1.3.0")
    bumper.apply_changes(changes)

    assert_in_file(foo_c, '#define FULL_VERSION "1.3.0"')
    assert_in_file(foo_c, '#define PUBLIC_VERSION "1.3"')
