from pathlib import Path
from typing import List, Tuple

import cli_ui as ui

from tbump.action import Action
from tbump.config import Config
from tbump.git import GitError, print_git_command, run_git, run_git_captured


class DirtyRepository(GitError):
    def __init__(self, *, git_status_output: str):
        super().__init__()
        self.git_status_output = git_status_output

    def print_error(self) -> None:
        ui.error("Repository is dirty")
        ui.info(self.git_status_output)


class NotOnAnyBranch(GitError):
    def print_error(self) -> None:
        ui.error("Not on any branch")


class NoTrackedBranch(GitError):
    def __init__(self, *, branch: str):
        super().__init__()
        self.branch = branch

    def print_error(self) -> None:
        ui.error(
            "Current branch (%s)" % self.branch, "does not track anything. Cannot push."
        )


class RefAlreadyExists(GitError):
    def __init__(self, *, ref: str):
        super().__init__()
        self.ref = ref

    def print_error(self) -> None:
        ui.error("git ref", self.ref, "already exists")


class Command(Action):
    def __init__(self, repo_path: Path, cmd: List[str]):
        super().__init__()
        self.repo_path = repo_path
        self.cmd = list(cmd)
        self.verbose = True

    def print_self(self) -> None:
        print_git_command(self.cmd)

    def do(self) -> None:
        self.run()

    def run(self) -> None:
        return run_git(self.repo_path, *self.cmd, verbose=False)


class GitBumper:
    def __init__(self, repo_path: Path, operations: List[str]):
        self.repo_path = repo_path
        self.tag_template = ""
        self.message_template = ""
        self.remote_name = ""
        self.remote_branch = ""
        self.operations = operations
        self.commands: List[Command] = []

    def get_tag_name(self, new_version: str) -> str:
        return self.tag_template.format(new_version=new_version)

    def set_config(self, config: Config) -> None:
        self.tag_template = config.git_tag_template
        self.message_template = config.git_message_template

    def run_git(self, *args: str, verbose: bool = False) -> None:
        return run_git(self.repo_path, *args, verbose=verbose)

    def run_git_captured(self, *args: str, check: bool = True) -> Tuple[int, str]:
        return run_git_captured(self.repo_path, *args, check=check)

    def check_dirty(self) -> None:
        if "commit" not in self.operations:
            return
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
            "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False
        )
        if rc != 0:
            raise NoTrackedBranch(branch=branch_name)
        return out

    def check_ref_does_not_exists(self, tag_name: str) -> None:
        rc, _ = self.run_git_captured("rev-parse", tag_name, check=False)
        if rc == 0:
            raise RefAlreadyExists(ref=tag_name)

    def check_branch_state(self, new_version: str) -> None:
        if "commit" not in self.operations:
            return
        if "tag" in self.operations:
            tag_name = self.get_tag_name(new_version)
            self.check_ref_does_not_exists(tag_name)

        if "push_commit" in self.operations:
            self.get_current_branch()
            tracking_ref = self.get_tracking_ref()
            self.remote_name, self.remote_branch = tracking_ref.split("/", maxsplit=1)

    def add_command(self, commands: List[Command], *cmd: str) -> None:
        command = Command(self.repo_path, list(cmd))
        commands.append(command)

    def get_commands(self, new_version: str) -> List[Command]:
        res: List[Command] = []
        if "commit" not in self.operations:
            return res
        self.add_command(res, "add", "--update")
        commit_message = self.message_template.format(new_version=new_version)
        self.add_command(res, "commit", "--message", commit_message)
        tag_name = self.get_tag_name(new_version)
        tag_message = tag_name
        if "tag" in self.operations:
            self.add_command(
                res, "tag", "--annotate", "--message", tag_message, tag_name
            )
        if "push_commit" in self.operations and "push_tag" in self.operations:
            self.add_command(
                res, "push", "--atomic", self.remote_name, self.remote_branch, tag_name
            )

        elif "push_commit" in self.operations:
            self.add_command(res, "push", self.remote_name, self.remote_branch)
        elif "push_tag" in self.operations:
            self.add_command(res, "push", self.remote_name, tag_name)
        # else do nothing
        return res
