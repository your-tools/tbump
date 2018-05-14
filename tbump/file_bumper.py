import attr
import path
import ui

import tbump
import tbump.config
import tbump.git


def print_patch(patch):
    ui.info(
        ui.red, "- ", ui.reset,
        ui.bold, patch.src, ":", ui.reset,
        ui.darkgray, patch.lineno + 1, ui.reset,
        " ", ui.red, patch.old_line.strip(),
        sep=""
    )
    ui.info(
        ui.green, "+ ", ui.reset,
        ui.bold, patch.src, ":", ui.reset,
        ui.darkgray, patch.lineno + 1, ui.reset,
        " ", ui.green, patch.new_line.strip(),
        sep=""
    )


@attr.s
class ChangeRequest:
    src = attr.ib()
    old_string = attr.ib()
    new_string = attr.ib()
    search = attr.ib(default=None)


@attr.s
class Patch:
    src = attr.ib()
    lineno = attr.ib()
    old_line = attr.ib()
    new_line = attr.ib()


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


class CurrentVersionNotFound(tbump.Error):
    # TODO: raise just once for all errors
    def print_error(self):
        ui.error(
            "Current version string: (%s)" % self.current_version_string,
            "not found in", self.src
        )


def should_replace(line, old_string, search=None):
    if not search:
        return old_string in line
    else:
        return (old_string in line) and (search in line)


def on_version_containing_none(src, verb, version, *, groups, template):
    raise BadSubstitution(src=src, verb=verb, version=version, groups=groups, template=template)


class FileBumper():
    def __init__(self, working_path):
        self.working_path = working_path
        self.files = None
        self.version_regex = None
        self.current_version = None
        self.current_groups = None
        self.new_version = None
        self.new_groups = None

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

    def compute_patches(self, new_version):
        self.new_version = new_version
        self.new_groups = self.parse_version(self.new_version)
        change_requests = self.compute_change_requests()
        tbump_toml_change = ChangeRequest("tbump.toml", self.current_version, new_version)
        change_requests.append(tbump_toml_change)
        patches = list()
        for change_request in change_requests:
            patches_for_request = self.compute_patches_for_change_request(change_request)
            patches.extend(patches_for_request)
        return patches

    def compute_patches_for_change_request(self, change_request):
        old_string = change_request.old_string
        new_string = change_request.new_string
        search = change_request.search

        file_path = path.Path(self.working_path).joinpath(change_request.src)
        old_lines = file_path.lines()

        patches = list()
        for i, old_line in enumerate(old_lines):
            if should_replace(old_line, old_string, search):
                new_line = old_line.replace(old_string, new_string)
                patch = Patch(change_request.src, i, old_line, new_line)
                patches.append(patch)
        if not patches:
            raise CurrentVersionNotFound(src=change_request.src, current_version_string=old_string)
        return patches

    def compute_change_requests(self):
        change_requests = list()
        for file in self.files:
            change_request = self.compute_change_request_for_file(file)
            change_requests.append(change_request)
        return change_requests

    def compute_change_request_for_file(self, file):
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

        return ChangeRequest(file.src, current_version, new_version, search=to_search)

    def apply_patches(self, patches):
        for patch in patches:
            print_patch(patch)
            file_path = path.Path(self.working_path).joinpath(patch.src)
            # TODO: read and write each file only once?
            lines = file_path.lines()
            lines[patch.lineno] = patch.new_line
            file_path.write_lines(lines)
