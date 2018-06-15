from typing import Any


class Error(Exception):
    def __init__(self, **kwargs: Any) -> None:
        self._dict = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    def print_error(self) -> None:
        pass

    def __repr__(self) -> str:
        return "<%s: %s>" % (self.__class__.__name__, repr(self._dict))
