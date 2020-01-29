""" This hooks crashes if the repo is dirty,
so it must be run *after* the push of the commit and tag

"""
import sys
import subprocess


def main():
    process = subprocess.run(
        ["git", "status", "--porcelain"], stdout=subprocess.PIPE, check=True
    )
    dirty = False
    for line in process.stdout.decode().splitlines():
        # Ignore untracked files
        if not line.startswith("??"):
            dirty = True
    if dirty:
        sys.exit("Repository is dirty")


if __name__ == "__main__":
    main()
