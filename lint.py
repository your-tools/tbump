import os
import subprocess
import sys

import cli_ui as ui


class Check:
    def __init__(self, name, cmd, env=None):
        self.name = name
        self.cmd = cmd
        self.ok = False
        self.env = env

    def run(self):
        ui.info_2(self.name)
        rc = subprocess.call(["poetry", "run"] + list(self.cmd), env=self.env)
        self.ok = rc == 0


def init_checks():
    res = []

    def append_check(name, *cmd, env=None):
        res.append(Check(name, cmd, env=env))

    if sys.version_info.minor >= 6:
        append_check("black", "black", "--check", "--diff", ".")

    append_check("flake8", "flake8", ".")

    env = os.environ.copy()
    env["MYPYPATH"] = "stubs/"
    append_check("mypy", "mypy", "tbump", env=env)

    return res


def main():
    ui.info_1("Starting lintings")
    all_checks = init_checks()
    check_list = sys.argv[1:]
    checks = all_checks
    if check_list:
        checks = [c for c in checks if c.name in check_list]
    for check in checks:
        check.run()
    failed_checks = [check for check in checks if not check.ok]
    if not failed_checks:
        ui.info(ui.check, "All lints passed")
        return
    for check in failed_checks:
        ui.error(check.name, "failed")
    sys.exit(1)


if __name__ == "__main__":
    main()
