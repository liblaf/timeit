# ADR 0002: Keep active intervals context-local

- Status: accepted
- Date: 2026-08-31

## Context

A decorator may be invoked from several threads or async tasks while still accumulating one shared statistical series.

## Decision

Active start values are stored in a `ContextVar`; completed samples are appended under a lock. Starting the same timer recursively in one context fails immediately.

## Consequences

Concurrent independent calls are supported and aggregate into one timer. Accidental nested reuse is visible instead of corrupting measurements. Callers needing nested measurements use separate timers.
