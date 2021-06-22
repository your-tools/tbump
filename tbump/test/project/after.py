""" Fake hook used for testing.
Just write a file named after-hook.stamp when called,
so that test code can check if the hook ran
"""

from pathlib import Path


def main() -> None:
    Path("after-hook.stamp").write_text("")


if __name__ == "__main__":
    main()
