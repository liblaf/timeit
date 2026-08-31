"""Timing state machine and adapters."""

from __future__ import annotations

import contextlib
import contextvars
import functools
import inspect
import statistics
import threading
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType, TracebackType
from typing import Any, Final, Self, overload

from ._clock import CLOCKS, ClockName, clock


def _default_emitter() -> Emitter:
    """Resolve the standard logging adapter without a module import cycle."""
    from ._logging import log_to

    return log_to()


@dataclass(frozen=True, slots=True)
class Statistics:
    """Aggregate values for one clock."""

    total: float
    mean: float
    minimum: float
    maximum: float
    stdev: float


@dataclass(frozen=True, slots=True)
class Record:
    """One completed timing interval."""

    label: str
    index: int
    durations: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class Summary:
    """Aggregate timing statistics."""

    label: str
    count: int
    statistics: Mapping[str, Statistics]


type TimerEvent = Record | Summary
type Emitter = Callable[[TimerEvent], None]


class _DefaultEmitter:
    pass


_DEFAULT_EMITTER: Final = _DefaultEmitter()


@dataclass(slots=True)
class Timer(contextlib.AbstractContextManager["Timer"]):
    """Accumulate timing samples and send immutable events to an emitter.

    Attributes:
        label: Human-readable event label. Decorated callables infer one.
        clocks: Registered clocks measured for every interval.
        emitter: Destination for records and summaries; `None` disables output.

    Examples:
        >>> measured = Timer(emitter=None)
        >>> with measured:
        ...     pass
        >>> len(measured)
        1
    """

    label: str | None = None
    clocks: Sequence[ClockName] = ("perf",)
    emitter: Emitter | None = field(default_factory=_default_emitter)
    _samples: dict[str, list[float]] = field(init=False, repr=False)
    _active: contextvars.ContextVar[dict[str, float] | None] = field(
        init=False, repr=False
    )
    _lock: threading.RLock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.clocks = tuple(self.clocks)
        if not self.clocks:
            msg = "at least one clock is required"
            raise ValueError(msg)
        missing = [name for name in self.clocks if name not in CLOCKS]
        if missing:
            msg = f"unknown clocks: {', '.join(missing)}"
            raise KeyError(msg)
        self._samples = {name: [] for name in self.clocks}
        self._active = contextvars.ContextVar(
            f"liblaf.timeit.active.{id(self)}", default=None
        )
        self._lock = threading.RLock()

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        with self._lock:
            return len(self._samples[self.default_clock])

    @property
    def default_clock(self) -> str:
        """Clock used for the timer's sample count."""
        return self.clocks[0]

    @property
    def timings(self) -> Mapping[str, tuple[float, ...]]:
        """Return an immutable snapshot of recorded durations."""
        with self._lock:
            snapshot = {name: tuple(values) for name, values in self._samples.items()}
        return MappingProxyType(snapshot)

    def start(self) -> None:
        """Start an interval in the current thread or async context."""
        if self._active.get() is not None:
            msg = "timer is already active in this context"
            raise RuntimeError(msg)
        self._active.set({name: clock(name) for name in self.clocks})

    def cancel(self) -> None:
        """Discard the active interval without recording it."""
        if self._active.get() is None:
            msg = "timer is not active in this context"
            raise RuntimeError(msg)
        self._active.set(None)

    def stop(self) -> Record:
        """Stop the active interval, record it, and emit a record event."""
        started = self._active.get()
        if started is None:
            msg = "timer is not active in this context"
            raise RuntimeError(msg)
        stopped = {name: clock(name) for name in self.clocks}
        self._active.set(None)
        durations = {name: stopped[name] - started[name] for name in self.clocks}
        with self._lock:
            for name, value in durations.items():
                self._samples[name].append(value)
            index = len(self._samples[self.default_clock])
        record = Record(
            self.label or "Timer", index, MappingProxyType(durations.copy())
        )
        if self.emitter is not None:
            self.emitter(record)
        return record

    def clear(self) -> None:
        """Remove every recorded sample.

        Raises:
            RuntimeError: If the timer is active in the current context.
        """
        if self._active.get() is not None:
            msg = "cannot clear an active timer"
            raise RuntimeError(msg)
        with self._lock:
            for values in self._samples.values():
                values.clear()

    def elapsed(self, clock_name: ClockName | None = None) -> float:
        """Read elapsed time for the active interval without stopping it."""
        started = self._active.get()
        if started is None:
            msg = "timer is not active in this context"
            raise RuntimeError(msg)
        selected = clock_name or self.default_clock
        return clock(selected) - started[selected]

    def summary(self) -> Summary:
        """Build an immutable statistical snapshot."""
        with self._lock:
            samples = {name: tuple(values) for name, values in self._samples.items()}
        count = len(samples[self.default_clock])
        aggregates: dict[str, Statistics] = {}
        for name, values in samples.items():
            if not values:
                continue
            aggregates[name] = Statistics(
                total=sum(values),
                mean=statistics.mean(values),
                minimum=min(values),
                maximum=max(values),
                stdev=statistics.stdev(values) if len(values) > 1 else 0.0,
            )
        return Summary(
            self.label or "Timer", count, MappingProxyType(aggregates.copy())
        )

    def finish(self) -> Summary:
        """Emit and return the current summary."""
        event = self.summary()
        if self.emitter is not None:
            self.emitter(event)
        return event

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.stop()

    @overload
    def __call__[**P, R](self, target: Callable[P, R], /) -> Callable[P, R]: ...

    @overload
    def __call__[T](self, target: Iterable[T], /) -> TimedIterable[T]: ...

    def __call__(self, target: Callable[..., Any] | Iterable[Any], /) -> Any:
        if callable(target):
            return self._decorate(target)
        return TimedIterable(target, self)

    def _decorate(self, func: Callable[..., Any]) -> Callable[..., Any]:
        if self.label is None:
            name = getattr(func, "__qualname__", type(func).__qualname__)
            self.label = f"{name}()"
        if inspect.isasyncgenfunction(func):

            @functools.wraps(func)
            async def async_generator_wrapper(*args: Any, **kwargs: Any) -> Any:
                # An async-generator body begins on first iteration, so this
                # interval covers execution rather than construction.
                self.start()
                try:
                    async for item in func(*args, **kwargs):
                        yield item
                finally:
                    self.stop()

            wrapped = async_generator_wrapper
        elif inspect.isgeneratorfunction(func):

            @functools.wraps(func)
            def generator_wrapper(*args: Any, **kwargs: Any) -> Any:
                # ``yield from`` preserves generator send/throw/close behavior
                # while keeping one interval for this generator invocation.
                self.start()
                try:
                    yield from func(*args, **kwargs)
                finally:
                    self.stop()

            wrapped = generator_wrapper
        elif inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                self.start()
                try:
                    return await func(*args, **kwargs)
                finally:
                    self.stop()

            wrapped = async_wrapper
        else:

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                self.start()
                try:
                    return func(*args, **kwargs)
                finally:
                    self.stop()

            wrapped = wrapper
        timer_attribute = "__liblaf_timeit_timer__"
        setattr(wrapped, timer_attribute, self)
        return wrapped


class TimedIterable[T]:
    """Iterable proxy that times each request for the next item."""

    def __init__(self, wrapped: Iterable[T], timer_: Timer) -> None:
        self._wrapped = wrapped
        self.__liblaf_timeit_timer__ = timer_
        if timer_.label is None:
            timer_.label = "Iterable"

    def __iter__(self) -> Iterator[T]:
        iterator = iter(self._wrapped)
        while True:
            self.__liblaf_timeit_timer__.start()
            try:
                item = next(iterator)
            except StopIteration:
                self.__liblaf_timeit_timer__.cancel()
                break
            except BaseException:
                self.__liblaf_timeit_timer__.cancel()
                raise
            self.__liblaf_timeit_timer__.stop()
            yield item
        self.__liblaf_timeit_timer__.finish()


@overload
def timer(
    *,
    label: str | None = None,
    clocks: Sequence[ClockName] = ("perf",),
    emitter: Emitter | None = ...,
) -> Timer: ...


@overload
def timer[**P, R](
    target: Callable[P, R],
    /,
    *,
    label: str | None = None,
    clocks: Sequence[ClockName] = ("perf",),
    emitter: Emitter | None = ...,
) -> Callable[P, R]: ...


@overload
def timer[T](
    target: Iterable[T],
    /,
    *,
    label: str | None = None,
    clocks: Sequence[ClockName] = ("perf",),
    emitter: Emitter | None = ...,
) -> TimedIterable[T]: ...


def timer(
    target: Callable[..., Any] | Iterable[Any] | None = None,
    /,
    *,
    label: str | None = None,
    clocks: Sequence[ClockName] = ("perf",),
    emitter: Emitter | _DefaultEmitter | None = _DEFAULT_EMITTER,
) -> Any:
    """Create a timer or immediately wrap a callable or iterable.

    Passing no explicit emitter selects the standard logging adapter. Pass
    ``emitter=lambda event: ...`` for another destination or ``None`` to disable
    output. Decorated generator and async-generator functions record one
    interval for each consumed generator invocation; constructing the generator
    object alone does not emit an event.

    Args:
        target: Callable or iterable to wrap. Omit it to obtain a [`Timer`][liblaf.timeit.Timer].
        label: Event label.
        clocks: Registered clocks to measure.
        emitter: Event destination; `None` disables event emission.

    Returns:
        A timer, a wrapped callable, or a timed iterable matching `target`.
    """
    resolved_emitter: Emitter | None = (
        _default_emitter() if isinstance(emitter, _DefaultEmitter) else emitter
    )
    instance = Timer(label=label, clocks=clocks, emitter=resolved_emitter)
    if target is None:
        return instance
    return instance(target)


def get_timer(wrapper: Any) -> Timer:
    """Return the timer attached by [`timer`][liblaf.timeit.timer].

    Raises:
        TypeError: If the object is not a `liblaf.timeit` wrapper.
    """
    try:
        value = wrapper.__liblaf_timeit_timer__
    except AttributeError as error:
        msg = "object has no liblaf.timeit timer"
        raise TypeError(msg) from error
    if not isinstance(value, Timer):
        msg = "attached timer has an invalid type"
        raise TypeError(msg)
    return value
