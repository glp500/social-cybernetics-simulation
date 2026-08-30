# Project 1 Validation and Freeze Gates

## Status table

| Gate | Status | Existing evidence | Work required to freeze |
| --- | --- | --- | --- |
| specification | frozen | authoritative scheduler, state, shock, RNG, experiment, and outcome contracts agree with source commit `4ae3859` | reopen only through a versioned scientific change |
| literature | frozen | four paired Project 1 notes classify support, counterevidence/boundaries, licensed use, prohibited use, and project choices | empirical calibration remains a future study |
| verification | frozen | 259 tests, 90.80% branch-aware coverage, Ruff, Pyright, exact baseline regression, lock consistency, clean lock install, and isolated browser stepping passed | rerun after any executable or environment change |
| sensitivity | frozen | 600/600 Morris runs completed; scope-specific elementary effects and uncertainty were inspected | do not interpret the broad screen as calibrated effect estimation |
| experiment | frozen | the preregistered P1-A–E design completed 140/140 runs with a validated recursive batch bundle | archive externally before publication |
| analysis | frozen | artifact-only analysis reconstructed and cross-validated 140 JSON/Parquet outcome rows | add inferential intervals only through preregistration |
| interpretation | frozen | every headline comparison has mechanical, computational, disciplinary, alternative, missing-mechanism, and prohibited-conclusion entries | reopen with new evidence or mechanisms |

## Frozen evidence registry

| Evidence | Identity / result |
| --- | --- |
| source state used for execution | Git commit `4ae3859364fe2abc995b858ed779519b8336d7e2` |
| canonical batch | `results/project1-batch`; 140 completed, 0 failed; manifest SHA-256 `9355cbb919f748446a0e6eab3c65c9104c151c5642ca7ca614a8865431a17197` |
| canonical analysis | `results/project1-analysis`; 140 outcome rows; manifest SHA-256 `773f07fcb61d3f9616666e514e0a67c8c8299bfea3f03126dd11a0c28bab983a` |
| full outcome JSON | SHA-256 `eac312c6a160c06f278e7ff4064b4a305dded9691061f6f25ac194e477aa7ebc` |
| typed outcome Parquet | SHA-256 `b95081c50f06e65f064759e8206df3815370453c673d0862bad88e02dd5ca1b9` |
| Morris sensitivity batch | `results/project1-sensitivity`; 600 completed, 0 failed; manifest SHA-256 `6cb02a3aad037e073288903316d5788d048f6ca21607b370d39aa0613c6163e0` |
| browser evidence | `docs/solara-v0.2.png`; SHA-256 `8eb393bf3cf6786c38f783aba4048f11e87268ae47c8bb9defe512922a302ad7` |

Large bundles remain in ignored local `results/` storage. Their hashes identify the reviewed
evidence and the commands below regenerate it, but no external archive or DOI is claimed.

## Exact environment and commands

The normal and clean-lock checks used Linux-64, Python 3.12.14, Mesa 3.5.1, NumPy 2.5.2, Pydantic
2.13.5, PyArrow 25.0.0, netCDF4 1.7.4, SALib 1.5.2, pytest 9.1.1, Ruff 0.16.5, and Pyright 1.1.411.

```bash
scs project1-run --spec configs/project-1.yml --output results/project1-batch
scs project1-analyze --spec configs/project-1.yml \
  --batch results/project1-batch --output results/project1-analysis
scs sensitivity --spec configs/sensitivity-v0.2.yml --output results/project1-sensitivity
just check
just browser-check
conda-lock install --prefix /tmp/<fresh-prefix> conda-lock.yml
```

The clean prefix installed the repository editable with `--no-deps --no-build-isolation` and passed
the baseline byte regression plus Project 1 execution, aggregate-analysis, and artifact-reader tests.

## Sensitivity interpretation

The scope-stratified Morris screen averaged the three model-seed outcomes at each sampled point and
used the declared four-level design. Event probability had the largest `mu*` for harvest, unmet need,
alive count, and final resources in independent and system scopes. For correlated shocks, event
probability, spread probability, and stock-loss fraction were the leading harvest/unmet-need factors.
Large `sigma` values and confidence widths indicate interactions and limited ranking precision. These
are screening results over project controls, not empirical elasticities or a global variance
decomposition.

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
