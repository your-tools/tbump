class Error(Exception):
    def __init__(self, **kwargs):
        self._dict = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    def print_error(self):
        pass

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, repr(self._dict))
