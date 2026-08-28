# ADR 0004: Use Model-owned Randomness

## Status

Accepted — 2026-08-28

## Context

Reproducibility fails when libraries or mechanisms draw from unrelated global generators.

## Decision

One configured seed initialises the runtime. Every stochastic scientific function receives the
model-owned NumPy generator explicitly. Direct calls to global `numpy.random` or Python `random` are
forbidden in domain and runtime scientific code.

## Alternatives considered

- **Module-level seeds:** rejected because import and call order affect results.
- **Independent unrecorded streams:** rejected because provenance would be incomplete.

## Consequences

Fixed configuration and seed produce a fixed trajectory. Future parallel runs must derive and record
child seeds explicitly rather than inheriting process-global state.

