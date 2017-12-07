import argparse
import os

import path
import ui

import tbump.config
from tbump.git import run_git


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


def check_dirty(working_path):
    rc, out = run_git(working_path, "status", "--porcelain", raises=False)
    if rc != 0:
        ui.fatal("git status failed")
    dirty = False
    for line in out.splitlines():
        if line.startswith("??"):
            ui.warning(line, end="")
            dirty = True
    if dirty:
        ui.fatal("Repository is dirty")


def commit(working_path, new_version):
    ui.info_2("Making bump commit")
    run_git(working_path, "add", ".")
    run_git(working_path, "commit", "--message", "Bump to %s" % new_version)


def tag(working_path, tag):
    ui.info_2("Creating tag", tag)
    run_git(working_path, "tag", tag)


def commit_and_tag(config, new_version):
    working_path = path.Path.getcwd()
    check_dirty(working_path)
    commit(working_path, new_version)
    tag_name = config.tag_template.format(new_version=new_version)
    tag(working_path, tag_name)


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
    parser = argparse.ArgumentParser()
    parser.add_argument("new_version")
    parser.add_argument("-C", "--cwd", dest="working_dir")
    args = parser.parse_args(args=args)
    working_dir = args.working_dir
    new_version = args.new_version
    if working_dir:
        os.chdir(working_dir)
    config = parse_config()
    ui.info_1(
            "Bumping from",
            ui.reset, ui.bold, config.current_version,
            ui.reset, "to",
            ui.reset, ui.bold, new_version)
    bump_version(config, new_version)
    commit_and_tag(config, new_version)
