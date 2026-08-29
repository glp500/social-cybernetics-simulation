# ADR 0011: Screen shock scopes with separate paired-seed Morris designs

## Status

Accepted

## Date

2026-08-30

## Context

Version 0.2 needs an economical global screen before focused verification experiments or expensive
variance decomposition. Independent, correlated, and system shocks share damage and recovery inputs,
but their hazards differ and only correlated events have propagation inputs. The executable model is
stochastic even when parameter values are fixed.

The design must remain reconstructable, validate every generated configuration, preserve raw
outcomes, and reuse the already verified sequential batch and fail-closed publication boundary.

## Decision

Run one ungrouped Morris design for each shock scope. Never encode `shock.kind` as a numeric factor.
Every scope varies event probability, the three damage fractions, and recovery duration. The
correlated scope additionally varies spread probability and maximum outward rounds.

Use four levels, 100 candidate trajectories, 10 selected trajectories, SALib's local optimization,
and design seed 42. Fraction and probability bounds are `[0, 1]`; recovery ticks use integer bounds
`[1, 10]`; correlated spread rounds use integer bounds `[0, 3]`. A generated integer factor must lie
exactly on an integer grid or validation fails rather than rounding it silently.

Repeat each design point with explicit model seeds `101`, `202`, and `303` in that order. These common
random numbers pair comparable conditions while the three independent seed blocks expose intrinsic
variation. Scope order is independent, correlated, then system; SALib point order is retained; seed
order is innermost. Stable run IDs encode scope, zero-padded point ordinal, and replicate ordinal.

The resulting design has 600 runs and a declared fail-closed run cap of 600. A sensitivity YAML names
one base configuration, the design controls, seed block, cap, and explicit per-scope fixed overrides
and factor ranges. Fixed overrides first resolve to a valid active shock configuration. Each sampled
point then resolves through `SimulationConfig`. Unknown, categorical, inactive, non-scalar, duplicate,
or invalid factor paths are rejected before model execution.

`scs sensitivity --spec ... --output ...` resolves the selected design directly into the existing
ordered batch contract and calls the existing batch executor. It does not publish a second bundle
type or maintain a separate run loop.

## Alternatives considered

### Screen only correlated shocks

Rejected because it would be cheaper but could not establish whether sensitivity rankings are robust
to the different spatial-correlation mechanisms.

### Treat shock kind as a categorical Morris factor

Rejected because Morris steps require numeric factors and the propagation inputs are inactive outside
the correlated variant.

### Use independent seeds at every parameter point

Rejected for the first screen because differences would be unnecessarily confounded by unrelated
random sequences. Independent seed blocks remain represented by the three explicit paired seeds.

### Begin with Sobol variance decomposition

Deferred until screening narrows the factor set and replication requirements are better understood.

### Write a separate sensitivity execution and persistence system

Rejected because it would duplicate configuration validation, failure semantics, provenance, and
atomic publication already provided by the batch boundary.

## Consequences

- Common factors can be ranked within each scope without inventing an ordinal shock-kind variable.
- Correlated-only propagation factors remain scientifically active in every generated configuration.
- The full first screen costs 600 runs and executes sequentially.
- Paired seeds improve comparisons but do not make the model deterministic or observations
  independent; later analysis must retain seed blocks.
- Exact numeric choices are transparent project controls, not empirical calibration.
