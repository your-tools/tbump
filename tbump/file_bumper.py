import collections
import sys

import attr
import path
import ui

import tbump.config
import tbump.git


@attr.s
class Change:
    src = attr.ib()
    old = attr.ib()
    new = attr.ib()
    search = attr.ib(default=None)


@attr.s
class Replacement:
    old = attr.ib()
    new = attr.ib()


def should_replace(line, old_string, search=None):
    if not search:
        return old_string in line
    else:
        return (old_string in line) and (search in line)


def find_replacements(file_path, old_string, new_string, search=None):
    old_lines = file_path.lines()
    replacements = dict()
    for i, old_line in enumerate(old_lines):
        if should_replace(old_line, old_string, search):
            new_line = old_line.replace(old_string, new_string)
            replacements[i] = Replacement(old_line, new_line)
    return replacements


def display_replacements(file_path, replacements, dry_run=False):
    if dry_run:
        ui.info_2("Would patch",
                  ui.reset, ui.bold, file_path.basename())
    else:
        ui.info_2("Patching",
                  ui.reset, ui.bold, file_path.basename())
    changed = False
    for replacement in replacements.values():
        if replacement.old != replacement.new:
            changed = True
            ui.info(ui.red, "-", replacement.old, end="")
            ui.info(ui.green, "+", replacement.new, end="")
    if not changed:
        ui.info(ui.brown, "No changes")


def replace_in_file(file_path, replacements, dry_run=False):
    display_replacements(file_path, replacements, dry_run=dry_run)
    if dry_run:
        return
    new_contents = ""
    old_lines = file_path.lines()
    for i, old_line in enumerate(old_lines):
        replacement = replacements.get(i)
        if replacement:
            new_contents += replacement.new
        else:
            new_contents += old_line
    file_path.write_text(new_contents)


class FileBumper():
    def __init__(self, working_path):
        self.working_path = working_path
        self.files = None
        self.version_regex = None
        self.current_version = None
        self.current_groups = None
        self.new_version = None
        self.new_groups = None

    def set_config(self, config):
        self.files = config.files
        self.check_files_exist()
        self.version_regex = config.version_regex
        self.current_version = config.current_version
        self.current_groups = self.version_regex.match(self.current_version).groupdict()

    def check_files_exist(self):
        for file in self.files:
            expected_path = self.working_path.joinpath(file.src)
            if not expected_path.exists():
                ui.fatal(str(expected_path), "does not exist")

    def compute_changes(self, new_version):
        self.new_version = new_version
        self.new_groups = self.version_regex.match(new_version).groupdict()
        res = list()
        tbump_toml_change = Change("tbump.toml", self.current_version, new_version)
        res.append(tbump_toml_change)
        for file in self.files:
            change = self.compute_changes_for_file(file)
            res.append(change)
        return res

    def compute_changes_for_file(self, file):
        if file.version_template:
            current_version = file.version_template.format(**self.current_groups)
            new_version = file.version_template.format(**self.new_groups)
        else:
            current_version = self.current_version
            new_version = self.new_version

        to_search = None
        if file.search:
            to_search = file.search.format(current_version=current_version)

        return Change(file.src, current_version, new_version, search=to_search)
        return res

    def apply_changes(self, changes, dry_run=False):
        todo = collections.OrderedDict()
        errors = list()
        for change in changes:
            file_path = path.Path(self.working_path).joinpath(change.src)
            replacements = find_replacements(file_path, change.old, change.new,
                                             search=change.search)
            todo[file_path] = replacements
            if not replacements:
                errors.append(change.src)

        if errors:
            message = [" Some files did not match the old version string\n"]
            for error in errors:
                message.extend([ui.reset, " * ", ui.bold, error, "\n"])
            ui.fatal(*message, sep="", end="")

        for file_path, replacements in todo.items():
            replace_in_file(file_path, replacements, dry_run=dry_run)
