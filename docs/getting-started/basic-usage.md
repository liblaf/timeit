# Basic usage

Create a timer for a context block. Pass `emitter=None` to collect samples
without logging them.

```python
from liblaf.timeit import Timer

measured = Timer(emitter=None)
with measured:
    pass

assert measured.summary().count == 1
```

`timer()` can also decorate a callable or wrap an iterable:

```python
from liblaf.timeit import get_timer, timer


@timer(emitter=None)
def parse() -> int:
    return 1


assert parse() == 1
assert get_timer(parse).summary().count == 1
```
