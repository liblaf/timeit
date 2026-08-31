# Timing

This context describes reusable measurement of elapsed work and the events
produced from those measurements.

## Language

**Timer**:
The owner of a named series of timing records.
_Avoid_: Stopwatch, benchmark

**Interval**:
One bounded execution whose durations are measured together.
_Avoid_: Lap, span

**Record**:
The immutable durations produced by one interval.
_Avoid_: Result, sample set

**Summary**:
Immutable aggregate statistics over a timer's records.
_Avoid_: Report, totals

**Emitter**:
An injected destination for timing records and summaries.
_Avoid_: Printer, logger

**Clock**:
A named source of comparable numeric instants.
_Avoid_: Timer, metric

**Timed iterable**:
An iterable whose requests for successive values are measured as separate
intervals.
_Avoid_: Timed loop

**Decorated generator invocation**:
The execution lifetime from a generator's first iteration until exhaustion,
closure, or error.
_Avoid_: Generator construction
