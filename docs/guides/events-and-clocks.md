# Events and clocks

The default clock is `perf`, but a timer may collect several registered clocks
for each interval.

```python
from liblaf.timeit import Timer

timer = Timer(clocks=("perf", "process"), emitter=None)
with timer:
    pass
```

Use `register_clock(name, func)` for a project-specific zero-argument clock.
Custom emitters receive ordinary immutable `Record` and `Summary` values, so
they can serialize or aggregate events without a logging-framework dependency.
