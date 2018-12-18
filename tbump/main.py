from typing import List, Optional
import sys
import textwrap

import attr
import docopt
from path import Path
import cli_ui as ui

import tbump
import tbump.config
import tbump.git
import tbump.init
from tbump.config import Config
from tbump.executor import Executor
from tbump.file_bumper import FileBumper
from tbump.git_bumper import GitBumper
from tbump.hooks import HooksRunner


TBUMP_VERSION = "5.0.3"

USAGE = textwrap.dedent("""
Usage:
  tbump [options] <new_version>
  tbump [options] init <current_version>
  tbump --help
  tbump --version

Options:
   -h --help          Show this screen.
   -v --version       Show version.
   -C --cwd=<path>    Set working directory to <path>.
   --non-interactive  Never prompt for confirmation. Useful for automated scripts.
   --dry-run          Only display the changes that would be made.
""")


class InvalidConfig(tbump.Error):
    def __init__(self,
                 io_error: Optional[IOError] = None,
                 parse_error: Optional[Exception] = None):
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


# pylint: disable=too-few-public-methods
@attr.s
class BumpOptions:
    working_path = attr.ib()  # type: Path
    new_version = attr.ib()  # type: str
    interactive = attr.ib(default=True)  # type: bool
    dry_run = attr.ib(default=False)  # type: bool


def run(cmd: List[str]) -> None:
    opt_dict = docopt.docopt(USAGE, argv=cmd)
    if opt_dict["--version"]:
        print("tbump", TBUMP_VERSION)
        return

    # when running `tbump init` (with current_version missing),
    # docopt thinks we are runnig `tbump` with new_version = "init"
    # bail out early in this case
    if opt_dict["<new_version>"] == "init":
        sys.exit(USAGE)

    if opt_dict["--cwd"]:
        working_path = Path(opt_dict["--cwd"])
    else:
        working_path = Path.getcwd()

    if opt_dict["init"]:
        current_version = opt_dict["<current_version>"]
        tbump.init.init(working_path, current_version)
        return

    new_version = opt_dict["<new_version>"]
    bump_options = BumpOptions(working_path=working_path, new_version=new_version)
    if opt_dict["--dry-run"]:
        bump_options.dry_run = True
    if opt_dict["--non-interactive"]:
        bump_options.interactive = False
    bump(bump_options)


def parse_config(working_path: Path) -> Config:
    tbump_path = working_path / "tbump.toml"
    try:
        config = tbump.config.parse(tbump_path)
    except IOError as io_error:
        raise InvalidConfig(io_error=io_error)
    except Exception as parse_error:
        raise InvalidConfig(parse_error=parse_error)
    return config


def bump(options: BumpOptions) -> None:
    working_path = options.working_path
    new_version = options.new_version
    interactive = options.interactive
    dry_run = options.dry_run

    config = parse_config(options.working_path)

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


def main(args: Optional[List[str]] = None) -> None:
    # Supress backtrace if exception derives from tbump.Error
    if not args:
        args = sys.argv[1:]
    try:
        run(args)
    except tbump.Error as error:
        error.print_error()
        sys.exit(1)
