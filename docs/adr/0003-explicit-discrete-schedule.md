# ADR 0003: Use an Explicit Discrete Schedule

## Status

Accepted — 2026-08-28

## Context

Changing whether resources regenerate, agents observe, actions resolve, or metabolism occurs first can
change scientific outcomes. A generic agent `step()` would hide that causal order.

## Decision

Use synchronous discrete ticks orchestrated by a readable model-level method. The schedule is
regeneration, shock, observation, belief, intent, institutional gate, physical resolution, metabolism,
mortality, and measurement. Tests capture the stage trace.

## Alternatives considered

- **Sequential agent steps:** rejected because activation order would mix observation, competition,
  and mutation.
- **Continuous/event time:** deferred until a research question requires it.

## Consequences

Intermediate values are stored until their stage resolves. Scheduler changes are scientific changes
that require specification and regression updates.

