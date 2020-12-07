"""Result module.

The Result[TSource,TError] type lets you write error-tolerant code that
can be composed. The Result type is typically used in monadic
error-handling, which is often referred to as Railway-oriented
Programming.

There is also a simplifyed alias of this type called `Maybe` that pins
the Result type to Exception.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generator, Iterable, Iterator, Type, TypeVar, Union, get_origin, overload

from .error import EffectError
from .match import Case, SupportsMatch
from .pipe import pipe

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TError = TypeVar("TError")

# Underscore types are used for generic methods
_TSource = TypeVar("_TSource")
_TError = TypeVar("_TError")

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")


class Result(Iterable[Union[TSource, TError]], SupportsMatch[Union[TSource, TError]], ABC):
    """The result abstract base class."""

    @overload
    def pipe(self, __fn1: Callable[["Result[TSource, TError]"], TResult]) -> TResult:
        ...

    @overload
    def pipe(self, __fn1: Callable[["Result[TSource, TError]"], T1], __fn2: Callable[[T1], T2]) -> T2:
        ...

    @overload
    def pipe(
        self, __fn1: Callable[["Result[TSource, TError]"], T1], __fn2: Callable[[T1], T2], __fn3: Callable[[T2], T3]
    ) -> T3:
        ...

    @overload
    def pipe(
        self,
        __fn1: Callable[["Result[TSource, TError]"], T1],
        __fn2: Callable[[T1], T2],
        __fn3: Callable[[T2], T3],
        __fn4: Callable[[T3], T4],
    ) -> T4:
        ...

    def pipe(self, *args: Any):
        """Pipe result through the given functions."""
        return pipe(self, *args)

    @abstractmethod
    def map(self, mapper: Callable[[TSource], TResult]) -> "Result[TResult, TError]":
        raise NotImplementedError

    @abstractmethod
    def map_error(self, mapper: Callable[[TError], TResult]) -> "Result[TSource, TResult]":
        """Return a result of the error value after applying the mapping
        function, or Ok if the input is Ok."""
        raise NotImplementedError

    @abstractmethod
    def bind(self, mapper: Callable[[TSource], "Result[TResult, TError]"]) -> "Result[TResult, TError]":
        raise NotImplementedError

    @overload
    def match(self, pattern: "Ok[_TSource, _TError]") -> Iterable[_TSource]:
        ...

    @overload
    def match(self, pattern: "Error[_TSource, _TError]") -> Iterable[_TError]:
        ...

    @overload
    def match(self, pattern: "Case[Ok[_TSource, _TError]]") -> Iterable[_TSource]:
        ...

    @overload
    def match(self, pattern: "Case[Error[_TSource, _TError]]") -> Iterable[_TError]:
        ...

    @overload
    def match(self, pattern: "Type[Result[_TSource, _TError]]") -> Iterable[TSource]:
        ...

    def match(self, pattern: Any) -> Any:
        """Match result with pattern."""

        case: Case[Iterable[Union[TSource, TError]]] = Case(self)
        return case(pattern) if pattern else case

    @abstractmethod
    def is_error(self) -> bool:
        """Returns `True` if the result is an `Error` value."""

        raise NotImplementedError

    @abstractmethod
    def is_ok(self) -> bool:
        """Returns `True` if the result is an `Ok` value."""

        raise NotImplementedError

    def __eq__(self, other: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def __iter__(self) -> Iterator[TSource]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return str(self)


class Ok(
    Result[TSource, TError],
    SupportsMatch[TSource],
):
    """The Ok result case class."""

    def __init__(self, value: TSource) -> None:
        self._value = value

    @property
    def value(self) -> TSource:
        return self._value

    def map(self, mapper: Callable[[TSource], TResult]) -> Result[TResult, TError]:
        return Ok(mapper(self._value))

    def bind(self, mapper: Callable[[TSource], Result[TResult, TError]]) -> Result[TResult, TError]:
        return mapper(self._value)

    def map_error(self, mapper: Callable[[TError], TResult]) -> Result[TSource, TResult]:
        """Return a result of the error value after applying the mapping
        function, or Ok if the input is Ok."""
        return Ok(self._value)

    def is_error(self) -> bool:
        """Returns `True` if the result is an `Ok` value."""

        return False

    def is_ok(self) -> bool:
        """Returns `True` if the result is an `Ok` value."""

        return True

    def __match__(self, pattern: Any) -> Iterable[TSource]:
        if self is pattern or self == pattern:
            return [self.value]

        try:
            origin: Any = get_origin(pattern)
            if isinstance(self, origin or pattern):
                return [self.value]
        except TypeError:
            pass

        return []

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Ok):
            return self.value == other.value  # type: ignore
        return False

    def __iter__(self) -> Generator[TSource, TSource, TSource]:
        """Return iterator for Ok case."""
        return (yield self._value)

    def __str__(self):
        return f"Ok {self._value}"


class ResultException(EffectError):
    """Makes the Error case a valid exception for effect handling. Do
    not use directly."""

    def __init__(self, message: str):
        self.message = message


class Error(Result[TSource, TError], ResultException):
    """The Error result case class."""

    def __init__(self, error: TError) -> None:
        super().__init__(str(error))
        self._error = error

    @property
    def error(self) -> TError:
        return self._error

    def map(self, mapper: Callable[[TSource], TResult]) -> Result[TResult, TError]:
        return Error(self._error)

    def bind(self, mapper: Callable[[TSource], Result[TResult, TError]]) -> Result[TResult, TError]:
        return Error(self._error)

    def map_error(self, mapper: Callable[[TError], TResult]) -> Result[TSource, TResult]:
        """Return a result of the error value after applying the mapping
        function, or Ok if the input is Ok."""
        return Error(mapper(self._error))

    def is_error(self) -> bool:
        """Returns `True` if the result is an `Ok` value."""
        return True

    def is_ok(self) -> bool:
        """Returns `True` if the result is an `Ok` value."""
        return False

    def __match__(self, pattern: Any) -> Iterable[TError]:
        if self is pattern or self == pattern:
            return [self.error]

        try:
            origin: Any = get_origin(pattern)
            if isinstance(self, origin or pattern):
                return [self.error]
        except TypeError:
            pass

        return []

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Error):
            return self.error == other.error  # type: ignore
        return False

    def __iter__(self) -> Iterator[TSource]:
        """Return iterator for Error case."""
        raise Error(self._error)
        while False:
            yield

    def __str__(self):
        return f"Error {self._error}"


def map(mapper: Callable[[TSource], TResult]) -> Callable[[Result[TSource, TError]], Result[TResult, TError]]:
    def _map(result: Result[TSource, TError]) -> Result[TResult, TError]:
        return result.map(mapper)

    return _map


def bind(
    mapper: Callable[[TSource], Result[TResult, TError]]
) -> Callable[[Result[TSource, TError]], Result[TResult, TError]]:
    def _bind(result: Result[TSource, TError]) -> Result[TResult, TError]:
        return result.bind(mapper)

    return _bind


Try = Result[TSource, Exception]


__all__ = ["Result", "Ok", "Error", "map", "bind", "Try"]
