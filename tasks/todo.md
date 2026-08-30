# Three-Study Programme Refactor Task List

Each task is a reviewable slice touching no more than five files. A checked task requires its stated
verification evidence, not merely code presence.

## Completed foundation retained

- [x] Verify deterministic material control and exact scheduler semantics.
- [x] Implement and verify heterogeneous landscapes and recoverable independent, correlated, and
  system shocks.
- [x] Implement immutable shock evidence, streamed spatial history, fail-closed run bundles,
  deterministic batches, Morris design generation, and isolated-browser visualization.
- [x] Pass the pre-refactor release gate: 217 tests, 91.08% branch-aware coverage, Ruff, Pyright,
  dependency/lock synchronization, clean lock install, baseline byte regression, and browser check.

## Phase A — Programme and study specifications

- [x] A1. Add the refactor requirements crosswalk and programme overview.
  - Acceptance: every section of `Full Refactor.md` maps to retain, implement in Project 1, specify
    for later, or reject as outside scope.
  - Verification: no external-document imperative is treated as authorization beyond the user request.
  - Evidence: the crosswalk separates authority from requirements input; the overview fixes the
    three-study progression, authority chain, seven gates, and honest current status.
  - Files: `docs/refactor_crosswalk.md`, `docs/programme/overview.md`.
- [x] A2. Define programme theory and theory matrix.
  - Acceptance: each theory entry identifies discipline, study, correlate, observable, required and
    absent mechanisms, permitted/prohibited inference, and sources.
  - Verification: mechanism evidence is distinguishable from interpretation and calibration.
  - Evidence: the theory layer separates mechanism-facing and interpretive roles; every matrix row
    names required/absent mechanisms, licensed/prohibited inference, evidence role, and source.
  - Files: `docs/programme/theory.md`, `docs/programme/theory_matrix.md`.
- [x] A3. Define shared ontology, causal map, and scope.
  - Acceptance: objective, privately actionable, and socially accessible opportunity are distinct;
    reserved political-economic terms have necessary conditions.
  - Verification: no future state appears in the Project 1 ontology.
  - Evidence: the ontology reserves politically loaded terms, the causal map identifies each
    cross-study transformation, and scope makes later-study mechanisms non-executable now.
  - Files: `docs/programme/shared_ontology.md`, `docs/programme/causal_map.md`,
    `docs/programme/scope.md`.
- [x] A4. Define the interpretation protocol and programme claims boundary.
  - Acceptance: seven required interpretation fields and the five-level methodological rule are
    mandatory for headline results.
  - Verification: prohibited conclusions from the refactor are enumerated.
  - Evidence: the protocol retains all eight distinct result fields and five analytical levels; the
    claims document states the exact prohibited translations and extension gate.
  - Files: `docs/programme/interpretation_protocol.md`, `docs/programme/claims_and_limits.md`.
- [x] A5. Create Project 1's eight-document scientific package.
  - Acceptance: specification, theory, hypotheses, experiments, validation, analysis, interpretation,
    and limits jointly define all seven completion gates.
  - Verification: equations and edge cases are implementation-ready.
  - Evidence: eight linked documents define mechanics, theory, falsifiable comparisons, exact
    140-run design, metric equations/edge cases, validation gates, interpretation template, and limits.
  - Files: split into two commits of four files under `docs/studies/project_1/`.
- [x] A6. Create Project 2's eight-document specification package.
  - Acceptance: observation channel `C=(radius, noise, delay)`, fixed-policy/Q-learning comparisons,
    information inequality, experiments, metrics, boundaries, and freeze gates are complete.
  - Verification: documents state that Project 2 is specified, not implemented.
  - Evidence: eight documents define sensing, belief, fixed/Q policies, exact P2-A/P2-B designs,
    information/conversion measures, seven gates, interpretations, and protected exclusions.
  - Files: split into two commits of four files under `docs/studies/project_2/`.
- [x] A7. Create Project 3's eight-document specification package.
  - Acceptance: network reports, trust, rewiring, capability diffusion, D0–D3 circulation accounting,
    relational metrics, boundaries, and freeze gates are complete.
  - Verification: credit stock is conserved and distinct from obligation claims in the specification.
  - Evidence: eight documents define reports/trust/rewiring, complete-profile diffusion, D0–D3
    accounting, 330 planned runs, relational metrics, invariants, interpretation, and limits.
  - Files: split into two commits of four files under `docs/studies/project_3/`.
- [x] A8. Expand the literature matrix and add missing paired-evidence notes.
  - Acceptance: the requested 13-column schema is used and Project 1 mechanisms/interpretations have
    supporting, boundary, and counterevidence roles where available.
  - Verification: sources are verified against primary or authoritative records; parameter values
    remain labelled as project choices.
  - Evidence: the 14-field matrix classifies 36 sources; four Project 1 paired notes record support,
    counterevidence/boundaries, licensed use, prohibited use, and project choices. Future-study rows
    still needing paired review remain explicitly marked `reading`.
  - Files: `docs/literature/literature_matrix.md` plus at most four notes per slice.
- [x] A9. Record the study-driven architecture decision.
  - Acceptance: configuration naming, legacy normalization, project-specific state, schema migration,
    and non-executable future studies are explicit.
  - Verification: ADR index and architecture links resolve.
  - Evidence: ADR 0012 separates study/config/artifact version axes, fixes legacy normalization and
    composed-state policy, and the architecture marks Project 2/3 as non-executable.
  - Files: `docs/adr/0012-study-driven-programme.md`, `docs/adr/README.md`,
    `docs/architecture.md`.

## Phase B — Study 01 contracts and evidence

- [x] B1. Add `Study01Config` and explicit legacy normalization.
  - Acceptance: canonical Project 1 YAML validates; legacy v0.1/v0.2 YAML resolves equivalently;
    unsupported study IDs fail closed.
  - Verification: configuration and CLI tests pass; baseline summary is byte-identical.
  - Evidence: canonical baseline uses `study: project_1`/schema `1.0.0`; legacy v0.1/v0.2 inputs
    normalize one-way, unsupported study IDs fail, 129 focused config/CLI/batch/persistence/spatial/
    sensitivity tests pass, and the existing baseline byte regression remains green.
  - Files: `src/social_cybernetics/config.py`, `tests/unit/test_config.py`,
    `tests/integration/test_cli.py`, `configs/baseline.yml`.
- [x] B2. Remove dormant future agent state.
  - Acceptance: holdings, debt, and information capability are absent from shared domain state and
    Project 1 snapshots.
  - Verification: domain tests and architecture search reject those fields in Project 1 code.
  - Evidence: `AgentState` now contains only ID, energy, and alive; snapshots add tick/position only;
    Project 1 cohort schema v1 removes holdings/debt/capabilities, bundle schema is v1, and 83 focused
    architecture/domain/runtime/persistence/batch/CLI regressions pass.
  - Files: `src/social_cybernetics/domain/types.py`, `src/social_cybernetics/runtime/mesa/model.py`,
    `tests/unit/test_domain.py`, `tests/architecture/test_boundaries.py`.
- [ ] B3. Define immutable agent-transition evidence.
  - Acceptance: one record can reconstruct local exposure, request, movement, extraction, shortfall,
    energy change, and death without duplicating mutable position.
  - Verification: immutability and field-invariant tests pass.
  - Files: `src/social_cybernetics/domain/types.py`, `src/social_cybernetics/domain/__init__.py`,
    `tests/unit/test_domain.py`.
- [ ] B4. Record one transition per active agent-tick.
  - Acceptance: records follow sorted agent identity and existing stage semantics without extra RNG
    draws or behavioral changes.
  - Verification: full tiny trajectories and activation-order invariance remain exact.
  - Files: `src/social_cybernetics/runtime/mesa/model.py`,
    `tests/integration/test_mesa_runtime.py`.
- [ ] B5. Publish the Project 1 transition table and migrate bundle schemas.
  - Acceptance: exact Arrow schema, empty-table behavior, cross-record counts, and bundle validation
    are fail closed.
  - Verification: persistence unit and CLI bundle tests pass, including tampering cases.
  - Files: `src/social_cybernetics/persistence.py`, `src/social_cybernetics/cli.py`,
    `tests/unit/test_persistence.py`, `tests/integration/test_cli.py`.

## Phase C — Pure Project 1 analysis

- [ ] C1. Add robust distribution shares and Gini helpers.
  - Acceptance: deterministic top/bottom shares cover empty, singleton, tied, and zero-total inputs.
  - Verification: example and property tests pass; `social_cybernetics.metrics.gini` remains public.
  - Files: `src/social_cybernetics/metrics.py`, `tests/test_metrics.py`.
- [ ] C2. Add subsistence-security metrics.
  - Acceptance: frequency, spell lengths, depth, maximum depth, and catastrophic probability follow
    the Project 1 equations and censoring rules.
  - Verification: hand-calculated multi-agent histories and edge cases pass.
  - Files: `src/social_cybernetics/analysis/project1.py`,
    `src/social_cybernetics/analysis/__init__.py`, `tests/unit/test_project1_analysis.py`.
- [ ] C3. Add distribution and persistence metrics.
  - Acceptance: harvest/energy/need inequality, quantile shares, rank autocorrelation, transition
    matrix, advantage duration, and half-life return typed values plus definedness metadata.
  - Verification: order-invariance, ties, extinction, and known-rank examples pass.
  - Files: `src/social_cybernetics/analysis/project1.py`,
    `tests/unit/test_project1_analysis.py`, `tests/property/test_analysis_properties.py`.
- [ ] C4. Add ecological deficit and recovery metrics.
  - Acceptance: depletion, capacity/regeneration deficits, recovery duration, and cumulative recovery
    deficit derive from complete spatial history and damage evidence.
  - Verification: no-shock zero deficits, forced damage, overlap, and incomplete history fail closed.
  - Files: `src/social_cybernetics/analysis/project1.py`,
    `tests/unit/test_project1_analysis.py`, `tests/property/test_analysis_properties.py`.
- [ ] C5. Assemble and serialize the Project 1 outcome vector.
  - Acceptance: raw measures and definedness flags are JSON-safe; no composite ranking is emitted.
  - Verification: published-bundle-only regression reproduces a fixed fixture.
  - Files: `src/social_cybernetics/analysis/project1.py`,
    `src/social_cybernetics/analysis/artifacts.py`, `tests/integration/test_project1_analysis.py`.

## Phase D — Canonical experiments

- [ ] D1. Define and validate the Project 1 experiment-plan contract.
  - Acceptance: groups, ordered conditions, paired seeds, horizons, and maximum run count are explicit;
    generated runs pass `Study01Config`.
  - Verification: invalid grids and unstable IDs fail before execution.
  - Files: `src/social_cybernetics/project1_experiments.py`,
    `tests/unit/test_project1_experiments.py`, `configs/project-1.yml`.
- [ ] D2. Generate P1-A and P1-B runs.
  - Acceptance: homogeneous/heterogeneous and density-by-mobility comparisons share controlled
    baselines and ten paired seeds.
  - Verification: exact run count, labels, positions, and seed pairing regressions pass.
  - Files: experiment module, focused tests, canonical config.
- [ ] D3. Generate P1-C and P1-D runs.
  - Acceptance: scope comparisons match expected initial affected-cell count where feasible; recovery
    comparisons change only recovery duration.
  - Verification: realized configs and matching calculations are tested exactly.
  - Files: experiment module, focused tests, canonical config.
- [ ] D4. Generate P1-E persistence runs.
  - Acceptance: three frozen representative regimes use 1,000 ticks and the same ten seeds without
    adding mechanisms.
  - Verification: selection provenance and exact realized configs are retained.
  - Files: experiment module, focused tests, canonical config.
- [ ] D5. Add Project 1 experiment and analysis CLI boundaries.
  - Acceptance: execution reuses batch publication; analysis consumes only validated published
    bundles and atomically publishes aggregate JSON/Parquet evidence.
  - Verification: tiny end-to-end design passes, existing destinations are refused, failures are typed.
  - Files: `src/social_cybernetics/cli.py`, `src/social_cybernetics/project1_experiments.py`,
    `src/social_cybernetics/analysis/artifacts.py`, `tests/integration/test_project1_cli.py`.

## Phase E — Project 1 freezes

- [ ] E1. Freeze Project 1 specification and literature evidence.
- [ ] E2. Freeze verification and baseline equivalence.
- [ ] E3. Freeze sensitivity evidence under Study 01 configuration.
- [ ] E4. Execute and freeze P1-A–E experimental evidence.
- [ ] E5. Freeze analysis, representative regimes, and interpretation tables.
  - Acceptance for E1–E5: `docs/studies/project_1/` status tables link exact configuration, artifact
    identity, environment, result, assumptions, alternatives, absent mechanisms, and prohibited
    conclusions.
  - Verification: all seven gates independently read `frozen`; no claim depends on a live model object.

## Phase F — Reconciliation and release

- [ ] F1. Reconcile the canonical repository documentation and remove version-driven active wording.
  - Files: `README.md`, `docs/00-dashboard.md`, `docs/model_specification.md`,
    `docs/research_roadmap.md`, `docs/experiment_log.md` in separate ≤5-file slices.
- [ ] F2. Apply the code-simplification review to all changed production modules.
  - Acceptance: named linear stages, explicit records, no speculative abstraction, no focused C901
    regressions without a documented scientific reason.
- [ ] F3. Pass full release verification.
  - Acceptance: focused and property tests, `just check`, exact baseline regression, run/batch/analysis
    bundle validation, isolated browser check, clean lock installation, and scheduler/spec agreement.
- [ ] F4. Report completion temperature honestly.
  - Acceptance: Project 1 and each freeze gate have separate percentages; Projects 2–3 distinguish
    specification completeness from implementation completeness.
