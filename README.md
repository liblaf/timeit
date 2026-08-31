<div align="center" markdown>

![Timeit](https://socialify.git.ci/liblaf/timeit/image?description=1&forks=1&issues=1&language=1&name=1&owner=1&pattern=Transparent&pulls=1&stargazers=1&theme=Auto)

[![Python](https://img.shields.io/pypi/pyversions/liblaf-timeit?logo=python)](https://pypi.org/project/liblaf-timeit)
[![Test](https://github.com/liblaf/timeit/actions/workflows/python-test.yaml/badge.svg)](https://github.com/liblaf/timeit/actions/workflows/python-test.yaml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

`liblaf.timeit` measures contexts, callables, async callables, and iterables. It emits structured events through Python logging instead of writing to a terminal, and it has no dependency on the other liblaf presentation packages.

## Installation

```bash
uv add liblaf-timeit
```

## Usage

```python
from liblaf.timeit import get_timer, timer


@timer()
def build_index() -> None: ...


build_index()
get_timer(build_index).finish()
```

The same `timer()` factory is a context manager or an iterable adapter. Pass an `emitter` callback to route immutable record and summary events somewhere other than standard logging.

## Design

- Standard `logging` is the default output seam; `liblaf.logging` is optional.
- Active intervals are context-local, while completed samples are safe to aggregate across threads.
- Invalid nesting and unmatched `start()` / `stop()` calls fail immediately.

See [the domain context](https://github.com/liblaf/timeit/blob/main/CONTEXT.md) and [architecture decisions](https://github.com/liblaf/timeit/tree/main/docs/adr).

## Guides

The documentation covers [basic usage](https://liblaf.github.io/timeit/getting-started/basic-usage/),
[the timing model](https://liblaf.github.io/timeit/concepts/timing-model/),
and [events and clocks](https://liblaf.github.io/timeit/guides/events-and-clocks/).

## License

[MIT](https://github.com/liblaf/timeit/blob/main/LICENSE)
