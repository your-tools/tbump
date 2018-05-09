import attr
import ui

import subprocess


@attr.s
class Hook:
    name = attr.ib()
    cmd = attr.ib()


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
            ui.info_count(i, len(self.hooks), hook.name)
            print_hook(hook)
            subprocess.run(hook.cmd, shell=True, cwd=self.working_path)
