import ui

import tbump.git


class DirtyRepository(tbump.git.GitError):

    def print_error(self):
        ui.error("Repository is dirty")
        ui.info(self.git_status_output)


class NotOnAnyBranch(tbump.git.GitError):
    def print_error(self):
        ui.error("Not on any branch")


class NoTrackedBranch(tbump.git.GitError):
    def print_error(self):
        ui.error("Current branch (%s)" % self.branch,
                 "does not track anything. Cannot push.")


class RefAlreadyExists(tbump.git.GitError):
    def print_error(self):
        ui.error("git ref", self.ref, "already exists")


class GitBumper():
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.tag_template = None
        self.message_template = None
        self.remote_name = None
        self.remote_branch = None

    def set_config(self, config):
        self.tag_template = config.tag_template
        self.message_template = config.message_template

    def run_git(self, *args, **kwargs):
        full_args = [self.repo_path] + list(args)
        return tbump.git.run_git(*full_args, **kwargs)

    def run_git_captured(self, *args, **kwargs):
        full_args = [self.repo_path] + list(args)
        return tbump.git.run_git_captured(*full_args, **kwargs)

    def check_dirty(self):
        _, out = self.run_git_captured("status", "--porcelain")
        dirty = False
        for line in out.splitlines():
            # Ignore untracked files
            if not line.startswith("??"):
                dirty = True
        if dirty:
            raise DirtyRepository(git_status_output=out)

    def get_current_branch(self):
        cmd = ("rev-parse", "--abbrev-ref", "HEAD")
        _, out = self.run_git_captured(*cmd)
        if out == "HEAD":
            raise NotOnAnyBranch()
        return out

    def get_tracking_ref(self):
        branch_name = self.get_current_branch()
        rc, out = self.run_git_captured(
            "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}",
            check=False)
        if rc != 0:
            raise NoTrackedBranch(branch=branch_name)
        return out

    def check_ref_does_not_exists(self, tag_name):
        rc, _ = self.run_git_captured("rev-parse", tag_name, check=False)
        if rc == 0:
            raise RefAlreadyExists(ref=tag_name)

    def check_state(self, new_version):
        self.check_dirty()
        self.get_current_branch()
        tag_name = self.tag_template.format(new_version=new_version)
        self.check_ref_does_not_exists(tag_name)

        tracking_ref = self.get_tracking_ref()
        self.remote_name, self.remote_branch = tracking_ref.split("/", maxsplit=1)

    def compute_commands(self, new_version):
        res = list()
        res.append(["add", "--update"])
        commit_message = self.message_template.format(new_version=new_version)
        res.append(["commit", "--message", commit_message])
        tag_name = self.tag_template.format(new_version=new_version)
        tag_message = tag_name
        res.append(["tag", "--annotate", "--message", tag_message, tag_name])
        if self.remote_branch:
            res.append(["push", self.remote_name, self.remote_branch, tag_name])
        return res

    def run_commands(self, commands):
        for command in commands:
            self.run_git(*command)
