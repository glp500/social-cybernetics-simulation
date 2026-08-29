# ADR 0007: Represent v0.2 ecology with explicit landscapes and recoverable shock events

## Status

Accepted

## Date

2026-08-29

## Context

Version 0.2 must estimate how much inequality and mortality arise from ecology alone. The extension
needs heterogeneous starting conditions and distinct independent, spatially correlated, and
system-wide shocks without coupling equations to Mesa. It must also define how reproducibility
evolves when one random stream becomes a permanent mechanism registry.

Generating landscapes implicitly inside model construction would hide realized scientific inputs.
Encoding shocks as agent actions would also contaminate activation order and the causal separation
between environment and observation.

## Decision

Represent heterogeneous landscapes as explicit capacity and initial-stock matrices in validated
configuration. Matrices use NumPy/Mesa `(x, y)` indexing and are saved verbatim in experiment
provenance.

Represent shock effects as three independent fractions: immediate stock loss, temporary effective-
capacity loss, and temporary effective-regeneration suppression. Effective ecological state recovers
linearly to immutable baseline values on a cell-local finite clock. Hits compound and restart that
clock. Stock may exceed effective capacity temporarily but remains bounded by baseline capacity and
relaxes toward the effective target.

Use scope-specific Bernoulli variants: independent cell events, concurrent correlated events that
spread as synchronous stochastic Von Neumann wavefronts, and system-wide events. Correlated spread
uses independent per-edge attempts and an explicit maximum number of outward rounds.

Resolve simultaneous hits once per cell and retain normalized immutable evidence: per-tick event
snapshots, event-cell exposures, and one cell-damage application linked to all contributing events.
Event IDs are run-local monotonic integers.

Derive permanent model-owned NumPy substreams with `SeedSequence(run_seed, spawn_key=...)`: policy
stream `(1,)`, shock-initiation `(2, 1)`, shock-location `(2, 2)`, and shock-transmission `(2, 3)`.
Record the registry and bit-generator identity in provenance.

## Alternatives considered

### Generate a random capacity field inside every model constructor

Rejected because the realized landscape would be implicit, harder to compare across treatments, and
easy to entangle with shock or agent random draws.

### Additive shocks

Rejected for v0.2 because truncation gives the same absolute loss different meanings across unequal
cells.

### Fixed-radius correlated masks

Rejected for v0.2 in favor of a connected stochastic wavefront with explicit propagation evidence.

### Clamp stock to damaged effective capacity

Rejected because it would make capacity damage create an additional immediate stock loss and weaken
the separation of the three mechanisms.

### Permanent capacity damage and non-linear recovery

Deferred. They are materially different resilience mechanisms and require new discriminated variants.

## Consequences

- The canonical v0.1 baseline summary remains byte-identical because it makes no movement draw.
- Any v0.1 trajectory that invokes stochastic policy movement is intentionally rebaselined from the
  former unnamespaced generator to permanent policy stream `(1,)`.
- Experiments can reuse one realized landscape across shock treatments.
- Array orientation, wavefront topology, recovery clocks, and simultaneous hits require asymmetric
  integration fixtures.
- Persistent outputs must include normalized configuration and realized landscape matrices.
- Sham shocks can verify record plumbing without shifting policy randomness or physical state.
- More realistic hazard and recovery processes require new discriminated variants and specification
  updates.
