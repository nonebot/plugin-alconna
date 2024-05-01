from typing import Callable, TypeVar

TCallable = TypeVar("TCallable", bound=Callable)


def annotation(**types):
    def wrapper(func: TCallable) -> TCallable:
        func.__annotations__ = types
        return func
    return wrapper
