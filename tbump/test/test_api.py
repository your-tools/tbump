from path import Path

import tbump
from tbump.test.conftest import file_contains


def test_bump_files_defaults_to_working_dir(test_repo: Path) -> None:
    with test_repo:
        tbump.bump_files("1.2.42")

    assert file_contains(test_repo / "package.json", '"version": "1.2.42"')


def test_bump_files_with_repo_path(test_repo: Path) -> None:
    tbump.bump_files("1.2.42", test_repo)

    assert file_contains(test_repo / "package.json", '"version": "1.2.42"')
