import sys

import ui

import tbump.git


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

    def check_dirty(self):
        rc, out = self.run_git("status", "--porcelain", raises=False)
        if rc != 0:
            ui.fatal("git status failed")
        dirty = False
        for line in out.splitlines():
            # Ignore untracked files
            if not line.startswith("??"):
                dirty = True
        if dirty:
            ui.error("Repository is dirty")
            ui.info(out)
            sys.exit(1)

    def get_current_branch(self):
        cmd = ("rev-parse", "--abbrev-ref", "HEAD")
        rc, out = self.run_git(*cmd, raises=False)
        if rc != 0:
            ui.fatal("Failed to get current ref")
        if out == "HEAD":
            ui.fatal("Not on any branch")
        return out

    def get_tracking_ref(self):
        rc, out = self.run_git(
            "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}",
            raises=False)
        if rc != 0:
            ui.fatal("Failed to get tracking ref")
        return out

    def check_ref_does_not_exists(self, tag_name):
        rc, _ = self.run_git("rev-parse", tag_name, raises=False)
        if rc == 0:
            ui.fatal("git ref", tag_name, "already exists")

    def check_state(self, new_version):
        self.check_dirty()
        branch_name = self.get_current_branch()
        tracking_ref = self.get_tracking_ref()
        self.remote_name, self.remote_branch = tracking_ref.split("/", maxsplit=1)

        tag_name = self.tag_template.format(new_version=new_version)
        self.check_ref_does_not_exists(tag_name)

    def commit(self, message, dry_run=False):
        if dry_run:
            ui.info_2("Would commit with message: '%s'" % message)
        else:
            ui.info_2("Making bump commit")
            self.run_git("add", "--update")
            self.run_git("commit", "--message", message)

    def tag(self, tag_name, dry_run=False):
        if dry_run:
            ui.info_2("Would create tag:", tag_name)
        else:
            ui.info_2("Creating tag", tag_name)
            self.run_git("tag", tag_name)

    def bump(self, new_version, dry_run=False):
        message = self.message_template.format(new_version=new_version)
        self.commit(message, dry_run=dry_run)
        tag_name = self.tag_template.format(new_version=new_version)
        self.tag(tag_name, dry_run=dry_run)

    def push(self, new_version):
        tag_name = self.tag_template.format(new_version=new_version)
        self.run_git("push", self.remote_name, self.remote_branch, tag_name, verbose=True)
