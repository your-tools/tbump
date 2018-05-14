import subprocess

import attr
import ui

import tbump


@attr.s
class Hook:
    name = attr.ib()
    cmd = attr.ib()


class HookError(tbump.Error):
    def print_error(self):
        ui.error(
            ui.reset, "`%s`" % self.cmd,
            "exited with return code", self.rc
        )


def print_hook(hook):
    ui.info(ui.darkgray, "$", ui.reset, hook.cmd)


class HooksRunner:
    def __init__(self, working_path=None):
        self.hooks = list()
        self.working_path = working_path

    def add_hook(self, hook):
        self.hooks.append(hook)

    def run(self, new_version):
        for i, hook in enumerate(self.hooks):
            hook.cmd = hook.cmd.format(new_version=new_version)
            ui.info_count(i, len(self.hooks), ui.bold, hook.name)
            print_hook(hook)
            rc = subprocess.call(hook.cmd, shell=True, cwd=self.working_path)
            if rc != 0:
                raise HookError(name=hook.name, cmd=hook.cmd, rc=rc)
