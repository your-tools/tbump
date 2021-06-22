from typing import List, Sequence

import cli_ui as ui

from tbump.action import Action
from tbump.config import ConfigFile
from tbump.file_bumper import FileBumper
from tbump.git_bumper import GitBumper
from tbump.hooks import HooksRunner


class ActionGroup:
    def __init__(
        self,
        dry_run_desc: str,
        desc: str,
        actions: Sequence[Action],
        *,
        should_enumerate: bool = False,
    ):
        self.should_enumerate = should_enumerate
        self.desc = desc
        self.dry_run_desc = dry_run_desc
        self.actions = actions

    def print_group(self, dry_run: bool = False) -> None:
        if not self.actions:
            return
        if dry_run and self.dry_run_desc:
            ui.info_2(self.dry_run_desc)
        if not dry_run and self.desc:
            ui.info_2(self.desc)
        for i, action in enumerate(self.actions):
            if self.should_enumerate:
                ui.info_count(i, len(self.actions), end="")
            action.print_self()

    def execute(self) -> None:
        for action in self.actions:
            action.do()


class UpdateConfig(Action):
    def __init__(self, config_file: ConfigFile, new_version: str):
        self.config_file = config_file
        self.new_version = new_version

    def print_self(self) -> None:
        return

    def do(self) -> None:
        # fmt: off
        ui.info_3(
            "Set current version to", ui.blue, self.new_version, ui.reset,
            "in", ui.bold, self.config_file.path.name
        )
        # fmt: on
        self.config_file.set_new_version(self.new_version)


class Executor:
    def __init__(self, new_version: str, file_bumper: FileBumper):
        self.new_version = new_version
        self.work: List[ActionGroup] = []

        config_file = file_bumper.config_file
        assert config_file
        update_config = UpdateConfig(config_file, new_version)

        update_config_group = ActionGroup(
            f"Would update current version in {config_file.path.name}",
            "Updating current version",
            [update_config],
            should_enumerate=False,
        )
        self.work.append(update_config_group)

        patches = ActionGroup(
            "Would patch these files",
            "Patching files",
            file_bumper.get_patches(new_version),
        )
        self.work.append(patches)

    def add_git_and_hook_actions(
        self, new_version: str, git_bumper: GitBumper, hooks_runner: HooksRunner
    ) -> None:
        before_hooks = ActionGroup(
            "Would run these hooks before commit",
            "Running hooks before commit",
            hooks_runner.get_before_hooks(new_version),
            should_enumerate=True,
        )
        self.work.append(before_hooks)

        git_commands = ActionGroup(
            "Would run these git commands",
            "Performing git operations",
            git_bumper.get_commands(new_version),
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
