# Assumptions, Limitations, and Protected Extensions

## Current assumptions

- Units are abstract and dimensionless.
- The default torus removes boundary-created inequality from the control condition.
- Cells permit unlimited co-location so movement conflict does not contaminate resource competition.
- Renewable resources relax toward capacity and recover from zero.
- Harvested resources are consumed immediately; stored holdings do not yet exist.
- The literal control policy values every harvest opportunity and can accumulate energy without bound.
- The baseline has perfect local sensing, a copied belief, one principal action, no shocks, and no
  institutional restriction.
- The initial cohort is fixed. Version 0.1 has mortality but no births or migration.
- Welfare is reported as multiple observables rather than a composite score.

## Active version 0.2 assumptions

- Heterogeneous landscapes are explicit realized matrices, indexed `(x, y)`, so initialization is
  auditable and adds no hidden random stream.
- Shock-enabled configurations explicitly declare every scientific parameter; there are no severity
  profiles or hidden shock defaults.
- Shocks can immediately remove stock, temporarily reduce effective capacity, and temporarily
  suppress effective regeneration as three independently configurable mechanisms.
- Effective capacity and regeneration recover linearly on a cell-local clock. Repeated hits compound
  against current effective values and restart recovery.
- Current stock may temporarily exceed effective capacity but remains bounded by immutable baseline
  capacity. Signed relaxation moves it toward the effective target.
- Independent, correlated-wavefront, and system shocks use scope-specific Bernoulli semantics.
- Correlated events propagate concurrently through synchronous, independent per-neighbour attempts;
  outward rounds are limited explicitly.
- Event snapshots, exposure records, and simultaneous cell-damage records are immutable evidence.
- Permanent, recorded RNG stream keys isolate policy draws from shock initiation, location, and
  propagation draws.
- Policy, sensing, gating, metabolism, and multi-occupancy resolution stay fixed while ecological
  effects are studied.
- Persistence is opt-in, accepts immutable records, and cannot overwrite an existing run destination.
  A bundle becomes visible only after staged schema, digest, row-count, and round-trip validation.
- Atomic publication currently requires Linux `renameat2(RENAME_NOREPLACE)` and fails closed when the
  primitive is unavailable. The manifest detects accidental corruption but is not a signature.
- Persistent runs synchronously stream tick zero and every completed tick of ecological spatial state
  into staged NetCDF. This bounds Python memory by grid size rather than run duration but adds one
  compression/synchronization operation per tick.
- Spatial axes are permanently ordered `(tick, x, y)`; baseline capacity and regeneration are static,
  while stock, effective capacity, effective regeneration, and recovery remaining are dynamic.
- Batch runs execute sequentially in declared order. Every override declares a seed explicitly;
  duplicate seeds remain legal and visible.
- All resolved batch configurations validate before execution. Per-run failures are recorded and do
  not stop later runs; aggregate-output failures publish no batch.
- A batch is one atomic attempt: successful children are complete run bundles, failed runs have no
  child directory, and JSON/Parquet indexes retain raw continuous summary outcomes.
- Sensitivity screening uses separate independent, correlated, and system Morris designs because the
  scopes have different semantics and active inputs; `shock.kind` is not assigned a numeric order.
- The first screen uses four levels, 100 candidate and 10 locally optimized selected trajectories,
  design seed 42, and three paired model seeds (`101`, `202`, `303`) at every point.
- The `[0, 1]` probability/fraction ranges, recovery range `[1, 10]`, spread-round range `[0, 3]`, and
  600-run cap are broad experimental controls, not empirically calibrated distributions.
- Paired seeds reduce comparison noise but do not remove stochastic uncertainty. Analysis must retain
  replicate identity and cannot interpret Morris screening statistics as causal effects or variance
  shares.
- SolaraViz is a read-only debugging adapter. Its shock counters are derived from public immutable
  event/damage records and recovery arrays; the page cannot mutate or bypass model transitions.

## Known limitations

- Parameter values are verification fixtures, not empirical estimates.
- Direct resource-to-energy conversion omits storage, spoilage, and consumption choice.
- A current-cell observation gives cognitive boundaries a software form but does not yet model
  perceptual error.
- Multi-occupancy differs from classic single-occupancy Sugarscape.
- Regime clustering is exploratory and must be accompanied by continuous features and stability
  analysis.
- Governance categories initially describe norm diffusion rather than formal authority delegation.
- Multiplicative damage and linear recovery are controlled ecological stress mechanisms, not an
  empirically calibrated hazard process. Alternative recovery curves, press disturbances, and
  permanent capacity damage require later variants.
- Three model seeds are sufficient for a broad screening pass, not for precise uncertainty intervals
  or final scientific inference. Important factors require a later, narrower replicated experiment.

## Protected extensions from early design work

The source drafts also proposed ideas intentionally excluded from version 0.1:

- separate food and material/tool resources;
- friction and resource-specific renewal/extraction time;
- physical tools that alter movement or extraction productivity;
- observation and action radii, signal/noise, and delayed feedback;
- communication and control actions with different spatial radii;
- internal hunger/health signals and external embodied action systems;
- social cooperation, exploitation, labour, trade, organisations, and institutions;
- information compression as a theoretical account of cognition.

These ideas are not rejected. They remain protected from entering the control model until a versioned
hypothesis, literature basis, state variables, interaction rule, and verification test exist.

## Boundaries for contributors

### Always

- update the specification before changing scientific semantics;
- validate external configuration once at the boundary;
- run focused tests and the full quality gate;
- record seeds, versions, and normalised configuration for experiment-producing versions.

### Ask first

- add or remove a scientific mechanism;
- change tick ordering or an accounting identity;
- change dependency, lockfile, CI, or output schema policy;
- redefine an outcome as welfare or introduce empirical units.

### Never

- use global randomness in scientific code;
- let agents mutate environment state directly;
- remove failing scientific tests to accept changed behaviour;
- commit secrets, generated results, caches, or local Obsidian plugin data.
