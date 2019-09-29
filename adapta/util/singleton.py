def singleton(cls):
    """Singleton class decorator."""

    cls._instance = None

    def new(func):
        def func_(cls):
            if cls._instance is None:
                return func(cls)
            return cls._instance
        return func_

    def init(func):
        def func_(self):
            if cls._instance is None:
                cls._instance = self
                func(self)
        return func_

    cls.__new__ = new(cls.__new__)
    cls.__init__ = init(cls.__init__)
    return cls
