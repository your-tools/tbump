from typing import List
import subprocess

import attr
from path import Path
import ui

import tbump

List


@attr.s
class Hook:
    name = attr.ib()  # type: str
    cmd = attr.ib()  # type: str


class HookError(tbump.Error):
    def __init__(self, *, name: str, cmd: str, rc: int) -> None:
        self.cmd = cmd
        self.rc = rc
        self.name = name

    def print_error(self) -> None:
        ui.error(
            ui.reset, "`%s`" % self.cmd,
            "exited with return code", self.rc
        )


def print_hook(hook: Hook) -> None:
    ui.info(ui.darkgray, "$", ui.reset, hook.cmd)


class HooksRunner:
    def __init__(self, working_path: Path) -> None:
        self.hooks = list()  # type: List[Hook]
        self.working_path = working_path

    def add_hook(self, hook: Hook) -> None:
        self.hooks.append(hook)

    def run(self, new_version: str) -> None:
        for i, hook in enumerate(self.hooks):
            hook.cmd = hook.cmd.format(new_version=new_version)
            ui.info_count(i, len(self.hooks), ui.bold, hook.name)
            print_hook(hook)
            rc = subprocess.call(hook.cmd, shell=True, cwd=self.working_path)
            if rc != 0:
                raise HookError(name=hook.name, cmd=hook.cmd, rc=rc)
