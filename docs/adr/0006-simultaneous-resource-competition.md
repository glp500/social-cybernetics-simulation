# ADR 0006: Use Simultaneous Resource Competition

## Status

Accepted — 2026-08-28

## Context

Single occupancy introduces movement conflicts, while sequential harvesting makes activation order an
unacknowledged allocation institution.

## Decision

Use unlimited cell occupancy. Collect all harvest requests before mutation and allocate scarce stock
proportionally to requested quantities. Resolve movement without collision priority.

## Alternatives considered

- **Classic single-occupancy Sugarscape:** deferred as a robustness variant.
- **Random first-come harvesting:** deferred as an explicit competition treatment.

## Consequences

The control isolates material scarcity from movement collisions and scheduler luck. Later ownership,
priority, market, or need rules replace the explicit resolver rather than agent activation order.

