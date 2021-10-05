import textwrap
from pathlib import Path
from typing import List, Optional

import cli_ui as ui

from tbump.error import Error
from tbump.git import run_git_captured


class TbumpTomlAlreadyExists(Error):
    def __init__(self, cfg_path: Path):
        super().__init__()
        self.cfg_path = cfg_path

    def print_error(self) -> None:
        ui.error(self.cfg_path, "already exists")


def find_files(working_path: Path, current_version: str) -> List[str]:
    ui.info_2("Looking for files matching", ui.bold, current_version)
    cmd = ["grep", "--fixed-strings", "--files-with-matches", current_version]
    _, out = run_git_captured(working_path, *cmd, check=True)
    res: List[str] = []
    ui.info("Found following matching files")
    for file in out.splitlines():
        ui.info(" * ", file)
        res.append(file)
    return res


def init(
    working_path: Path,
    *,
    current_version: str,
    use_pyproject: bool = False,
    specified_config_path: Optional[Path] = None,
) -> None:
    """Interactively creates a new tbump.toml"""
    if use_pyproject:
        text = "[tool.tbump]\n"
        key_prefix = "tool.tbump."
        cfg_path = working_path / "pyproject.toml"
    else:
        text = ""
        key_prefix = ""
        if specified_config_path:
            cfg_path = specified_config_path
        else:
            cfg_path = working_path / "tbump.toml"
        if cfg_path.exists():
            raise TbumpTomlAlreadyExists(cfg_path)
    ui.info_1("Generating tbump config file")
    text += textwrap.dedent(
        """\
        # Uncomment this if your project is hosted on GitHub:
        # github_url = "https://github.com/<user or organization>/<project>/"

        [@key_prefix@version]
        current = "@current_version@"

        # Example of a semver regexp.
        # Make sure this matches current_version before
        # using tbump
        regex = '''
          (?P<major>\\d+)
          \\.
          (?P<minor>\\d+)
          \\.
          (?P<patch>\\d+)
          '''

        [@key_prefix@git]
        message_template = "Bump to {new_version}"
        tag_template = "v{new_version}"

        # For each file to patch, add a [[@key_prefix@file]] config
        # section containing the path of the file, relative to the
        # tbump.toml location.
        [[@key_prefix@file]]
        src = "..."

        # You can specify a list of commands to
        # run after the files have been patched
        # and before the git commit is made

        #  [[@key_prefix@before_commit]]
        #  name = "check changelog"
        #  cmd = "grep -q {new_version} Changelog.rst"

        # Or run some commands after the git tag and the branch
        # have been pushed:
        #  [[@key_prefix@after_push]]
        #  name = "publish"
        #  cmd = "./publish.sh"
    """
    )

    text = text.replace("@current_version@", current_version)
    text = text.replace("@key_prefix@", key_prefix)
    with cfg_path.open("a") as f:
        f.write(text)
    ui.info_2(ui.check, "Generated", cfg_path)
