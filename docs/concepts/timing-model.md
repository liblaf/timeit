# Timing model

A `Timer` owns a series of intervals. Each completed interval creates an
immutable `Record`; `summary()` aggregates completed records into an immutable
`Summary`. An emitter receives those events but does not own timer state.

Active intervals are context-local. Unmatched `stop()`, nesting in one context,
or `clear()` while active fails immediately. Completed samples use a lock and
`timings` returns a snapshot rather than the mutable internal lists.

Decorated generators and async generators begin timing on first iteration and
stop at exhaustion, closure, or error. `TimedIterable` measures each request
for the next value as a separate interval.
