""" This hooks crashes if the repo is dirty,
so it must be run *after* the push of the commit and tag

"""
import sys

from path import Path
import tbump.git


def main():
    this_path = Path(".")
    _, out = tbump.git.run_git_captured(this_path, "status", "--porcelain")
    dirty = False
    for line in out.splitlines():
        # Ignore untracked files
        if not line.startswith("??"):
            dirty = True
    if dirty:
        sys.exit("Repository is dirty")


if __name__ == "__main__":
    main()
