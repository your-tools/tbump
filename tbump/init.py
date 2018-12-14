import textwrap
from typing import List

import cli_ui as ui
from path import Path

import tbump.git


def find_files(working_path: Path, current_version: str) -> List[str]:
    ui.info_2("Looking for files matching", ui.bold, current_version)
    cmd = ["grep", "--fixed-strings", "--files-with-matches", current_version]
    _, out = tbump.git.run_git_captured(working_path, *cmd, check=True)
    res = list()  # type: List[str]
    ui.info("Found following matching files")
    for file in out.splitlines():
        ui.info(" * ", file)
        res.append(file)
    return res


def init(working_path: Path, current_version: str) -> None:
    """ Interactively creates a new tbump.toml """
    ui.info_1("Generating tbump config file")
    tbump_path = working_path / "tbump.toml"
    if tbump_path.exists():
        ui.fatal(tbump_path, "already exists")
    template = textwrap.dedent(r"""
        [version]
        current = "@current_version@"

        # Example of a semver regexp.
        # Make sure this matches current_version before
        # using tbump
        regex = '''
          (?P<major>\d+)
          \.
          (?P<minor>\d+)
          \.
          (?P<patch>\d+)
          '''

        [git]
        message_template = "Bump to {new_version}"
        tag_template = "v{new_version}"
     """)

    file_template = textwrap.dedent("""
        [[file]]
        src = "@src@"
    """)

    hooks_template = textwrap.dedent("""
        # You can specify a list of commands to
        # run after the files have been patched
        # and before the git commit is made

        #  [[before_commit]]
        #  name = "check changelog"
        #  cmd = "grep -q {current_version} Changelog.md"

        # Or run some commands after the git tag and the branch
        # have been pushed:
        #  [[after_push]]
        #  name = "check changelog"
        #  cmd = "grep -q {current_version} Changelog.md"
    """)

    to_write = template.replace("@current_version@", current_version)
    files = find_files(working_path, current_version)
    for file in files:
        to_write += file_template.replace("@src@", file)
    to_write += hooks_template
    tbump_path.write_text(to_write)
    ui.info_2(ui.check, "Generated tbump.toml")
