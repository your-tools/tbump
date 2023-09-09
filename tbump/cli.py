import sys
import textwrap
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, cast

import cli_ui as ui
import docopt

from tbump.config import get_config_file
from tbump.error import Error
from tbump.executor import Executor
from tbump.file_bumper import FileBumper
from tbump.git import GitError
from tbump.git_bumper import GitBumper, GitBumperOptions
from tbump.hooks import HooksRunner
from tbump.init import init

TBUMP_VERSION = "6.11.0"

USAGE = textwrap.dedent(
    """
Usage:
  tbump [options] <new_version>
  tbump [options] current-version
  tbump [options] init [--pyproject] <current_version>
  tbump --help
  tbump --version

Options:
   -h --help           Show this screen.
   -v --version        Show version.
   -C --cwd=<path>     Set working directory to <path>.
   -c --config=<path>  Use specified toml config file. When not set, `tbump.toml` is assumed.
   --non-interactive   Never prompt for confirmation. Useful for automated scripts.
   --dry-run           Only display the changes that would be made.
   --tag-message=<msg> Message to use for tag instead of being based on the tag template
   --only-patch        Only patches files, skipping any git operations or hook commands.
   --no-tag            Do not create a tag
   --no-push           Do not push after creating the commit and/or tag
   --no-tag-push       Create a tag, but don't push it
"""
)


class Canceled(Error):
    def print_error(self) -> None:
        ui.error("Canceled by user")


@dataclass
class BumpOptions:
    working_path: Path
    new_version: str
    interactive: bool = True
    dry_run: bool = False
    config_path: Optional[Path] = None
    tag_message: Optional[str] = None


class Command(Enum):
    bump = "bump"
    init = "init"
    current_version = "current_version"
    version = "version"


def print_diff(filename: str, lineno: int, old: str, new: str) -> None:
    # fmt: off
    ui.info(
        ui.red, "- ", ui.reset,
        ui.bold, filename, ":", lineno, ui.reset,
        " ", ui.red, old,
        sep="",
    )
    ui.info(
        ui.green, "+ ", ui.reset,
        ui.bold, filename, ":", lineno,  ui.reset,
        " ", ui.green, new,
        sep="",
    )
    # fmt: on


@dataclass
class GivenCliArguments:
    """
    Values of the CLI arguments that were given.

    Bool values indicate that that argument was given, NOT the intended behavior of the program.
    """

    command: Command
    bump_new_version: Optional[str]
    init_current_version: Optional[str]
    init_pyproject: bool
    working_path: Optional[Path]
    config_path: Optional[Path]
    tag_message: Optional[str]
    non_interactive: bool
    dry_run: bool
    only_patch: bool
    no_tag: bool
    no_push: bool
    no_tag_push: bool

    @classmethod
    def from_opts(
        cls, opt_dict: Dict[str, Union[bool, Optional[str]]]
    ) -> "GivenCliArguments":
        def _get_path(key: str) -> Optional[Path]:
            value = opt_dict[key]
            if value is None:
                return None
            return Path(cast(str, value))

        def _get_str(key: str) -> Optional[str]:
            return cast(Optional[str], opt_dict[key])

        def _get_bool(key: str) -> bool:
            return cast(bool, opt_dict[key])

        # docopt has a hard time parsing the commands because run_bump uses that same cli slot for
        # the new version. This corrects those issues.
        command = Command.bump
        new_version = opt_dict["<new_version>"]
        if new_version == "init" or opt_dict["init"]:
            command = Command.init
        elif new_version == "current-version":
            command = Command.current_version
        elif opt_dict["--version"]:
            command = Command.version

        return cls(
            command=command,
            bump_new_version=_get_str("<new_version>"),
            init_current_version=_get_str("<current_version>"),
            init_pyproject=_get_bool("--pyproject"),
            working_path=_get_path("--cwd"),
            config_path=_get_path("--config"),
            non_interactive=_get_bool("--non-interactive"),
            dry_run=_get_bool("--dry-run"),
            only_patch=_get_bool("--only-patch"),
            tag_message=_get_str("--tag-message"),
            no_tag=_get_bool("--no-tag"),
            no_push=_get_bool("--no-push"),
            no_tag_push=_get_bool("--no-tag-push"),
        )


def run(cmd: List[str]) -> None:
    opt_dict = docopt.docopt(USAGE, argv=cmd)
    arguments = GivenCliArguments.from_opts(opt_dict)

    if arguments.command == Command.version:
        print("tbump", TBUMP_VERSION)
        return

    # when running `tbump init` (with current_version missing),
    # docopt thinks we are running `tbump` with new_version = "init"
    # bail out early in this case
    if arguments.command == Command.init and arguments.init_current_version is None:
        sys.exit(USAGE)

    # if a path wasn't given, use current working directory
    working_path = arguments.working_path or Path.cwd()

    # Ditto for `tbump current-version`
    if arguments.command == Command.current_version:
        config_file = get_config_file(
            working_path,
            specified_config_path=arguments.config_path,
        )
        config = config_file.get_config()
        print(config.current_version)
        return

    if arguments.command == Command.init:
        run_init(arguments, working_path)
        return

    run_bump(arguments, working_path, arguments.tag_message)


def run_init(arguments: GivenCliArguments, working_path: Path) -> None:
    init(
        working_path,
        current_version=cast(str, arguments.init_current_version),
        use_pyproject=arguments.init_pyproject,
        specified_config_path=arguments.config_path,
    )


def run_bump(
    arguments: GivenCliArguments, working_path: Path, tag_message: Optional[str]
) -> None:
    bump_options = BumpOptions(
        working_path=working_path,
        tag_message=tag_message,
        new_version=cast(str, arguments.bump_new_version),
        config_path=arguments.config_path,
        dry_run=arguments.dry_run,
        interactive=not arguments.non_interactive,
    )

    bump(bump_options, _construct_operations(arguments))


def bump(options: BumpOptions, operations: List[str]) -> None:
    working_path = options.working_path
    new_version = options.new_version
    interactive = options.interactive
    dry_run = options.dry_run
    specified_config_path = options.config_path

    config_file = get_config_file(
        options.working_path, specified_config_path=specified_config_path
    )
    config = config_file.get_config()

    # fmt: off
    ui.info_1(
        "Bumping from", ui.bold, config.current_version,
        ui.reset, "to", ui.bold, new_version,
    )
    # fmt: on

    bumper_options = GitBumperOptions(
        working_path=options.working_path,
        tag_message=options.tag_message,
    )
    git_bumper = GitBumper(bumper_options, operations)
    git_bumper.set_config(config)
    git_state_error = None
    try:
        git_bumper.check_dirty()
        git_bumper.check_branch_state(new_version)
    except GitError as e:
        if dry_run:
            git_state_error = e
        else:
            raise

    file_bumper = FileBumper(working_path, config)
    file_bumper.check_files_exist()
    config_file.set_new_version(new_version)

    executor = Executor(new_version, file_bumper, config_file)

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
                raise Canceled()

    if dry_run:
        if git_state_error:
            ui.error("Git repository state is invalid")
            git_state_error.print_error()
            sys.exit(1)
        else:
            return

    executor.run()

    if config.github_url and "push_tag" in operations:
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
    # Suppress backtrace if exception derives from Error
    if not args:
        args = sys.argv[1:]
    try:
        run(args)
    except Error as error:
        error.print_error()
        sys.exit(1)


def _construct_operations(arguments: GivenCliArguments) -> List[str]:
    operations = ["patch", "hooks", "commit", "tag", "push_commit", "push_tag"]
    if arguments.only_patch:
        operations = ["patch"]
    if arguments.no_push:
        operations.remove("push_commit")
        operations.remove("push_tag")
    if arguments.no_tag_push:
        # may have been removed by the above line
        if "push_tag" in operations:
            operations.remove("push_tag")
    if arguments.no_tag:
        operations.remove("tag")
        # Also remove push_tag if it's still in the list:
        if "push_tag" in operations:
            operations.remove("push_tag")
    return operations
