import argparse
import contextlib
import os
import sys

import path
import schema
import ui

import tbump.config
from tbump.file_bumper import FileBumper
from tbump.git_bumper import GitBumper


TBUMP_VERSION = "1.0.0"


@contextlib.contextmanager
def bump_git(git_bumper, new_version, dry_run=False):
    git_bumper.check_state(new_version)
    yield
    git_bumper.bump(new_version, dry_run=dry_run)


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("new_version")
    parser.add_argument("-C", "--cwd", dest="working_dir")
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--version", action="version", version=TBUMP_VERSION)
    args = parser.parse_args(args=args)
    interactive = args.interactive
    working_dir = args.working_dir
    new_version = args.new_version
    dry_run = args.dry_run
    if working_dir:
        os.chdir(working_dir)
    try:
        config = tbump.config.parse(path.Path("tbump.toml"))
    except IOError as io_error:
        ui.fatal("Could not read config file:", io_error)
    except Exception as e:
        ui.fatal("Invalid config:",  e)
    bumping_message = [
        "Bumping from",
        ui.reset, ui.bold, config.current_version,
        ui.reset, "to",
        ui.reset, ui.bold, new_version
    ]
    if dry_run:
        bumping_message.extend([ui.reset, ui.brown, "(dry run)"])
    ui.info_1(*bumping_message)
    working_path = path.Path.getcwd()
    git_bumper = GitBumper(working_path)
    git_bumper.set_config(config)
    file_bumper = FileBumper(working_path)
    file_bumper.set_config(config)
    with bump_git(git_bumper, new_version, dry_run=dry_run):
        changes = file_bumper.compute_changes(new_version)
        file_bumper.apply_changes(changes, dry_run=dry_run)

    if interactive and not dry_run:
        push_ok = ui.ask_yes_no("OK to push", default=False)
        if push_ok:
            git_bumper.push(new_version)
