# ADR 0003: Time decorated generators when they execute

- Status: accepted
- Date: 2026-08-31

## Context

A generator function returns an inert generator object. Timing its ordinary function call records construction time rather than the work performed during iteration.

## Decision

When a decorated function is a generator or async generator, start its timer at first iteration and stop it on exhaustion, closure, or error. One consumed generator invocation produces one `Record`. Direct iterable adapters retain their per-`next()` record model.

## Consequences

Constructing a decorated generator produces no event. Generator execution is measured honestly while the existing direct iterable API continues to distinguish producer time from consumer time.
