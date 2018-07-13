from typing import List, Optional
import abc
import argparse
import os
import sys

import path
import ui

import tbump
import tbump.config
import tbump.git
from tbump.config import Config
from tbump.file_bumper import FileBumper, Patch
from tbump.git_bumper import GitBumper
from tbump.hooks import HooksRunner


TBUMP_VERSION = "3.0.1"


class InvalidConfig(tbump.Error):
    def __init__(self,
                 io_error: Optional[IOError] = None,
                 parse_error: Optional[Exception] = None) -> None:
        super().__init__()
        self.io_error = io_error
        self.parse_error = parse_error

    def print_error(self) -> None:
        if self.io_error:
            ui.error("Could not read config file:", self.io_error)
        if self.parse_error:
            ui.error("Invalid config:", self.parse_error)


class Cancelled(tbump.Error):
    def print_error(self) -> None:
        ui.error("Cancelled by user")


def main(args: Optional[List[str]] = None) -> None:
    # Supress backtrace if exception derives from tbump.Error
    if not args:
        args = sys.argv[1:]
    try:
        run(args)
    except tbump.Error as error:
        error.print_error()
        sys.exit(1)


def parse_command_line(cmd: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("new_version")
    parser.add_argument("-C", "--cwd", dest="working_dir")
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")
    parser.add_argument("--version", action="version", version=TBUMP_VERSION)
    args = parser.parse_args(args=cmd)
    return args


class Runner(metaclass=abc.ABCMeta):
    def __init__(self, args: argparse.Namespace) -> None:
        self.new_version = args.new_version

        working_dir = args.working_dir or os.getcwd()
        self.working_path = path.Path(working_dir)
        os.chdir(self.working_path)

        self.config = self.parse_config()

        self.git_bumper = self.setup_git_bumper()
        self.file_bumper = self.setup_file_bumper()
        self.hooks_runner = self.setup_hooks_runner()

    def display_bump(self, dry_run: bool = False) -> None:
        ui.info_1(
            "Bumping from",
            ui.reset, ui.bold, self.config.current_version,
            ui.reset, "to",
            ui.reset, ui.bold, self.new_version, end=""
        )
        if dry_run:
            ui.info(ui.brown, "(dry _run)")
        else:
            ui.info()
        ui.info()

    def parse_config(self) -> Config:
        tbump_path = self.working_path / "tbump.toml"
        try:
            config = tbump.config.parse(tbump_path)
        except IOError as io_error:
            raise InvalidConfig(io_error=io_error)
        except Exception as parse_error:
            raise InvalidConfig(parse_error=parse_error)
        return config

    def setup_git_bumper(self) -> GitBumper:
        git_bumper = GitBumper(self.working_path)
        git_bumper.set_config(self.config)
        return git_bumper

    def setup_file_bumper(self) -> FileBumper:
        file_bumper = FileBumper(self.working_path)
        file_bumper.set_config(self.config)
        return file_bumper

    def setup_hooks_runner(self) -> HooksRunner:
        hooks_runner = HooksRunner(self.working_path)
        for hook in self.config.hooks:
            hooks_runner.add_hook(hook)
        return hooks_runner

    def before_bump(self, patches: List[Patch], git_commands: List[List[str]]) -> None:
        pass

    def bump(self) -> None:
        self.display_bump()
        patches = self.file_bumper.compute_patches(self.new_version)
        git_commands = self.git_bumper.compute_commands(self.new_version)
        self.before_bump(patches, git_commands)

        ui.info_2("Patching files")
        self.file_bumper.apply_patches(patches)
        if self.hooks_runner.hooks:
            ui.info()
            ui.info_2("Running hooks")
            self.hooks_runner.run(self.new_version)
        ui.info()
        ui.info_2("Running git commands", ui.ellipsis)
        self.git_bumper.run_commands(git_commands)
        ui.info()
        ui.info(ui.green, "Done", ui.check)

    @abc.abstractmethod
    def check(self) -> None:
        pass


class InteractiveRunner(Runner):

    def check(self) -> None:
        try:
            self.git_bumper.check_state(self.new_version)
        except tbump.git_bumper.NoTrackedBranch as e:
            e.print_error()
            proceed = ui.ask_yes_no("Continue anyway?", default=False)
            if not proceed:
                raise Cancelled from None

    # pylint: disable=no-self-use
    def display_patches(self, patches: List[Patch]) -> None:
        for patch in patches:
            tbump.file_bumper.print_patch(patch)

    # pylint: disable=no-self-use
    def display_git_commands(self, git_commands: List[List[str]]) -> None:
        for git_command in git_commands:
            tbump.git.print_git_command(git_command)

    def display_hooks(self) -> None:
        hooks = self.hooks_runner.hooks
        if not hooks:
            return
        ui.info_2("Would execute these hooks")
        for i, hook in enumerate(hooks):
            ui.info_count(i, len(hooks), ui.bold, hook.name)
            tbump.hooks.print_hook(hook)

    def before_bump(self, patches: List[Patch], git_commands: List[List[str]]) -> None:
        ui.info_2("Would patch those files")
        self.display_patches(patches)
        ui.info()
        self.display_hooks()
        ui.info()
        ui.info_2("Would run these commands")
        self.display_git_commands(git_commands)
        ui.info()
        answer = ui.ask_yes_no("Looking good?", default=False)
        if not answer:
            raise Cancelled from None
        ui.info()


class NonInteractiveRunner(Runner):
    def check(self) -> None:
        self.git_bumper.check_state(self.new_version)


def run(cmd: List[str]) -> None:
    args = parse_command_line(cmd)
    interactive = args.interactive
    if interactive:
        runner = InteractiveRunner(args)  # type: Runner
    else:
        runner = NonInteractiveRunner(args)

    runner.check()
    runner.bump()
