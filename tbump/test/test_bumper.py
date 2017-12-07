import re

import tbump.bumper

import pytest

COMPLEX_RE = re.compile("""
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
    )?
    """, re.VERBOSE)


COMPLEX_SERIALIZATIONS = [
    "{major}.{minor}.{patch}",
    "{major}.{minor}.{patch}-{channel}-{release}",
]

SEMVER_RE = re.compile("(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)")
SEMVER_SERIALIZATIONS = ["{major}.{minor}.{patch}"]


def test_complex_bump_patch_to_alpha():
    bumper = tbump.bumper.Bumper(parse=COMPLEX_RE, serialize=COMPLEX_SERIALIZATIONS)
    new_version = bumper.bump("1.2.41", "minor")
    assert new_version == "1.2.42-alpha-0"


def test_semver_bump_patch():
    bumper = tbump.bumper.Bumper(parse=SEMVER_RE, serialize=SEMVER_SERIALIZATIONS)
    new_version = bumper.bump("1.2.41", "patch")
    assert new_version == "1.2.42"


def test_semver_bump_minor():
    bumper = tbump.bumper.Bumper(parse=SEMVER_RE, serialize=SEMVER_SERIALIZATIONS)
    new_version = bumper.bump("1.2.41", "minor")
    assert new_version == "1.3.0"


def assert_parse(regex, version, expected):
    actual = tbump.bumper.parse_version(regex, version)
    actual_tuples = [(x.name, x.value) for x in actual]
    assert actual_tuples == expected


def test_parse_semver():
    assert_parse(SEMVER_RE, "1.2.3", [("major", "1"), ("minor", "2"), ("patch", "3")])


def test_parse_complex_alpha():
    assert_parse(COMPLEX_RE, "1.2.3-alpha-4",
                 [("major", "1"), ("minor", "2"), ("patch", "3"),
                  ("channel", "alpha"), ("release", "4")])


def test_parse_complex_prod():
    assert_parse(COMPLEX_RE, "1.2.3", [("major", "1"), ("minor", "2"), ("patch", "3")])
