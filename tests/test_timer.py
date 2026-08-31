import asyncio
import logging
from collections.abc import AsyncIterator, Generator, Iterator
from typing import cast

import pytest

from liblaf.timeit import Record, Summary, Timer, get_timer, register_clock, timer


class SequenceClock:
    def __init__(self, *values: float) -> None:
        self._values: Iterator[float] = iter(values)

    def __call__(self) -> float:
        return next(self._values)


def clock_name(name: str, *values: float) -> str:
    register_clock(name, SequenceClock(*values), replace=True)
    return name


def test_context_emits_record_and_summary() -> None:
    events: list[Record | Summary] = []
    name = clock_name("test-context", 1.0, 1.25)
    measured = Timer(label="step", clocks=(name,), emitter=events.append)

    with measured:
        pass
    summary = measured.finish()

    assert len(measured) == 1
    assert measured.timings[name] == pytest.approx((0.25,))
    assert events[0] == Record("step", 1, {name: 0.25})
    assert summary.count == 1
    assert summary.statistics[name].mean == pytest.approx(0.25)


def test_decorator_preserves_result_and_attaches_timer() -> None:
    name = clock_name("test-function", 2.0, 2.5)

    @timer(clocks=(name,), emitter=lambda _event: None)
    def add(left: int, right: int) -> int:
        return left + right

    assert add(2, 3) == 5
    measured = get_timer(add)
    assert (
        measured.label
        == "test_decorator_preserves_result_and_attaches_timer.<locals>.add()"
    )
    assert measured.timings[name] == pytest.approx((0.5,))


def test_async_decorator() -> None:
    name = clock_name("test-async", 4.0, 4.75)

    @timer(clocks=(name,), emitter=lambda _event: None)
    async def work() -> str:
        await asyncio.sleep(0)
        return "done"

    assert asyncio.run(work()) == "done"
    assert get_timer(work).timings[name] == pytest.approx((0.75,))


def test_generator_decorator_times_consumption_and_close() -> None:
    name = clock_name("test-generator", 1.0, 1.5)
    events: list[Record | Summary] = []

    @timer(clocks=(name,), emitter=events.append)
    def values() -> Generator[int, None, None]:
        yield 1

    generator = values()
    assert events == []
    assert next(generator) == 1
    generator.close()

    assert get_timer(values).timings[name] == pytest.approx((0.5,))
    assert isinstance(events[0], Record)


def test_generator_decorator_records_exception() -> None:
    name = clock_name("test-generator-error", 2.0, 2.25)
    events: list[Record | Summary] = []

    @timer(clocks=(name,), emitter=events.append)
    def fail() -> Iterator[int]:
        raise RuntimeError
        yield 1

    with pytest.raises(RuntimeError):
        next(fail())

    assert get_timer(fail).timings[name] == pytest.approx((0.25,))
    assert isinstance(events[0], Record)


def test_async_generator_decorator_times_consumption() -> None:
    name = clock_name("test-async-generator", 3.0, 3.5)
    events: list[Record | Summary] = []

    @timer(clocks=(name,), emitter=events.append)
    async def values() -> AsyncIterator[int]:
        yield 1

    async def consume() -> list[int]:
        generator = values()
        assert events == []
        return [item async for item in generator]

    assert asyncio.run(consume()) == [1]
    assert get_timer(values).timings[name] == pytest.approx((0.5,))
    assert isinstance(events[0], Record)


def test_iterable_times_next_not_consumer() -> None:
    name = clock_name(
        "test-iterable",
        0.0,
        0.1,
        10.0,
        10.2,
        20.0,
    )
    wrapped = timer([1, 2], clocks=(name,), emitter=lambda _event: None)

    assert list(wrapped) == [1, 2]
    assert get_timer(wrapped).timings[name] == pytest.approx((0.1, 0.2))


def test_invalid_state_fails_visibly() -> None:
    name = clock_name("test-state", 0.0)
    measured = Timer(clocks=(name,), emitter=None)

    with pytest.raises(RuntimeError, match="not active"):
        measured.stop()
    measured.start()
    with pytest.raises(RuntimeError, match="already active"):
        measured.start()


def test_default_emitter_uses_logging(caplog: pytest.LogCaptureFixture) -> None:
    name = clock_name("test-logging", 1.0, 1.001)
    caplog.set_level(logging.DEBUG, logger="liblaf.timeit")
    measured = timer(label="query", clocks=(name,))

    with measured:
        pass

    assert "query #1" in caplog.text
    event = cast("Record", caplog.records[0].__dict__["timer_event"])
    assert event.durations[name] == pytest.approx(0.001)


def test_factory_none_disables_emission() -> None:
    name = clock_name("test-disabled", 0.0, 1.0)
    measured = timer(clocks=(name,), emitter=None)

    with measured:
        pass

    assert len(measured) == 1
