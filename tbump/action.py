import abc


class Action(metaclass=abc.ABCMeta):
    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def print_self(self) -> None:
        pass

    @abc.abstractmethod
    def do(self) -> None:
        pass
