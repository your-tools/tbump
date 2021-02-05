import sys
import textwrap
import urllib.parse
from pathlib import Path
from typing import List, Optional

import attr
import cli_ui as ui
import docopt

import tbump
import tbump.config
import tbump.git
import tbump.init
from tbump.executor import Executor
from tbump.file_bumper import FileBumper
from tbump.git_bumper import GitBumper
from tbump.hooks import HooksRunner

TBUMP_VERSION = "6.3.0"

USAGE = textwrap.dedent(
    """
Usage:
  tbump [options] <new_version>
  tbump [options] init [--pyproject] <current_version>
  tbump --help
  tbump --version

Options:
   -h --help          Show this screen.
   -v --version       Show version.
   -C --cwd=<path>    Set working directory to <path>.
   --non-interactive  Never prompt for confirmation. Useful for automated scripts.
   --dry-run          Only display the changes that would be made.
   --only-patch       Only patches files, skipping any git operations or hook commands.
   --no-tag           Do not create a tag
   --no-push          DO not push after creating the commit and/or tag
"""
)


class Cancelled(tbump.Error):
    def print_error(self) -> None:
        ui.error("Cancelled by user")


@attr.s
class BumpOptions:
    working_path: Path = attr.ib()
    new_version: str = attr.ib()
    interactive: bool = attr.ib(default=True)
    dry_run: bool = attr.ib(default=False)
    only_patch: bool = attr.ib(default=False)


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
        working_path = Path.cwd()

    if opt_dict["init"]:
        current_version = opt_dict["<current_version>"]
        use_pyproject = opt_dict["--pyproject"]
        tbump.init.init(
            working_path, current_version=current_version, use_pyproject=use_pyproject
        )
        return

    new_version = opt_dict["<new_version>"]
    bump_options = BumpOptions(working_path=working_path, new_version=new_version)
    if opt_dict["--dry-run"]:
        bump_options.dry_run = True
    if opt_dict["--non-interactive"]:
        bump_options.interactive = False

    operations = ["patch", "hooks", "commit", "tag", "push"]
    if opt_dict["--only-patch"]:
        operations = ["patch"]
    if opt_dict["--no-push"]:
        operations.remove("push")
    if opt_dict["--no-tag"]:
        operations.remove("tag")
    bump(bump_options, operations)


def bump(options: BumpOptions, operations: List[str]) -> None:
    working_path = options.working_path
    new_version = options.new_version
    interactive = options.interactive
    dry_run = options.dry_run

    config_file = tbump.config.get_config_file(options.working_path)
    config = config_file.get_config()

    # fmt: off
    ui.info_1(
        "Bumping from", ui.bold, config.current_version,
        ui.reset, "to", ui.bold, new_version,
    )
    # fmt: on

    git_bumper = GitBumper(working_path, operations)
    git_bumper.set_config(config)
    git_state_error = None
    try:
        git_bumper.check_dirty()
        git_bumper.check_branch_state(new_version)
    except tbump.git.GitError as e:
        if dry_run:
            git_state_error = e
        else:
            raise

    file_bumper = FileBumper(working_path)
    file_bumper.set_config_file(config_file)

    executor = Executor(new_version, file_bumper)

    hooks_runner = HooksRunner(working_path, config.current_version, operations)
    if "hooks" in operations:
        for hook in config.hooks:
            hooks_runner.add_hook(hook)

    executor.add_git_and_hook_actions(new_version, git_bumper, hooks_runner)

    if interactive:
        executor.print_self(dry_run=True)
        if not dry_run:
            proceed = ui.ask_yes_no("Looking good?", default=False)
            if not proceed:
                raise Cancelled()

    if dry_run:
        if git_state_error:
            ui.error("Git repository state is invalid")
            git_state_error.print_error()
            sys.exit(1)
        else:
            return

    executor.run()

    if config.github_url and "push" in operations:
        tag_name = git_bumper.get_tag_name(new_version)
        suggest_creating_github_release(config.github_url, tag_name)


def suggest_creating_github_release(github_url: str, tag_name: str) -> None:
    query_string = urllib.parse.urlencode({"tag": tag_name})
    if not github_url.endswith("/"):
        github_url += "/"
    full_url = github_url + "releases/new?" + query_string
    ui.info()
    ui.info("Note: create a new release on GitHub by visiting:")
    ui.info(ui.tabs(1), full_url)


def main(args: Optional[List[str]] = None) -> None:
    # Supress backtrace if exception derives from tbump.Error
    if not args:
        args = sys.argv[1:]
    try:
        run(args)
    except tbump.Error as error:
        error.print_error()
        sys.exit(1)
