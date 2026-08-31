"""Measure work and emit structured timing events through Python logging.

[`timer`][liblaf.timeit.timer] works as a context manager, decorator, or
iterable adapter. It never repaints a terminal and has no runtime dependency on
other `liblaf` packages.

Examples:
    >>> isinstance(timer(emitter=None), Timer)
    True
"""

from ._clock import CLOCKS, Clock, ClockName, clock, register_clock
from ._logging import LoggingEmitter, format_event, log_to
from ._timer import (
    Emitter,
    Record,
    Statistics,
    Summary,
    TimedIterable,
    Timer,
    TimerEvent,
    get_timer,
    timer,
)
from ._version import __commit_id__, __version__, __version_tuple__

__all__ = [
    "CLOCKS",
    "Clock",
    "ClockName",
    "Emitter",
    "LoggingEmitter",
    "Record",
    "Statistics",
    "Summary",
    "TimedIterable",
    "Timer",
    "TimerEvent",
    "__commit_id__",
    "__version__",
    "__version_tuple__",
    "clock",
    "format_event",
    "get_timer",
    "log_to",
    "register_clock",
    "timer",
]
