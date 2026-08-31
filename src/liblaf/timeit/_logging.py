"""Standard-library logging adapter for timer events."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, TypeGuard

from ._format import format_duration


class _Statistics(Protocol):
    @property
    def total(self) -> float: ...

    @property
    def mean(self) -> float: ...

    @property
    def minimum(self) -> float: ...

    @property
    def maximum(self) -> float: ...

    @property
    def stdev(self) -> float: ...


class _RecordEvent(Protocol):
    @property
    def label(self) -> str: ...

    @property
    def index(self) -> int: ...

    @property
    def durations(self) -> Mapping[str, float]: ...


class _SummaryEvent(Protocol):
    @property
    def label(self) -> str: ...

    @property
    def count(self) -> int: ...

    @property
    def statistics(self) -> Mapping[str, _Statistics]: ...


type TimerEvent = _RecordEvent | _SummaryEvent


def _is_record(event: TimerEvent) -> TypeGuard[_RecordEvent]:
    return hasattr(event, "durations")


def _is_summary(event: TimerEvent) -> TypeGuard[_SummaryEvent]:
    return not _is_record(event)


def format_event(event: TimerEvent) -> str:
    """Render a timer event as stable plain text.

    Examples:
        >>> from liblaf.timeit import Record
        >>> format_event(Record("query", 1, {"perf": 0.001}))
        'query #1 > perf: 1 ms'
    """
    if _is_record(event):
        values = ", ".join(
            f"{name}: {format_duration(value)}"
            for name, value in event.durations.items()
        )
        return f"{event.label} #{event.index} > {values}"

    assert _is_summary(event)
    header = f"{event.label} (count: {event.count})"
    if not event.statistics:
        return header
    lines = []
    for name, stats in event.statistics.items():
        lines.append(
            f"{name} > total: {format_duration(stats.total)}, "
            f"mean: {format_duration(stats.mean)}, "
            f"min: {format_duration(stats.minimum)}, "
            f"max: {format_duration(stats.maximum)}, "
            f"stdev: {format_duration(stats.stdev)}"
        )
    return f"{header} " + "\n".join(lines)


@dataclass(frozen=True, slots=True)
class LoggingEmitter:
    """Emit timer records and summaries through a standard-library logger.

    The emitted `LogRecord` contains the original event as `timer_event`.
    """

    logger: logging.Logger
    record_level: int = logging.DEBUG
    summary_level: int = logging.INFO

    def __call__(self, event: TimerEvent) -> None:
        level = self.record_level if _is_record(event) else self.summary_level
        self.logger.log(level, "%s", format_event(event), extra={"timer_event": event})


def log_to(
    logger: logging.Logger | str | None = None,
    *,
    record_level: int = logging.DEBUG,
    summary_level: int = logging.INFO,
) -> LoggingEmitter:
    """Build an emitter for a logger without a `liblaf.logging` dependency.

    Args:
        logger: Logger instance or name. Defaults to `liblaf.timeit`.
        record_level: Logging level for interval records.
        summary_level: Logging level for summaries.
    """
    if logger is None:
        resolved = logging.getLogger("liblaf.timeit")
    elif isinstance(logger, str):
        resolved = logging.getLogger(logger)
    else:
        resolved = logger
    return LoggingEmitter(resolved, record_level, summary_level)
