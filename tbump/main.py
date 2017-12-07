import path
import ui

import tbump.config


def display_diffs(file_path, diffs):
    ui.info_2("Patching",
              ui.reset, ui.bold, file_path)
    for old, new in diffs:
        ui.info(ui.red, "-", old)
        ui.info(ui.green, "+", old)


def should_replace(line, old_string, search=None):
    if not search:
        return old_string in line
    else:
        return (old_string in line) and (search in line)


def replace_in_file(file_path, old_string, new_string, search=None):
    old_lines = file_path.lines(retain=False)
    diffs = list()
    new_lines = list()
    for old_line in old_lines:
        new_line = old_line
        if should_replace(old_line, old_string, search):
            new_line = old_line.replace(old_string, new_string)
            diffs.append((old_line, new_line))
        new_lines.append(new_line)
    display_diffs(file_path, diffs)
    file_path.write_lines(new_lines)


def parse_config():
    config = tbump.config.parse(path.Path("tbump.toml"))
    return config


def bump_version(config, new_version):
    current_version = config.current_version
    for file in config.files:
        file_path = path.Path(file.src)
        to_search = None
        if file.search:
            to_search = file.search.format(current_version=current_version)
        replace_in_file(file_path, current_version, new_version, search=to_search)
    replace_in_file(path.Path("tbump.toml"), current_version, new_version)


def main(args):
    new_version = args[0]
    config = parse_config()
    ui.info_1(
            "Bumping from",
            ui.reset, ui.bold, config.current_version,
            ui.reset, "to",
            ui.reset, ui.bold, new_version)
    bump_version(config, new_version)
