from typing import List, Tuple
from path import Path
import cli_ui as ui

import tbump.action
from tbump.config import Config
import tbump.git


class DirtyRepository(tbump.git.GitError):
    def __init__(self, *, git_status_output: str):
        super().__init__()
        self.git_status_output = git_status_output

    def print_error(self) -> None:
        ui.error("Repository is dirty")
        ui.info(self.git_status_output)


class NotOnAnyBranch(tbump.git.GitError):
    def print_error(self) -> None:
        ui.error("Not on any branch")


class NoTrackedBranch(tbump.git.GitError):
    def __init__(self, *, branch: str):
        super().__init__()
        self.branch = branch

    def print_error(self) -> None:
        ui.error("Current branch (%s)" % self.branch,
                 "does not track anything. Cannot push.")


class RefAlreadyExists(tbump.git.GitError):
    def __init__(self, *, ref: str):
        super().__init__()
        self.ref = ref

    def print_error(self) -> None:
        ui.error("git ref", self.ref, "already exists")


class Command(tbump.action.Action):
    def __init__(self, repo_path: Path, cmd: List[str]):
        super().__init__()
        self.repo_path = repo_path
        self.cmd = list(cmd)
        self.verbose = True

    def print_self(self) -> None:
        tbump.git.print_git_command(self.cmd)

    def do(self) -> None:
        self.run()

    def run(self) -> None:
        full_args = [self.repo_path] + self.cmd
        return tbump.git.run_git(*full_args, verbose=False)


class GitBumper():
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.tag_template = ""
        self.message_template = ""
        self.remote_name = ""
        self.remote_branch = ""
        self.commands = list()  # type: List[Command]

    def set_config(self, config: Config) -> None:
        self.tag_template = config.tag_template
        self.message_template = config.message_template

    def run_git(self, *args: str, verbose: bool = False) -> None:
        full_args = [self.repo_path] + list(args)
        return tbump.git.run_git(*full_args, verbose=verbose)

    def run_git_captured(self, *args: str, check: bool = True) -> Tuple[int, str]:
        full_args = [self.repo_path] + list(args)
        return tbump.git.run_git_captured(*full_args, check=check)

    def check_dirty(self) -> None:
        _, out = self.run_git_captured("status", "--porcelain")
        dirty = False
        for line in out.splitlines():
            # Ignore untracked files
            if not line.startswith("??"):
                dirty = True
        if dirty:
            raise DirtyRepository(git_status_output=out)

    def get_current_branch(self) -> str:
        cmd = ("rev-parse", "--abbrev-ref", "HEAD")
        _, out = self.run_git_captured(*cmd)
        if out == "HEAD":
            raise NotOnAnyBranch()
        return out

    def get_tracking_ref(self) -> str:
        branch_name = self.get_current_branch()
        rc, out = self.run_git_captured(
            "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}",
            check=False)
        if rc != 0:
            raise NoTrackedBranch(branch=branch_name)
        return out

    def check_ref_does_not_exists(self, tag_name: str) -> None:
        rc, _ = self.run_git_captured("rev-parse", tag_name, check=False)
        if rc == 0:
            raise RefAlreadyExists(ref=tag_name)

    def check_state(self, new_version: str) -> None:
        self.check_dirty()
        self.get_current_branch()
        tag_name = self.tag_template.format(new_version=new_version)
        self.check_ref_does_not_exists(tag_name)

        tracking_ref = self.get_tracking_ref()
        self.remote_name, self.remote_branch = tracking_ref.split("/", maxsplit=1)

    def add_command(self, commands: List[Command], *cmd: str) -> None:
        command = Command(self.repo_path, list(cmd))
        commands.append(command)

    def get_commands(self, new_version: str) -> List[Command]:
        res = list()  # type: List[Command]
        self.add_command(res, "add", "--update")
        commit_message = self.message_template.format(new_version=new_version)
        self.add_command(res, "commit", "--message", commit_message)
        tag_name = self.tag_template.format(new_version=new_version)
        tag_message = tag_name
        self.add_command(res, "tag", "--annotate", "--message", tag_message, tag_name)
        self.add_command(res, "push", self.remote_name, self.remote_branch)
        self.add_command(res, "push", self.remote_name, tag_name)
        return res
