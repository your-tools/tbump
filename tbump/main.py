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


TBUMP_VERSION = "0.0.7"


@contextlib.contextmanager
def bump_git(git_bumper, new_version):
    git_bumper.check_state(new_version)
    yield
    git_bumper.bump(new_version)


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("new_version")
    parser.add_argument("-C", "--cwd", dest="working_dir")
    parser.add_argument("--non-interactive", dest="interactive", action="store_false")
    parser.add_argument("--version", action="version", version=TBUMP_VERSION)
    args = parser.parse_args(args=args)
    working_dir = args.working_dir
    new_version = args.new_version
    if working_dir:
        os.chdir(working_dir)
    try:
        config = tbump.config.parse(path.Path("tbump.toml"))
    except IOError as io_error:
        ui.fatal("Could not read config file:", io_error)
    except Exception as e:
        ui.fatal("Invalid config:",  e)
    ui.info_1(
            "Bumping from",
            ui.reset, ui.bold, config.current_version,
            ui.reset, "to",
            ui.reset, ui.bold, new_version)
    working_path = path.Path.getcwd()
    git_bumper = GitBumper(working_path)
    git_bumper.set_config(config)
    file_bumper = FileBumper(working_path)
    file_bumper.set_config(config)
    with bump_git(git_bumper, new_version):
        changes = file_bumper.compute_changes(new_version)
        file_bumper.apply_changes(changes)

    if args.interactive:
        push_ok = ui.ask_yes_no("OK to push", default=False)
        if push_ok:
            git_bumper.push(new_version)
