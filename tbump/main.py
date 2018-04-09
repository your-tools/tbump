import abc
import argparse
import os
import sys

import path
import ui

import tbump
import tbump.config
from tbump.file_bumper import FileBumper
from tbump.git_bumper import GitBumper


TBUMP_VERSION = "1.0.2"


class InvalidConfig(tbump.Error):
    def __init__(self, io_error=None, parse_error=None):
        self.io_error = io_error
        self.parse_error = parse_error

    def print_error(self):
        if self.io_error:
            ui.error("Could not read config file:", self.io_error)
        if self.parse_error:
            ui.error("Invalid config:",  self.parse_error)


class Cancelled(tbump.Error):
    def print_error(self):
        ui.error("Cancelled by user")


def main(args=None):
    # Supress backtrace if exception derives from tbump.Error
    try:
        run(args)
    except tbump.Error as error:
        error.print_error()
        sys.exit(1)


def parse_command_line(cmd):
    parser = argparse.ArgumentParser()
    parser.add_argument("new_version")
    parser.add_argument("-C", "--cwd", dest="working_dir")
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--version", action="version", version=TBUMP_VERSION)
    args = parser.parse_args(args=cmd)
    return args


class Runner(metaclass=abc.ABCMeta):
    def __init__(self, args):
        self.new_version = args.new_version
        self.dry_run = args.dry_run

        working_dir = args.working_dir or os.getcwd()
        self.working_path = path.Path(working_dir)
        os.chdir(self.working_path)

        self.config = self.parse_config()
        self.display_bump()

        self.git_bumper = self.setup_git_bumper()
        self.file_bumper = self.setup_file_bumper()

    def parse_config(self):
        tbump_path = self.working_path.joinpath("tbump.toml")
        try:
            config = tbump.config.parse(tbump_path)
        except IOError as io_error:
            raise InvalidConfig(io_error=io_error)
        except Exception as parse_error:
            raise InvalidConfig(parse_error=parse_error)
        return config

    def setup_git_bumper(self):
        git_bumper = GitBumper(self.working_path)
        git_bumper.set_config(self.config)
        return git_bumper

    def setup_file_bumper(self):
        file_bumper = FileBumper(self.working_path)
        file_bumper.set_config(self.config)
        return file_bumper

    def display_bump(self):
        bumping_message = [
            "Bumping from",
            ui.reset, ui.bold, self.config.current_version,
            ui.reset, "to",
            ui.reset, ui.bold, self.new_version
        ]
        if self.dry_run:
            bumping_message.extend([ui.reset, ui.brown, "(dry run)"])
        ui.info_1(*bumping_message)

    @abc.abstractmethod
    def check(self):
        pass

    def bump(self):
        changes = self.file_bumper.compute_changes(self.new_version)
        self.file_bumper.apply_changes(changes, dry_run=self.dry_run)
        self.git_bumper.bump(self.new_version, dry_run=self.dry_run)

    @abc.abstractmethod
    def push(self):
        pass


class InteractiveRunner(Runner):
    def __init__(self, args):
        super().__init__(args)
        self.tracked_branch = True

    def check(self):
        try:
            self.git_bumper.check_state(self.new_version)
        except tbump.git_bumper.NoTrackedBranch as e:
            e.print_error()
            self.tracked_branch = False
            proceed = ui.ask_yes_no("Continue anyway?", default=False)
            if not proceed:
                raise Cancelled from None

    def push(self):
        if self.dry_run:
            return
        if not self.tracked_branch:
            return
        push_ok = ui.ask_yes_no("OK to push", default=False)
        if push_ok:
            self.git_bumper.push(self.new_version)


class NonInteractiveRunner(Runner):
    def check(self):
        self.git_bumper.check_state(self.new_version)
        return True

    def push(self):
        return


def run(cmd=None):

    args = parse_command_line(cmd)
    interactive = args.interactive
    if interactive:
        runner = InteractiveRunner(args)
    else:
        runner = NonInteractiveRunner(args)

    runner.check()
    runner.bump()
    runner.push()
