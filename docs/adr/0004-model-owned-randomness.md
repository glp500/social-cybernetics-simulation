# ADR 0004: Use Model-owned Randomness

## Status

Accepted — 2026-08-28; amended 2026-08-29

## Context

Reproducibility fails when libraries or mechanisms draw from unrelated global generators.

## Decision

One configured seed initialises the runtime. Every stochastic scientific function receives an
explicit NumPy generator derived with `SeedSequence(run_seed, spawn_key=...)`. Permanent numeric keys
form a compatibility registry:

- policy and movement: `(1,)`;
- ecological event initiation: `(2, 1)`;
- ecological event location: `(2, 2)`;
- ecological frontier-edge transmission: `(2, 3)`.

The registry and bit-generator identity are recorded in run provenance. New mechanisms receive new
keys and cannot reuse or renumber an existing key. Direct calls to global `numpy.random` or Python
`random` are forbidden in domain and runtime scientific code.

The registry applies to every supported configuration schema. This intentionally migrates stochastic
version 0.1 policy trajectories from the former unnamespaced generator to `(1,)`. The canonical v0.1
baseline summary remains byte-identical only because that fixture never invokes a movement draw.

## Alternatives considered

- **Module-level seeds:** rejected because import and call order affect results.
- **Independent unrecorded streams:** rejected because provenance would be incomplete.
- **Keep the legacy v0.1 stream only for schema 0.1:** rejected because schema-specific RNG ownership
  would make mechanism code and comparisons harder to audit.

## Consequences

Fixed configuration, seed, registry, bit generator, and software environment produce a fixed
trajectory. Pre-registry stochastic fixtures are incompatible and must be rebaselined once. Future
parallel runs must derive and record child keys explicitly rather than inheriting process-global
state.
