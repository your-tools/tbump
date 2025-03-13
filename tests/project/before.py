""" Fake hook used for testing.
Just write a file named before-hook.stamp when called,
so that test code can check if the hook ran
"""

import sys
from pathlib import Path


def main() -> None:
    current, new = sys.argv[1:]
    Path("before-hook.stamp").write_text(current + " -> " + new)


if __name__ == "__main__":
    main()
