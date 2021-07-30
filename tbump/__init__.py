import pprint


class Error(Exception):
    def print_error(self) -> None:
        pass

    def __str__(self) -> str:
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(vars(self))


# Part of the public API, and must be *after* Error is defined
from tbump.file_bumper import bump_files  # noqa: F401, E402
