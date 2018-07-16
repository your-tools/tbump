from typing import List, Optional  # noqa
import subprocess

from path import Path
import ui

import tbump
import tbump.action


class Hook(tbump.action.Action):
    def __init__(self, name: str, cmd: str, *,
                 after_push: bool = False) -> None:
        super().__init__()
        self.working_path = None  # type: Optional[Path]
        self.name = name
        self.cmd = cmd
        self.after_push = after_push

    def print_self(self) -> None:
        ui.info(ui.darkgray, "$", ui.reset, self.cmd)

    def do(self) -> None:
        self.run()

    def run(self) -> None:
        rc = subprocess.call(self.cmd, shell=True, cwd=self.working_path)
        if rc != 0:
            raise HookError(name=self.name, cmd=self.cmd, rc=rc)


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


class HooksRunner:
    def __init__(self, working_path: Path) -> None:
        self.hooks = list()  # type: List[Hook]
        self.working_path = working_path

    def add_hook(self, hook: Hook) -> None:
        hook.working_path = self.working_path
        self.hooks.append(hook)

    def get_before_hooks(self, new_version: str) -> List[Hook]:
        return self._get_hooks(new_version, after_push=False)

    def get_after_hooks(self, new_version: str) -> List[Hook]:
        return self._get_hooks(new_version, after_push=True)

    def _get_hooks(self, new_version: str, *, after_push: bool = False) -> List[Hook]:
        matching_hooks = [hook for hook in self.hooks if hook.after_push == after_push]
        res = list()
        for hook in matching_hooks:
            hook.cmd = hook.cmd.format(new_version=new_version)
            res.append(hook)
        return res
