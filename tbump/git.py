import subprocess

import ui


def run_git(working_path, *cmd, raises=True, verbose=False):
    git_cmd = list(cmd)
    git_cmd.insert(0, "git")
    options = dict()
    if not raises:
        options["stdout"] = subprocess.PIPE
        options["stderr"] = subprocess.STDOUT

    if verbose:
        ui.info_3(*git_cmd)
    process = subprocess.Popen(git_cmd, cwd=working_path, **options)

    if raises:
        process.wait()
    else:
        out, _ = process.communicate()
        out = out.decode("utf-8")

    returncode = process.returncode
    if raises:
        if returncode != 0:
            ui.fatal(" ".join(git_cmd), "failed")
    else:
        if out.endswith('\n'):
            out = out.strip('\n')
        ui.debug(ui.lightgray, "[%i]" % returncode, ui.reset, out)
        return returncode, out
