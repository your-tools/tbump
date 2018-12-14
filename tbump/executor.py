from typing import List, Sequence

import cli_ui as ui

from tbump.action import Action
from tbump.git_bumper import GitBumper
from tbump.file_bumper import FileBumper
from tbump.hooks import HooksRunner

_ = List


class ActionGroup():

    def __init__(self, dry_run_desc: str, desc: str,
                 actions: Sequence[Action],
                 *, should_enumerate: bool = False):
        self.should_enumerate = should_enumerate
        self.desc = desc
        self.dry_run_desc = dry_run_desc
        self.actions = actions

    def print_group(self, dry_run: bool = False) -> None:
        if not self.actions:
            return
        if dry_run:
            ui.info_2(self.dry_run_desc)
        else:
            ui.info_2(self.desc)
        for i, action in enumerate(self.actions):
            if self.should_enumerate:
                ui.info_count(i, len(self.actions), end="")
            action.print_self()

    def execute(self) -> None:
        for action in self.actions:
            action.do()


class Executor:
    def __init__(self,
                 new_version: str,
                 git_bumper: GitBumper,
                 file_bumper: FileBumper,
                 hooks_runner: HooksRunner):
        self.new_version = new_version
        self.work = list()  # type: List[ActionGroup]

        patches = ActionGroup(
            "Would patch these files",
            "Patching files",
            file_bumper.get_patches(new_version),
        )
        self.work.append(patches)

        before_hooks = ActionGroup(
            "Would run these hooks before commit",
            "Running hooks before commit",
            hooks_runner.get_before_hooks(new_version),
            should_enumerate=True,
        )
        self.work.append(before_hooks)

        git_commands = ActionGroup(
            "Would run these git commands",
            "Making bump commit and push matching tag",
            git_bumper.get_commands(new_version)
        )
        self.work.append(git_commands)

        after_hooks = ActionGroup(
            "Would run these hooks after push",
            "Running hooks after push",
            hooks_runner.get_after_hooks(new_version),
            should_enumerate=True,
        )
        self.work.append(after_hooks)

    def print_self(self, *, dry_run: bool = False) -> None:
        for action_group in self.work:
            action_group.print_group(dry_run=dry_run)

    def run(self) -> None:
        for action_group in self.work:
            action_group.print_group(dry_run=False)
            action_group.execute()
