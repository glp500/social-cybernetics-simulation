# Project 1 Validation and Freeze Gates

## Status table

| Gate | Status | Existing evidence | Work required to freeze |
| --- | --- | --- | --- |
| specification | candidate | scheduler, shock, RNG, evidence, and experiment contracts are written | reconcile after implementation and mark equations authoritative |
| literature | candidate | ecology, disturbance, mobility, distribution, persistence, and subsistence sources classified | complete paired notes and counterevidence review |
| verification | inherited candidate | V0–V4, fixed trajectories, invariants, CLI, persistence, and browser checks passed pre-refactor | rerun under `Study01Config` and new record schema |
| sensitivity | inherited candidate | scope-stratified Morris design is validated | migrate schema, execute/inspect evidence, and record parameter influence limits |
| experiment | open | P1-A–E design is preregistered | execute 140 runs and validate all bundles |
| analysis | open | equations and edge cases are specified | implement, test, version, and freeze artifact-only analysis |
| interpretation | open | programme protocol and Project 1 template exist | complete result tables and prohibit unsupported claims |

No inherited gate is automatically frozen. The refactor changes configuration, evidence, and analysis
contracts and therefore requires explicit reconciliation.

## Mechanism verification ladder

- **V0:** no agents; uniform resources converge to capacity over 1,000 ticks.
- **V1:** one agent; fixed-seed trajectory is fully understandable and exact.
- **V2:** zero-resource scarcity produces shortfall and mortality with death retained in records.
- **V3:** two agents contest one productive cell proportionally and independently of iteration order.
- **V4:** ten agents use a deterministic heterogeneous fixture with exact stage ordering.
- **V5:** each shock scope has reproducible initiation/damage evidence; sham shocks do not shift policy
  draws.
- **V6:** transition evidence reconstructs every active agent-tick and agrees with cohort/event totals.

## Invariants

- resource stock, capacity, regeneration, energy, harvest, and shortfall are finite and non-negative;
- stock never exceeds baseline capacity;
- harvest removes exactly the material allocated and never depends on agent iteration order;
- shock damage is applied once per cell-tick after all contributing events are normalized;
- recovery reaches baseline exactly on its active cell-local clock absent a repeated hit;
- every active agent produces one decision and one transition record per tick;
- dead agents leave Mesa activation but remain in cohort records with zero energy;
- complete spatial history contains tick zero and every completed tick;
- all scientific randomness comes from registered model-owned streams;
- analysis reads immutable records/artifacts and cannot mutate or step the model.

## Regression requirements

- equivalent legacy and Study 01 configs produce identical normalized mechanism inputs;
- the canonical baseline JSON summary remains byte-for-byte unchanged;
- pre-refactor baseline and ecological complete trajectories remain equal aside from intentionally
  migrated schema fields;
- same configuration/seed reproduces all records and artifacts;
- order permutations do not change contested allocations or aggregate metrics;
- run, batch, experiment, and analysis destinations fail closed and are never overwritten.

## Statistical verification

Seeds are experimental blocks, not parameter levels. Agent-ticks and cells are observations within a
run, not independent replicates. Analysis must retain undefined metrics instead of replacing them with
convenient zeros unless zero is mathematically defined.

## Release checks

Project 1 requires focused/unit/property/integration tests, at least 90% branch-aware coverage, Ruff,
Pyright standard, dependency/lock synchronization, clean Conda-lock installation, isolated browser
stepping, exact scheduler/spec trace agreement, and validation of every frozen artifact.
