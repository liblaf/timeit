# ADR 0001: Emit timing events instead of writing to a terminal

- Status: accepted
- Date: 2026-08-31

## Context

The Grapes timer printed through project-specific helpers. This package must work independently of `liblaf.logging` and must not write directly to stdout or stderr.

## Decision

`Timer` emits immutable `Record` and `Summary` values through one injected callback. Its default adapter creates standard-library log records. `liblaf.logging` can improve their presentation through normal logging configuration without becoming a hard dependency.

## Consequences

Alternative logging systems only need one callback adapter. Timing and presentation remain separately testable. Applications that have not configured logging may not see DEBUG record events, which follows normal Python logging behavior.
