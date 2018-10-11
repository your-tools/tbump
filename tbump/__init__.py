class Error(Exception):
    def print_error(self) -> None:
        pass

from .file_bumper import bump_files  # noqa
