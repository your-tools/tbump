from typing import List

import cli_ui as ui
from path import Path

import tbump.git


def find_files(working_path: Path, current_version: str) -> List[str]:
    ui.info_2("Looking for files matching", ui.bold, current_version)
    cmd = ["grep", "--fixed-strings", "--files-with-matches", current_version]
    _, out = tbump.git.run_git_captured(working_path, *cmd, check=True)
    res = []  # type: List[str]
    ui.info("Found following matching files")
    for file in out.splitlines():
        ui.info(" * ", file)
        res.append(file)
    return res


TBUMP_TOML_SPECIFIC_TEMPLATE = """\
# Uncomment this if your project is hosted on GitHub:
# github_url = https://github.com/<user or organization>/<project>/

"""

PYPROJECT_TOML_SPECIFIC_TEMPLATE = """\
[tool.tbump]
# Uncomment this if your project is hosted on GitHub:
# github_url = https://github.com/<user or organization>/<project>/

"""

BASE_TEMPLATE = """\
[@key_prefix@version]
current = "@current_version@"

# Example of a semver regexp.
# Make sure this matches current_version before using tbump
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

# For each file to patch, add a [[file]] config section containing
# the path of the file, relative to the tbump.toml location.
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
""".strip()


def generate_config_file_contents(current_version: str, use_pyproject: bool) -> str:
    if use_pyproject:
        key_prefix = "tool.tbump."
        format_specific_template = PYPROJECT_TOML_SPECIFIC_TEMPLATE
    else:
        key_prefix = ""
        format_specific_template = TBUMP_TOML_SPECIFIC_TEMPLATE
    template = format_specific_template + BASE_TEMPLATE
    contents = template.replace("@current_version@", current_version)
    contents = contents.replace("@key_prefix@", key_prefix)
    return contents


def init(
    working_path: Path, *, current_version: str, use_pyproject: bool = False
) -> None:
    """
    Interactively creates a new tbump configuration file

    By default it creates a `tbump.toml` file, but if `use_pyproject is True` then
    a `pyproject.toml` is created/updated instead.
    """
    ui.info_1("Generating tbump config file")
    config_filename = "pyproject.toml" if use_pyproject else "tbump.toml"
    tbump_path = working_path / config_filename
    if tbump_path.exists():
        # TODO: when `use_pyproject` is True, we need to check if tbump configuration
        # is present. If it isn't then we should append the configuration instead of
        # failing
        ui.fatal(tbump_path, "already exists")

    contents = generate_config_file_contents(current_version, use_pyproject)
    tbump_path.write_text(contents)

    msg = "Generated {config_filename}".format(config_filename=config_filename)
    ui.info_2(ui.check, msg)
