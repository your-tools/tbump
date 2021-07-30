import pprint


class Error(Exception):
    def print_error(self) -> None:
        pass

    def __str__(self) -> str:
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(vars(self))
