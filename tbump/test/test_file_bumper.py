from pathlib import Path

import pytest

from tbump.config import get_config_file
from tbump.file_bumper import BadSubstitution, CurrentVersionNotFound, FileBumper, Patch
from tbump.test.conftest import file_contains


def test_file_bumper_simple(test_repo: Path) -> None:
    bumper = FileBumper(test_repo)
    config_file = get_config_file(test_repo)
    assert bumper.working_path == test_repo
    bumper.set_config_file(config_file)
    patches = bumper.get_patches(new_version="1.2.41-alpha-2")
    for patch in patches:
        patch.apply()

    assert file_contains(test_repo / "package.json", '"version": "1.2.41-alpha-2"')
    assert file_contains(test_repo / "package.json", '"other-dep": "1.2.41-alpha-1"')
    assert file_contains(test_repo / "pub.js", "PUBLIC_VERSION = '1.2.41'")
    assert file_contains(test_repo / "glob-one.c", 'version_one = "1.2.41-alpha-2"')
    assert file_contains(test_repo / "glob-two.v", 'version_two = "1.2.41-alpha-2"')


def test_patcher_preserve_endings(tmp_path: Path) -> None:
    foo_txt = tmp_path / "foo.txt"
    old_contents = b"line 1\r\nv=42\r\nline3\r\n"
    foo_txt.write_bytes(old_contents)
    patch = Patch(tmp_path, "foo.txt", 1, "v=42", "v=43")
    patch.apply()
    actual_contents = foo_txt.read_bytes()
    expected_contents = old_contents.replace(b"42", b"43")
    assert actual_contents == expected_contents


def test_file_bumper_preserve_endings(test_repo: Path) -> None:
    bumper = FileBumper(test_repo)
    config_file = get_config_file(test_repo)
    package_json = test_repo / "package.json"

    # Make sure package.json contain CRLF line endings
    lines = package_json.read_text().splitlines(keepends=False)
    package_json.write_bytes(b"\r\n".join([x.encode() for x in lines]))

    bumper.set_config_file(config_file)
    patches = bumper.get_patches(new_version="1.2.41-alpha-2")
    for patch in patches:
        patch.apply()

    actual = package_json.read_bytes()
    assert b'version": "1.2.41-alpha-2",\r\n' in actual


def test_looking_for_empty_groups(tmp_path: Path) -> None:
    tbump_path = tmp_path / "tbump.toml"
    tbump_path.write_text(
        r"""
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
    foo_path = tmp_path / "foo"
    foo_path.write_text(
        """
        version = "1.2"
        """
    )
    config_file = get_config_file(tmp_path)
    bumper = FileBumper(tmp_path)
    bumper.set_config_file(config_file)
    with pytest.raises(BadSubstitution) as e:
        bumper.get_patches(new_version="1.3.1")
    assert e.value.src == "foo"
    assert e.value.groups == {"major": "1", "minor": "2", "patch": None}


def test_current_version_not_found(tmp_path: Path) -> None:
    tbump_path = tmp_path / "tbump.toml"
    tbump_path.write_text(
        r"""
        [version]
        current = "1.2.3"
        regex = ".*"

        [git]
        message_template = "Bump to {new_version}"
        tag_template = "v{new_version}"

        [[file]]
        src = "version.txt"
        """
    )
    version_txt_path = tmp_path / "version.txt"
    version_txt_path.write_text("nope")
    config_file = get_config_file(tmp_path)

    bumper = FileBumper(tmp_path)
    bumper.set_config_file(config_file)
    with pytest.raises(CurrentVersionNotFound) as e:
        bumper.get_patches(new_version="1.3.1")
    assert e.value.src == "version.txt"


def test_replacing_with_empty_groups(tmp_path: Path) -> None:
    tbump_path = tmp_path / "tbump.toml"
    tbump_path.write_text(
        r"""
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
    foo_path = tmp_path / "foo"
    foo_path.write_text(
        """
        version = "1.2.3"
        """
    )

    bumper = FileBumper(tmp_path)
    config_file = get_config_file(tmp_path)
    bumper.set_config_file(config_file)
    with pytest.raises(BadSubstitution) as e:
        bumper.get_patches(new_version="1.3")
    assert e.value.groups == {"major": "1", "minor": "3", "patch": None}


def test_changing_same_file_twice(tmp_path: Path) -> None:
    tbump_path = tmp_path / "tbump.toml"
    tbump_path.write_text(
        r"""
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

    foo_c = tmp_path / "foo.c"
    foo_c.write_text(
        """
        #define FULL_VERSION "1.2.3"
        #define PUBLIC_VERSION "1.2"
        """
    )
    bumper = FileBumper(tmp_path)
    config_file = get_config_file(tmp_path)
    bumper.set_config_file(config_file)
    patches = bumper.get_patches(new_version="1.3.0")
    for patch in patches:
        patch.do()

    assert file_contains(tmp_path / foo_c, '#define FULL_VERSION "1.3.0"')
    assert file_contains(tmp_path / foo_c, '#define PUBLIC_VERSION "1.3"')
