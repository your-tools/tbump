import collections

import attr
import path
import ui

import tbump
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


class BadSubstitution(tbump.Error):
    def print_error(self):
        message = [
            " ", self.src + ":",
            " refusing to ", self.verb, " version containing 'None'\n",
        ]
        message += [
            "More info:\n",
            " * version groups:  ", self.groups, "\n"
            " * template:        ", self.template, "\n",
            " * version:         ", self.version, "\n",
        ]
        ui.error(*message, end="", sep="")


class InvalidVersion(tbump.Error):
    def print_error(self):
        ui.error("Could not parse", self.version, "as a valid version string")


class SourceFileNotFound(tbump.Error):
    def print_error(self):
        ui.error(self.src, "does not exist")


class OldVersionNotFound(tbump.Error):
    def print_error(self):
        message = [" Some files did not match the old version string\n"]
        for src in self.sources:
            message.extend([ui.reset, " * ", ui.bold, src, "\n"])
        ui.error(*message, sep="", end="")


def should_replace(line, old_string, search=None):
    if not search:
        return old_string in line
    else:
        return (old_string in line) and (search in line)


def on_version_containing_none(src, verb, version, *, groups, template):
    raise BadSubstitution(src=src, verb=verb, version=version, groups=groups, template=template)


def find_replacements(file_path, old_string, new_string, search=None):
    old_lines = file_path.lines()
    replacements = dict()
    for i, old_line in enumerate(old_lines):
        if should_replace(old_line, old_string, search):
            new_line = old_line.replace(old_string, new_string)
            replacements[i] = Replacement(old_line, new_line)
    return replacements


class FileBumper():
    def __init__(self, working_path):
        self.working_path = working_path
        self.files = None
        self.version_regex = None
        self.current_version = None
        self.current_groups = None
        self.new_version = None
        self.new_groups = None

    def replace_in_file(self, file_path, replacements, dry_run=False):
        self.display_replacements(file_path, replacements, dry_run=dry_run)
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

    def display_replacements(self, file_path, replacements, dry_run=False):
        relpath = self.working_path.relpathto(file_path)
        if dry_run:
            ui.info_2("Would patch",
                      ui.reset, ui.bold, relpath)
        else:
            ui.info_2("Patching",
                      ui.reset, ui.bold, relpath)
        changed = False
        for replacement in replacements.values():
            if replacement.old != replacement.new:
                changed = True
                ui.info(ui.red, "-", replacement.old, end="")
                ui.info(ui.green, "+", replacement.new, end="")
        if not changed:
            ui.info(ui.brown, "No changes")

    def parse_version(self, version):
        match = self.version_regex.fullmatch(version)
        if match is None:
            raise InvalidVersion(version=version, regex=self.version_regex)
        return match.groupdict()

    def set_config(self, config):
        self.files = config.files
        self.check_files_exist()
        self.version_regex = config.version_regex
        self.current_version = config.current_version
        self.current_groups = self.parse_version(self.current_version)

    def check_files_exist(self):
        for file in self.files:
            expected_path = self.working_path.joinpath(file.src)
            if not expected_path.exists():
                raise SourceFileNotFound(src=file.src)

    def compute_changes(self, new_version):
        self.new_version = new_version
        self.new_groups = self.parse_version(self.new_version)
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
            if "None" in current_version:
                on_version_containing_none(
                    file.src,
                    "look for",
                    current_version,
                    groups=self.current_groups,
                    template=file.version_template
                )
            new_version = file.version_template.format(**self.new_groups)
            if "None" in new_version:
                on_version_containing_none(
                    file.src,
                    "replace by",
                    new_version,
                    groups=self.new_groups,
                    template=file.version_template
                )
        else:
            current_version = self.current_version
            new_version = self.new_version

        to_search = None
        if file.search:
            to_search = file.search.format(current_version=current_version)

        return Change(file.src, current_version, new_version, search=to_search)

    def apply_changes(self, changes, dry_run=False):
        todo = collections.OrderedDict()
        errors = list()
        for change in changes:
            file_path = path.Path(self.working_path).joinpath(change.src)
            replacements = find_replacements(file_path, change.old, change.new,
                                             search=change.search)
            if file_path not in todo:
                todo[file_path] = dict()
            todo[file_path].update(replacements)
            if not replacements:
                errors.append(change.src)

        if errors:
            raise OldVersionNotFound(sources=errors)

        for file_path, replacements in todo.items():
            self.replace_in_file(file_path, replacements, dry_run=dry_run)
