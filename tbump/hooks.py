import subprocess
from pathlib import Path
from typing import List, Optional

import cli_ui as ui

from tbump.action import Action
from tbump.error import Error


class Hook(Action):
    def __init__(self, name: str, cmd: str):
        super().__init__()
        self.working_path: Optional[Path] = None
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


class HookError(Error):
    def __init__(self, *, name: str, cmd: str, rc: int):
        super().__init__()
        self.cmd = cmd
        self.rc = rc
        self.name = name

    def print_error(self) -> None:
        ui.error(ui.reset, "`%s`" % self.cmd, "exited with return code", self.rc)


class HooksRunner:
    def __init__(self, working_path: Path, current_version: str, operations: List[str]):
        self.hooks: List[Hook] = []
        self.working_path = working_path
        self.current_version = current_version
        self.operations = operations

    def add_hook(self, hook: Hook) -> None:
        hook.working_path = self.working_path
        self.hooks.append(hook)

    def get_before_hooks(self, new_version: str) -> List[Hook]:
        return self._get_hooks_for_new_version_by_type(new_version, "before_commit")

    def get_after_hooks(self, new_version: str) -> List[Hook]:
        if "push_tag" in self.operations or "push_commit" in self.operations:
            return self._get_hooks_for_new_version_by_type(new_version, "after_push")
        else:
            return []

    def _get_hooks_for_new_version_by_type(
        self, new_version: str, type_: str
    ) -> List[Hook]:
        cls = HOOKS_CLASSES[type_]
        matching_hooks = [hook for hook in self.hooks if isinstance(hook, cls)]
        res = []
        for hook in matching_hooks:
            hook.cmd = hook.cmd.format(
                current_version=self.current_version, new_version=new_version
            )
            res.append(hook)
        return res
