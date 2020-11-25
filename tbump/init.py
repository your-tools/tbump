import textwrap
from pathlib import Path
from typing import List

import cli_ui as ui

import tbump.git


def find_files(working_path: Path, current_version: str) -> List[str]:
    ui.info_2("Looking for files matching", ui.bold, current_version)
    cmd = ["grep", "--fixed-strings", "--files-with-matches", current_version]
    _, out = tbump.git.run_git_captured(working_path, *cmd, check=True)
    res: List[str] = []
    ui.info("Found following matching files")
    for file in out.splitlines():
        ui.info(" * ", file)
        res.append(file)
    return res


def init(
    working_path: Path, *, current_version: str, use_pyproject: bool = False
) -> None:
    """ Interactively creates a new tbump.toml """
    ui.info_1("Generating tbump config file")
    if use_pyproject:
        key_prefix = "tool.tbump."
        cfg_path = working_path / "pyproject.toml"
    else:
        key_prefix = ""
        cfg_path = working_path / "tbump.toml"
        if cfg_path.exists():
            ui.fatal(cfg_path, "already exists")
    text = textwrap.dedent(
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
