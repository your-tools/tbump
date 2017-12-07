import subprocess

import ui


def run_git(working_path, *cmd, raises=True):
    git_cmd = list(cmd)
    git_cmd.insert(0, "git")
    options = dict()
    if not raises:
        options["stdout"] = subprocess.PIPE
        options["stderr"] = subprocess.STDOUT

    ui.debug(ui.lightgray, working_path, "$", ui.reset, *git_cmd)
    process = subprocess.Popen(git_cmd, cwd=working_path, **options)

    if raises:
        process.wait()
    else:
        out, _ = process.communicate()
        out = out.decode("utf-8")

    returncode = process.returncode
    if raises:
        if returncode != 0:
            ui.fatal(" ".join(cmd), "failed")
    else:
        if out.endswith('\n'):
            out = out.strip('\n')
        ui.debug(ui.lightgray, "[%i]" % returncode, ui.reset, out)
        return returncode, out
