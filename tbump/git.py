import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import cli_ui as ui

from tbump.error import Error


class GitError(Error):
    pass


class GitCommandError(GitError):
    def __init__(
        self, cmd: List[str], working_path: Path, output: Optional[str] = None
    ):
        super().__init__()
        self.cmd = cmd
        self.output = output
        self.working_path = working_path

    def print_error(self) -> None:
        cmd_str = " ".join(self.cmd)
        ui.error("Command", "`%s`" % cmd_str, "failed")


def print_git_command(cmd: List[str]) -> None:
    ui.info(ui.darkgray, "$", ui.reset, "git", *cmd)


def run_git(working_path: Path, *cmd: str, verbose: bool = False) -> None:
    """Run git `cmd` in given `working_path`

    Displays the command ran if `verbose` is True

    Raise GitCommandError if return code is non-zero.
    """
    cmd_list = list(cmd)
    if verbose:
        print_git_command(cmd_list)
    git_cmd = list(cmd)
    git_cmd.insert(0, "git")

    returncode = subprocess.call(git_cmd, cwd=working_path)
    if returncode != 0:
        raise GitCommandError(cmd=git_cmd, working_path=working_path)


def run_git_captured(
    working_path: Path, *cmd: str, check: bool = True
) -> Tuple[int, str]:
    """Run git `cmd` in given `working_path`, capturing the output

    Return a tuple (returncode, output).

    Raise GitCommandError if return code is non-zero and check is True
    """
    git_cmd = list(cmd)
    git_cmd.insert(0, "git")
    options = {}
    options["stdout"] = subprocess.PIPE
    options["stderr"] = subprocess.STDOUT

    ui.debug(ui.lightgray, working_path, "$", ui.reset, *git_cmd)
    process = subprocess.Popen(git_cmd, cwd=working_path, **options)  # type: ignore
    output, _ = process.communicate()
    output = output.decode("utf-8")
    if output.endswith("\n"):
        output = output.strip("\n")
    returncode = process.returncode
    ui.debug(ui.lightgray, "[%i]" % returncode, ui.reset, output)
    if check and returncode != 0:
        raise GitCommandError(working_path=working_path, cmd=git_cmd, output=output)
    return returncode, output
