# Stochastic Ecological Baseline v0.2 Task List

## Completed prerequisite

- [x] Complete and verify deterministic material control v0.1.
  - Evidence: 56 tests, 97.02% branch-aware coverage, clean lock install, exact CLI regression, and
    isolated-browser verification recorded in `docs/experiment_log.md`.
- [x] Audit primary literature for the committed causal sequence using paired evidence.
  - Evidence: reviewed notes distinguish support, counterevidence/boundaries, justified commitments,
    and uncalibrated choices for learning, diffusion, networks, enforcement, governance, and regime
    discovery.
  - Files: `docs/literature/items/`, `docs/literature/literature_matrix.md`,
    `docs/modeling/mechanism_backlog.md`, `docs/experiment_log.md`.

## Phase A — Documentation and ecological contracts

- [x] Reconcile canonical documents for active v0.2 work and add ADR 0007.
  - Acceptance: scope, implemented landscape representation, proposed shock alternatives,
    compatibility, and exclusions agree.
  - Verify: documentation links resolve and no canonical page calls v0.2 merely future work.
  - Files: `docs/model_specification.md`, `docs/architecture.md`, `docs/assumptions.md`,
    `docs/adr/0007-stochastic-ecological-variants.md`, `docs/adr/README.md`.
- [x] Add backward-compatible v0.2 landscape configuration contracts.
  - Acceptance: v0.1 accepts only uniform/no-shock; v0.2 accepts implemented variants and rejects
    malformed matrices or unsupported kinds.
  - Verify: focused configuration tests pass; baseline JSON remains byte-identical.
  - Files: `src/social_cybernetics/config.py`, `tests/unit/test_config.py`,
    `tests/integration/test_cli.py`, `configs/baseline.yml`, `configs/ecology-v0.2.yml`.
- [x] Construct resource arrays from validated landscape configuration.
  - Acceptance: uniform and asymmetric explicit fixtures produce correctly oriented, independent
    float arrays satisfying `0 <= stock <= capacity`.
  - Verify: unit and property tests cover shape and bounds.
  - Files: `src/social_cybernetics/domain/ecology.py`, `src/social_cybernetics/domain/__init__.py`,
    `tests/unit/test_domain.py`, `tests/property/test_domain_properties.py`.

## Phase B — Pure shock mechanisms

- [x] Add the required shock-mechanism literature note and relevance statement.
  - Acceptance: primary evidence supports the abstraction or clearly identifies it as a controlled
    experimental simplification.
  - Verify: literature matrix and mechanism backlog link to the note and executable target.
  - Files: `docs/literature/items/<shock-note>.md`, `docs/literature/literature_matrix.md`,
    `docs/modeling/mechanism_backlog.md`.
- [x] Confirm shock semantics before adding a domain contract.
  - Acceptance: the user selects the loss model, event clock, correlated footprint, duration/recovery,
    and minimum event evidence after reviewing alternatives and tradeoffs.
  - Verify: specification, assumptions, ADR 0007, plan, and task wording agree with the selection.
  - Files: `docs/model_specification.md`, `docs/assumptions.md`,
    `docs/adr/0007-stochastic-ecological-variants.md`, `tasks/plan.md`, `tasks/todo.md`.
- [x] Define immutable shock-result evidence.
  - Acceptance: recovery state, event snapshots, event-cell exposures, and simultaneous cell-damage
    applications cannot alias mutable inputs or double-count physical changes.
  - Verify: contract isolation and invariant tests pass.
  - Files: `src/social_cybernetics/domain/types.py`, `src/social_cybernetics/domain/__init__.py`,
    `tests/unit/test_domain.py`.
- [x] Implement independent, correlated, and system shocks.
  - Acceptance: pure functions implement finite recovery, signed relaxation, scope-specific hazards,
    concurrent synchronous wavefronts, simultaneous compounding, and explicit hierarchical RNGs.
  - Verify: focused deterministic examples, sham controls, and repeated-hit cases pass.
  - Files: `src/social_cybernetics/domain/ecology.py`, `tests/unit/test_domain.py`.
- [x] Prove stochastic ecology properties.
  - Acceptance: removal accounting, bounds, seed reproducibility, and mask geometry hold.
  - Verify: Hypothesis suite passes without flaky examples.
  - Files: `tests/property/test_domain_properties.py`, `tests/architecture/test_domain_boundaries.py`.

## Phase C — Runtime integration and records

- [x] Initialize Mesa property layers from configured resource arrays.
  - Acceptance: asymmetric arrays keep documented `(x, y)` orientation and tick-zero measurement.
  - Verify: focused runtime tests pass for uniform and explicit landscapes.
  - Files: `src/social_cybernetics/runtime/mesa/model.py`, `tests/integration/test_mesa_runtime.py`.
- [x] Execute shocks in the explicit shock stage and retain event evidence.
  - Acceptance: shocks occur after regeneration and before observation; no other stage draws them.
  - Verify: stage trace and fixed-seed event regressions pass.
  - Files: `src/social_cybernetics/runtime/mesa/model.py`, `src/social_cybernetics/domain/types.py`,
    `tests/integration/test_mesa_runtime.py`.
- [x] Add complete v0.2 trajectory and CLI regressions.
  - Acceptance: same seed reproduces records; the canonical v0.1 JSON remains unchanged while
    stochastic v0.1 trajectories intentionally migrate to policy stream `(1,)`.
  - Verify: regression suite compares records and JSON byte-for-byte.
  - Files: `tests/integration/test_mesa_runtime.py`, `tests/integration/test_cli.py`,
    `tests/fixtures/ecology_v0.2_summary.json`.

## Phase D — Persistent run bundles

- [x] Define provenance and persistent table schemas.
  - Evidence: normalized configuration, software/RNG provenance, JSON summary, manifest, and six
    explicit Arrow table schemas validate and round-trip, including empty tables.
- [x] Write fail-closed atomic Parquet bundles.
  - Evidence: sibling staging, digest/schema/value validation, Linux atomic no-replace publication,
    collision preservation, and cleanup-on-failure tests pass. See ADR 0008.
- [x] Expose `scs run --output` with stable failure behavior.
  - Evidence: the CLI preserves JSON stdout, rejects an existing destination before execution, and
    persists real runtime shock and damage evidence.
- [x] Stream complete NetCDF spatial history.
  - Evidence: tick zero and every completed tick use exact `(tick, x, y)` coordinates; four dynamic
    ecological variables and two static baselines validate against configuration and completed ticks.
    Runtime failures remove staging, and successful CLI bundles publish NetCDF and Parquet together.

## Phase E — Batch and sensitivity workflows

- [x] Add deterministic sequential batch execution and aggregate indexes.
  - Evidence: relative base configuration plus ordered recursive overrides, explicit per-run seeds,
    duplicate-seed controls, full preflight validation, sequential failure isolation, exact child
    bundles, normalized provenance/configuration hashes, equivalent JSON/Parquet indexes, recursive
    bundle validation, deterministic complete-tree digests, and atomic no-overwrite publication.
  - Interface: `scs batch --spec configs/batch-v0.2.yml --output results/batch-v0.2`.
- [x] Simplify batch validation before adding sensitivity behavior.
  - Acceptance: `validate_batch_bundle` and normalized-run validation read as named sequential checks;
    focused C901 reports no batch violations; schemas, error ordering, and published bytes are
    unchanged.
  - Verify: existing batch/config tests pass without modification, deterministic bundle-digest tests
    remain exact, and `just check` passes.
  - Evidence: both prior batch C901 violations (17 and 28) are eliminated; 197 unchanged tests pass
    with 90.98% branch-aware coverage, clean Ruff/Pyright checks, and a consistent Conda lock.
  - Files: `src/social_cybernetics/batch.py`, `tasks/plan.md`, `tasks/todo.md`.
- [x] Complete the sensitivity evidence and decision gate.
  - Decisions required: screening method, shock-scope treatment, parameter paths/ranges, design seed,
    model-seed pairing/replication, and maximum run budget.
  - Acceptance: a paired literature note distinguishes support, counterevidence, stochastic-model
    boundaries, and project choices; specification/assumptions record every selected semantic.
  - Evidence: ADR 0011 specifies three separate scope designs, four levels, 100 candidate and 10
    selected trajectories, design seed 42, paired model seeds 101/202/303, broad explicit ranges, and
    a 600-run fail-closed cap. The literature note distinguishes screening evidence from calibration
    and final inference.
  - Files: `docs/literature/items/<sensitivity-note>.md`, `docs/literature/literature_matrix.md`,
    `docs/model_specification.md`, `docs/assumptions.md`, `tasks/plan.md`.
- [x] Add validated, seeded sensitivity designs after the decision gate.
  - Acceptance: declared scalar paths and ranges reject unknown, categorical, inactive, or invalid
    fields; the design is reproducible from its own recorded seed and emits ordered batch runs with
    explicit model seeds and configuration provenance.
  - Verify: focused unit/property tests cover bounds, determinism, run counts, seed pairing, and full
    `SimulationConfig` validation; generated designs execute through the existing batch boundary.
  - Evidence: the canonical specification resolves deterministically to 600 validated runs (180
    independent, 240 correlated, 180 system); a tiny CLI design publishes through the ordinary batch
    validator; explicit seed-type regression tests reject YAML coercion; `just check` passes 214 tests
    with 90.90% branch-aware coverage.
  - Files: one sensitivity configuration module, its tests, one CLI/config integration, and at most
    two reconciled documentation/configuration files.
- [x] Add verification experiments for ecological inequality and mortality controls.
  - Acceptance: no-shock, sham-shock, scarcity/mortality, and scope-comparison fixtures retain raw
    outcomes and separate parameter effects from replicate-seed variation.
  - Verify: analysis smoke tests read only published JSON/Parquet/NetCDF evidence and reproduce fixed
    small-design results.
  - Evidence: `configs/verification-v0.2.yml` publishes 12 runs covering paired no-shock/sham
    equivalence, forced scarcity mortality, and three paired seeds for every shock scope. The
    integration regression checks raw Parquet outcomes and complete child NetCDF history. `just
    check` passes 215 tests with 91.08% branch-aware coverage.

## Phase F — Release reconciliation

- [x] Update SolaraViz for heterogeneous landscapes and shock events.
  - Evidence: the page uses `configs/visualization-v0.2.yml`, renders the heterogeneous stock field
    and living-agent energy, and reports recovery, active-event, and damage counters from public
    runtime evidence. Unit tests and isolated Chromium stepping pass; `docs/solara-v0.2.png` is the
    reference screenshot.
- [x] Reconcile all status documentation and record the v0.2 experiment environment.
  - Evidence: specification, assumptions, architecture, roadmap, dashboard, README, plan, task list,
    and experiment log identify v0.2 as verified and retain its limitations and project choices.
- [x] Pass clean lock installation, `just check`, browser verification, and scheduler agreement.
  - Evidence: a new `/tmp` prefix installed from `conda-lock.yml`; the editable package, baseline
    validation/regression, 600-run design resolution, and published verification regression passed.
    `just check` passes 217 tests at 91.08% coverage, and isolated Chromium captures the stepped v0.2
    page with only the documented upstream warning. Stage-order agreement remains regression-tested.
