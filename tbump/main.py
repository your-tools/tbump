from typing import List, Optional
import argparse
import os
import sys

from path import Path
import ui

import tbump
import tbump.config
import tbump.git
import tbump.init
from tbump.config import Config
from tbump.executor import Executor
from tbump.file_bumper import FileBumper
from tbump.git_bumper import GitBumper
from tbump.hooks import HooksRunner


TBUMP_VERSION = "4.0.0"


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


def parse_command_line(cmd: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("new_version")
    parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("-C", "--cwd", dest="working_path")
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")
    parser.add_argument("--version", action="version", version=TBUMP_VERSION)
    parser.set_defaults(dry_run=False)
    args = parser.parse_args(args=cmd)
    return args


def parse_config(working_path: Path) -> Config:
    tbump_path = working_path / "tbump.toml"
    try:
        config = tbump.config.parse(tbump_path)
    except IOError as io_error:
        raise InvalidConfig(io_error=io_error)
    except Exception as parse_error:
        raise InvalidConfig(parse_error=parse_error)
    return config


def bump(working_path: Path, new_version: str, *,
         interactive: bool = True, dry_run: bool = False) -> None:
    config = parse_config(working_path)

    ui.info_1("Bumping from", ui.bold, config.current_version,
              ui.reset, "to", ui.bold, new_version)

    git_bumper = GitBumper(working_path)
    git_bumper.set_config(config)
    git_bumper.check_state(new_version)

    file_bumper = FileBumper(working_path)
    file_bumper.set_config(config)

    hooks_runner = HooksRunner(working_path)
    for hook in config.hooks:
        hooks_runner.add_hook(hook)

    executor = Executor(new_version, git_bumper, file_bumper, hooks_runner)

    if interactive:
        executor.print_self(dry_run=True)
        if not dry_run:
            proceed = ui.ask_yes_no("Looking good?", default=False)
            if not proceed:
                raise Cancelled()

    if dry_run:
        return

    executor.print_self(dry_run=False)
    executor.run()


def run(cmd: List[str]) -> None:
    args = parse_command_line(cmd)
    if args.working_path:
        working_path = Path(args.working_path)
    else:
        working_path = Path(os.getcwd())

    new_version = args.new_version
    if new_version == "init":
        tbump.init.init(working_path)
        return

    dry_run = args.dry_run
    interactive = args.interactive
    bump(working_path, new_version, interactive=interactive, dry_run=dry_run)


def main(args: Optional[List[str]] = None) -> None:
    # Supress backtrace if exception derives from tbump.Error
    if not args:
        args = sys.argv[1:]
    try:
        run(args)
    except tbump.Error as error:
        error.print_error()
        sys.exit(1)
