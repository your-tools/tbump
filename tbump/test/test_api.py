from pathlib import Path
from typing import Any

from tbump import bump_files
from tbump.test.conftest import file_contains


def test_bump_files_defaults_to_working_dir(test_repo: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(test_repo)
    bump_files("1.2.42")

    assert file_contains(test_repo / "package.json", '"version": "1.2.42"')


def test_bump_files_with_repo_path(test_repo: Path) -> None:
    bump_files("1.2.42", test_repo)

    assert file_contains(test_repo / "package.json", '"version": "1.2.42"')
