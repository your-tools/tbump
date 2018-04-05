import subprocess

import ui

import tbump


class GitError(tbump.Error):
    pass


class GitCommandError(GitError):
    pass


def run_git(working_path, *cmd, verbose=False):
    """ Run git `cmd` in given `working_path`

    Displays the command ran if `verbose` is True

    Raise GitCommandError if return code is non-zero.
    """
    git_cmd = list(cmd)
    git_cmd.insert(0, "git")

    if verbose:
        ui.info_3(*git_cmd)
    else:
        ui.debug(ui.lightgray, working_path, "$", ui.reset, *git_cmd)
    returncode = subprocess.call(git_cmd, cwd=working_path)
    if returncode != 0:
        raise GitCommandError(cmd=cmd, working_path=working_path)


def run_git_captured(working_path, *cmd, check=True):
    """ Run git `cmd` in given `working_path`, capturing the output

    Return a tuple (returncode, output).

    Raise GitCommandError if return code is non-zero and check is True
    """
    git_cmd = list(cmd)
    git_cmd.insert(0, "git")
    options = dict()
    options["stdout"] = subprocess.PIPE
    options["stderr"] = subprocess.STDOUT

    ui.debug(ui.lightgray, working_path, "$", ui.reset, *git_cmd)
    process = subprocess.Popen(git_cmd, cwd=working_path, **options)
    output, _ = process.communicate()
    output = output.decode("utf-8")
    if output.endswith('\n'):
        output = output.strip('\n')
    returncode = process.returncode
    ui.debug(ui.lightgray, "[%i]" % returncode, ui.reset, output)
    if check and returncode != 0:
        raise GitCommandError(working_path=working_path, cmd=cmd, output=output)
    return returncode, output
