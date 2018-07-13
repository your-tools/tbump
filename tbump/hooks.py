from typing import List  # noqa
import subprocess

import attr
from path import Path
import ui

import tbump


@attr.s
class Hook:
    name = attr.ib()  # type: str
    cmd = attr.ib()  # type: str
    after_push = attr.ib(default=False)  # type: bool


class HookError(tbump.Error):
    def __init__(self, *, name: str, cmd: str, rc: int) -> None:
        super().__init__()
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

    def run_hooks_before_push(self, new_version: str) -> None:
        self._run(new_version, after_push=False)

    def run_hooks_after_push(self, new_version: str) -> None:
        self._run(new_version, after_push=True)

    def _run(self, new_version: str, *, after_push: bool = False) -> None:
        matching_hooks = [hook for hook in self.hooks if hook.after_push == after_push]
        if not matching_hooks:
            return
        if after_push:
            desc = "after push"
        else:
            desc = "before push"
        ui.info_2("Running hooks", desc)
        for i, hook in enumerate(matching_hooks):
            hook.cmd = hook.cmd.format(new_version=new_version)
            ui.info_count(i, len(matching_hooks), ui.bold, hook.name)
            print_hook(hook)
            rc = subprocess.call(hook.cmd, shell=True, cwd=self.working_path)
            if rc != 0:
                raise HookError(name=hook.name, cmd=hook.cmd, rc=rc)
        ui.info()
