# Implementation Plan: Stochastic Ecological Baseline v0.2

## Overview

Version 0.1 is implemented and verified. Version 0.2 asks how much mortality and inequality can arise
from ecological heterogeneity and shocks alone, before information capabilities, learning, networks,
or institutions enter the executable model.

The phase adds mechanisms in causal and dependency order. Every stochastic function receives an
explicit generator derived from the permanent run-seed registry. Version 0.1 configurations and the
canonical baseline summary remain supported. The registry migration intentionally rebaselines any
v0.1 trajectory that actually invokes stochastic policy movement.

## Confirmed scientific and architecture decisions

- Heterogeneous landscapes are explicit capacity and initial-stock matrices in configuration. This
  makes experimental fixtures inspectable and avoids hiding a second random process in initialization.
- Shock-enabled configurations explicitly declare three damage fractions and a finite recovery
  duration. Correlated configurations also declare spread probability and outward-round limit.
- Effective capacity and regeneration recover linearly on cell-local clocks. Current stock may
  temporarily exceed effective capacity and relaxes toward it while remaining below baseline capacity.
- Independent, concurrent correlated-wavefront, and system shocks use scope-specific Bernoulli
  semantics. Simultaneous hits compound and restart recovery once per cell.
- Immutable event snapshots, exposure records, and cell-damage applications provide normalized
  evidence without double-counting.
- Stable recorded RNG namespaces isolate policy `(1,)` from shock initiation `(2, 1)`, location
  `(2, 2)`, and propagation `(2, 3)`.
- Persistent output is opt-in. The implemented bundle contains normalized configuration, software and
  RNG provenance, schema-versioned Parquet tables, the JSON summary, and complete streamed NetCDF
  spatial history.
- Batch execution is deterministic and sequential first. Parallel execution is permitted only after
  record ordering and failure semantics are fixed.
- Sensitivity designs operate on declared parameter paths and ranges; they never mutate an opaque
  model object or bypass configuration validation.

## Dependency order

### Phase A — Documentation and ecological contracts

1. Reconcile canonical documentation and add the v0.2 ecological-variants ADR.
2. Extend configuration with backward-compatible schema and discriminated landscape/shock variants.
3. Build validated resource arrays from uniform or explicit landscape configuration.

### Checkpoint A

- v0.1 baseline validation and byte-for-byte CLI regression still pass.
- Explicit matrices reject shape, finiteness, negativity, and stock-above-capacity errors.
- Domain code remains independent of Pydantic and Mesa.

### Phase B — Pure shock mechanisms

4. Add a mechanism literature note and relevance statement for ecological shock geometry.
5. Reconcile the approved recoverable-shock design and RNG registry.
6. Define immutable shock-result evidence required by the selected design.
7. Implement the selected independent, correlated, and system shock functions with explicit RNG input.
8. Add property tests for bounds, accounting, reproducibility, and spatial masks.

### Checkpoint B

- Shock removal equals the difference between pre/post resource totals within tolerance.
- Identical seed and inputs reproduce stock and event evidence.
- Zero probability or zero severity is observationally equivalent to the no-shock control.

### Phase C — Runtime integration and records

9. Initialize Mesa property layers from validated landscape arrays.
10. Dispatch the configured shock during the existing shock stage and append event evidence.
11. Add v0.2 fixed-seed integration and stage-order regression fixtures.

### Checkpoint C

- The ODD+D scheduler still matches `STAGE_ORDER` exactly.
- The canonical v0.1 baseline summary remains byte-identical; stochastic v0.1 trajectories use the
  new `(1,)` policy stream and are intentionally incompatible with pre-registry fixtures.
- Activation iteration order cannot change ecological shock draws or contested allocation.

### Phase D — Persistent run bundles

12. Define normalized provenance and table schemas independent of the visualization.
13. Serialize model, cohort, and event records to a validated fail-closed Parquet bundle.
14. Add `scs run --output` with fail-closed destination and invariant behavior.
15. Stream tick zero and every completed tick to staged NetCDF with bounded memory.

### Checkpoint D

- A bundle round-trips with exact row counts, schema versions, normalized configuration, seed, and
  package versions.
- Existing destinations are never overwritten implicitly.
- Running without `--output` preserves the v0.1 JSON-only behavior.

Tasks 12–15 are implemented. The bundle contract is complete before batch indexes begin depending on
it.

### Phase E — Batch and sensitivity workflows

16. Add deterministic sequential batch execution with per-run directories and an aggregate index.
16a. Simplify batch validation into named schema, index, and child-bundle checks without changing
    accepted artifacts, error ordering, or publication behavior.
17a. Add paired sensitivity-method evidence and confirm the screening method, shock-scope treatment,
     stochastic seed/replication policy, factor ranges, and run budget through decision rounds.
17b. Add declared parameter-range validation and generate the selected seeded sensitivity design as
     an ordered batch specification without bypassing `SimulationConfig`.
18. Add small verification experiments and analysis smoke tests.

### Checkpoint E

- Batch reruns produce identical indexes and run bundles.
- One failed run is reported without corrupting completed bundles.
- Sensitivity samples and outputs retain raw continuous outcomes and configuration provenance.

Task 16 is implemented. Ordered YAML specifications resolve one validated base plus explicit
seed-bearing overrides; complete attempts publish equivalent JSON/Parquet indexes and successful
child bundles atomically. Per-run failures are retained without stopping later runs. Sensitivity and
verification work depend on this stable batch contract.

Task 16a is complete. Batch validation now reads as named root, manifest, artifact, provenance,
JSON-index, Parquet-index, count, and child-bundle checks. Public schemas and failure ordering are
unchanged; the existing tests pass without modification and focused C901 reports no batch violations.

Task 17a is complete. The accepted design uses separate independent, correlated, and system Morris
screens, four levels, 100 candidate and 10 locally optimized selected trajectories per scope, design
seed 42, paired model seeds 101/202/303, explicit broad ranges, and a 600-run fail-closed cap. The
literature note records the stochastic-model limitations and identifies every number as a project
choice rather than calibration.

Task 17b is complete. `scs sensitivity` validates explicit numeric shock paths and ranges, rejects
inactive/categorical fields and inexact integer grids, generates stable point/replicate ordering from
the recorded design seed, validates all 600 realized configurations, and delegates execution and
publication to the existing batch boundary.

### Phase F — Release reconciliation

19. Update visualization for heterogeneous capacity and shock debugging without alternate transitions.
20. Reconcile specification, assumptions, architecture, roadmap, dashboard, README, and experiment log.
21. Repeat clean lock installation, `just check`, browser verification, and exact regression checks.

## Task sizing and likely files

Each numbered task is limited to five files. Focused tasks normally touch one production module, its
tests, and at most three configuration/documentation files. If implementation reveals a task needs
more than five files, split it before editing.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| RNG registry changes stochastic v0.1 trajectories | accepted | rebaseline fixtures once, retain the registry permanently, and record the migration in ADR 0004 |
| array orientation differs between YAML, NumPy, and Mesa | high | specify `(x, y)` indexing and test asymmetric fixtures |
| shock draws depend on agent activation | high | draw once in model stage through a pure domain function |
| persistence leaks framework objects | medium | serialize immutable domain records and normalized mappings |
| partial bundle writes look complete | high | stage output and publish only after validation succeeds |
| sensitivity scope expands prematurely | medium | begin with declared scalar paths and a small seeded design |
| output validation becomes difficult to review | medium | keep validators as named sequential checks and monitor focused C901 complexity |

## Open design checkpoints

- Confirm whether long batch runs should add process-level parallelism after deterministic sequential
  semantics and the 600-run screen are verified.
- Select the narrowed factors, replication count, and inferential method only after the screening
  outputs and seed-stratified variability are inspected.
