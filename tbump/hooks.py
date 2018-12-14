from typing import List, Optional  # noqa
import subprocess

from path import Path
import cli_ui as ui

import tbump
import tbump.action


class Hook(tbump.action.Action):
    def __init__(self, name: str, cmd: str):
        super().__init__()
        self.working_path = None  # type: Optional[Path]
        self.name = name
        self.cmd = cmd

    def print_self(self) -> None:
        ui.info(ui.darkgray, "$", ui.reset, self.cmd)

    def do(self) -> None:
        self.run()

    def run(self) -> None:
        rc = subprocess.call(self.cmd, shell=True, cwd=self.working_path)
        if rc != 0:
            raise HookError(name=self.name, cmd=self.cmd, rc=rc)


class BeforeCommitHook(Hook):
    pass


class AfterPushHook(Hook):
    pass


HOOKS_CLASSES = {
    "after_push": AfterPushHook,
    "before_commit": BeforeCommitHook,
    "before_push": BeforeCommitHook,  # retro-compat name
    "hook": BeforeCommitHook,  # retro-compat name
}


class HookError(tbump.Error):
    def __init__(self, *, name: str, cmd: str, rc: int):
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
    def __init__(self, working_path: Path):
        self.hooks = list()  # type: List[Hook]
        self.working_path = working_path

    def add_hook(self, hook: Hook) -> None:
        hook.working_path = self.working_path
        self.hooks.append(hook)

    def get_before_hooks(self, new_version: str) -> List[Hook]:
        return self._get_hooks_for_new_version_by_type(new_version, "before_commit")

    def get_after_hooks(self, new_version: str) -> List[Hook]:
        return self._get_hooks_for_new_version_by_type(new_version, "after_push")

    def _get_hooks_for_new_version_by_type(self, new_version: str, type_: str) -> List[Hook]:
        cls = HOOKS_CLASSES[type_]
        matching_hooks = [hook for hook in self.hooks if isinstance(hook, cls)]
        res = list()
        for hook in matching_hooks:
            hook.cmd = hook.cmd.format(new_version=new_version)
            res.append(hook)
        return res
