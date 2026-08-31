"""Clock registry used by timers."""

import os
import time
from collections.abc import Callable

type Clock = Callable[[], float]
type ClockName = str

CLOCKS: dict[str, Clock] = {
    "monotonic": time.monotonic,
    "perf": time.perf_counter,
    "process": time.process_time,
    "thread": time.thread_time,
    "time": time.time,
    "children-system": lambda: os.times().children_system,
    "children-user": lambda: os.times().children_user,
    "elapsed": lambda: os.times().elapsed,
    "system": lambda: os.times().system,
    "user": lambda: os.times().user,
}


def register_clock(name: str, func: Clock, *, replace: bool = False) -> None:
    """Register a clock.

    Args:
        name: Public clock name.
        func: Zero-argument function returning monotonically comparable values.
        replace: Allow replacing an existing registration.

    Raises:
        ValueError: If ``name`` is already registered and ``replace`` is false.
    """
    if name in CLOCKS and not replace:
        msg = f"clock {name!r} is already registered"
        raise ValueError(msg)
    CLOCKS[name] = func


def clock(name: ClockName = "perf") -> float:
    """Read a registered clock.

    Args:
        name: Registered clock name; `perf` is the default.

    Returns:
        The clock's current numeric instant.
    """
    return CLOCKS[name]()
