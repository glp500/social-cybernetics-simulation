# Experiment Log

## 2026-08-30 — Stochastic-ecology visualization checkpoint

**Status:** Phase F Task 19 implemented and browser-verified

Replaced the uniform no-shock page fixture with a checked 3×2 heterogeneous correlated-shock
configuration. Resource colors now auto-scale to realized heterogeneous data. The read-only metrics
panel adds recovering cells, active shock events, and cells damaged on the current tick, derived from
public arrays and immutable records rather than private orchestration state.

The verifier now allocates an available loopback port instead of assuming 8765 is unused. In isolated
headless Chromium it loaded the page, rendered the grid/agent/metrics, stepped once, observed the
resource and energy changes, retained usable controls, and captured `docs/solara-v0.2.png`. There
were no application console errors or warnings; the single previously documented upstream Vue
fallback warning remains. `just check` passed 217 tests with 91.08% branch-aware coverage.

## 2026-08-30 — Ecological verification experiment set

**Status:** Phase E complete; shock-aware visualization next

Added a compact 12-run batch with one no-shock control, a same-seed zero-damage system-shock sham,
one guaranteed mortality condition with zero capacity and stock, and independent, correlated, and
system shocks under paired seeds 101, 202, and 303. Scope comparisons share event probability,
damage, recovery, duration, landscape, agents, sensing, policy, and gate; only the spatial shock
mechanism and the correlated propagation fields differ.

The integration analysis reads the published Parquet index and child NetCDF histories after recursive
bundle validation. It confirms no-shock/sham equality, death retention in scarcity, seed blocks,
non-null raw outcomes, exact fixed resource totals for all nine scope runs, and six spatial snapshots
for a five-tick correlated child. No assertion reads a live model object.

`just check` passed 215 tests with 91.08% branch-aware coverage, Ruff formatting/lint, Pyright
standard, dependency synchronization, and the unchanged Linux-64 lock input hash.

## 2026-08-30 — Scope-stratified Morris sensitivity workflow

**Status:** Phase E Task 17 implemented and verified; verification experiments next

Recorded paired primary evidence and ADR 0011 before implementation. The accepted broad screen uses
separate independent, correlated, and system designs rather than assigning an artificial numeric
order to shock scope. Each design uses four levels, 100 candidate and 10 locally optimized selected
trajectories under design seed 42. Common shock factors span `[0, 1]`; recovery ticks span `[1, 10]`;
correlated spread rounds span `[0, 3]`. Model seeds 101, 202, and 303 repeat at every point. All values
are project controls, not empirical calibration.

Added a strict sensitivity YAML boundary and `scs sensitivity --spec ... --output ...`. Unknown,
categorical, inactive, duplicate, invalid, and non-integral factor paths fail before execution. YAML
booleans, strings, floats, and negative values cannot be coerced into model seeds. The canonical
configuration resolves deterministically to 600 fully validated runs: 180 independent, 240
correlated, and 180 system. A tiny end-to-end fixture confirms generated runs publish through the
existing batch contract; sensitivity introduces no second runner or artifact format.

The code-simplification pass kept factor lookup, exact-grid conversion, scope preflight, sampling,
and run generation as named linear steps. Focused C901 reports no sensitivity-module violations.
`just check` passed 214 tests with 90.90% branch-aware coverage, Ruff formatting/lint, Pyright
standard, dependency synchronization, and the existing Linux-64 lock input hash.

## 2026-08-30 — Batch validation simplification checkpoint

**Status:** behavior-preserving maintainability refactor verified

Reviewed the active plan and task checklist before starting sensitivity work. Phases A–D and Phase E
Task 16 remain supported by executable evidence; sensitivity design and verification experiments are
the next incomplete tasks. A focused Ruff complexity audit identified batch validation—not the
explicit scientific scheduler—as the clearest recent readability hotspot.

Split normalized-batch and published-bundle validation into named sequential checks for root layout,
manifest schema, artifact descriptors, resolved configuration provenance, JSON index, Parquet index,
aggregate counts, and child bundles. This retains the same fail-closed checks and their order while
making the public validator read as the artifact contract. No tests or expected artifacts changed.

`just check` passed 197 tests with 90.98% branch-aware coverage, Ruff formatting/lint, Pyright
standard, dependency synchronization, and lockfile consistency. Focused C901 analysis reports no
remaining violation in `batch.py`; the previous normalized-batch and full-bundle validators measured
17 and 28 respectively.

## 2026-08-29 — Stochastic ecological baseline begins

**Status:** Phases A–D and Phase E batch execution verified; sensitivity design next

Version 0.1 remains the stable control. The active v0.2 dependency order is explicit landscape input,
shock evidence and pure mechanisms, runtime integration, persistent bundles, batches, then sensitivity
analysis. Policy, observation, gating, metabolism, and simultaneous competition remain fixed.

The documentation audit initially found that heterogeneous landscapes had a Sugarscape literature
anchor while the proposed shock geometries lacked a mechanism note. The evidence gate was resolved
before shock code: Turner et al. (1989) now anchors initiation and spatially connected disturbance,
and Massie et al. (2015) supports the distinction between independent and spatially correlated
environmental forcing. The note explicitly labels multiplicative damage, synchronous Von Neumann
wavefront transmission, and finite linear recovery as controlled project choices rather than claims
from those sources.

## 2026-08-29 — Deterministic failure-isolated batch execution

**Status:** implemented and verified; Phase E sensitivity design next

Added `scs batch --spec ... --output ...` and the batch YAML schema recorded in ADR 0010. A batch
names a base model configuration plus ordered unique run IDs and nested overrides. Every run override
must state a non-negative integer seed explicitly; duplicate seeds are supported. Mappings recursively
merge and scalar/list values replace. The loader validates the base and every complete resolved
configuration before output staging or model construction.

Execution is sequential in declared order. Each successful condition publishes the existing complete
run-bundle contract under `runs/<run-id>`. Invariant, runtime, or child-output failures produce typed
index records, leave no partial child directory, and do not stop later conditions. The entire attempt
is staged as one sibling directory, recursively validated, and atomically published without replacing
an existing destination. Aggregate-output failure publishes nothing.

Batch schema `scs-batch-bundle/v0.1.0` retains normalized base configuration, explicit overrides,
complete resolved configurations and canonical SHA-256 identities. Ordered JSON and explicitly typed
Parquet indexes contain the same successful summaries and failure evidence; raw resource, energy,
harvest, unmet-need, and inequality measures remain directly available. Validation reconstructs every
override, compares JSON/Parquet values, checks aggregate and child digests, validates each successful
run bundle, and rejects extra children or child substitution.

`just check` passed 197 tests with 90.84% branch-aware coverage, Ruff formatting/lint, Pyright
standard, dependency synchronization, and lockfile-input consistency. Tests cover recursive merge and
list replacement, unsafe IDs and non-portable YAML, explicit/duplicate seeds, full preflight
validation, declared execution order, all three typed run failures, continuation after failure,
collision preflight, complete-tree digest equality across reruns, JSON/Parquet equality, and
adversarial cross-artifact tampering.

## 2026-08-29 — Fail-closed persistent Parquet bundles

**Status at this checkpoint:** implemented and verified; NetCDF spatial history awaited a decision

Added an opt-in `scs run --output` boundary that persists normalized configuration, the deterministic
JSON summary, software and exact RNG-registry provenance, and six explicit Parquet tables: model,
cohort, agent events, shock-event snapshots, shock exposures, and cell-damage applications. Empty
tables preserve their complete Arrow schemas and schema metadata. PyArrow 25.0.0 is now a synchronized
runtime dependency; the Linux-64 Conda lock was regenerated from `environment.yml` rather than edited.

Publication implements ADR 0008. It writes into a unique sibling staging directory, validates the
exact file set, canonical configuration, summary and provenance contracts, SHA-256 digests, byte and
row counts, Arrow schemas, and Parquet value round trips, then uses Linux
`renameat2(RENAME_NOREPLACE)` for atomic no-overwrite publication. Tests cover existing files,
directories and broken symlinks, a concurrent destination collision, build failure cleanup, malformed
configuration, manifest and artifact tampering, optional-library absence, deterministic manifests,
and real runtime shock/damage persistence.

`just check` passed 142 tests with 92.90% branch-aware coverage, Ruff format/lint, Pyright standard,
dependency synchronization, and lockfile-input consistency. The persistence module has 80% local
branch-aware coverage while the full scientific package remains above the 90% gate; every publication
success, collision, cleanup, schema round trip, and CLI behavior required for this slice is exercised.
The no-output baseline and v0.2 CLI regressions remain byte-identical.

At this checkpoint, the runtime retained
final environmental arrays and sparse damage evidence, but not a complete tick-indexed spatial array
history. Complete per-tick capture, initial/final capture, and deferral to a streaming writer have
different scientific and memory consequences and require selection before NetCDF implementation.

## 2026-08-29 — Complete streamed spatial history

**Status:** implemented and verified; Phase D complete

Selected complete tick streaming rather than in-memory buffering, endpoint-only snapshots, or
deferral. Every persistent run now opens its sibling staging bundle before model construction and
writes `spatial.nc` incrementally. The NetCDF artifact uses permanent `(tick, x, y)` orientation,
float64 ecological values, int64 tick/recovery values, one-tick bounded spatial chunks, compression,
checksums, and synchronous flushes. It contains tick zero plus every completed tick for stock,
effective capacity, effective regeneration, and recovery remaining, with baseline capacity and
regeneration stored once.

Mesa depends only on a typed synchronous snapshot-sink protocol. Tick zero is emitted when execution
begins rather than in the constructor, allowing a pre-run verification fixture to remain
authoritative. Once tick zero has been emitted, resource fixtures are rejected. Model or output
failure closes the NetCDF handle and removes staging; successful runs close and validate the stream
before manifest construction and ADR 0008 publication.

Bundle schema `scs-run-bundle/v0.2.0` requires the spatial artifact and records its schema, variables,
dimensions, and snapshot count. Validation checks canonical coordinates, exact dtypes and dimensions,
`completed_ticks + 1` snapshots, static baselines against normalized configuration, file digest, and
the existing cross-artifact contracts. NetCDF4 is now a synchronized runtime dependency; Xarray
remains in the research environment for analysis.

`just check` passed 152 tests with 90.71% branch-aware coverage, Ruff format/lint, Pyright standard,
dependency synchronization, and lockfile-input consistency. Tests exercise exact system-shock spatial
values, duration-zero history, fixture timing, consecutive tick enforcement, shape and baseline
invariants, incomplete-history rejection, output failure cleanup, and unchanged JSON-only CLI
regressions.

## 2026-08-29 — Deterministic foundation rewrite

**Status:** implemented and verified

**Purpose:** establish the version 0.1 control model before introducing stochastic ecology, cognitive
tools, adaptive learning, or institutions.

**Canonical fixture:** `configs/baseline.yml` — seed 42, 5 by 5 torus, uniform renewable resources,
one centred agent, literal local harvest-or-move policy.

**Locked environment:** Linux-64; Python 3.12.14; Mesa 3.5.1; Solara 1.61.0; NumPy 2.5.2; Pydantic
2.13.5; conda-lock 4.0.2. Mesa's visualization stack is constrained to ipyvue 1.x and ipyvuetify 1.x;
a clean lock install exposed and prevented an incompatible automatic upgrade to their 3.x lines.

**Verification commands:**

```bash
just check
just browser-check
conda-lock install --name social-cybernetics-lockcheck conda-lock.yml
conda run -n social-cybernetics-lockcheck pytest --cov=social_cybernetics --cov-fail-under=90
```

The clean-room environment was removed after verification. The suite passed 56 tests with 97.02%
branch-aware coverage. Ruff formatting/lint, Pyright standard, dependency synchronization, the
lockfile input hash, V0–V4 integration fixtures, fixed-seed trajectories, CLI byte regression,
architecture boundaries, death retention, and scheduler-stage agreement all passed. Isolated
Chromium rendered the grid, resources, living agent, metrics, and controls; stepping changed total
resources from 250 to 248 and cohort mean energy from 10 to 11. The reference image is
`docs/solara-v0.1.png`.

**Canonical run summary:**

```json
{"alive_count":1,"cohort_mean_energy":16.565938,"completed_ticks":100,"dead_count":0,"inequality":{"energy_gini":0.0,"harvest_gini":0.0,"unmet_need_gini":0.0},"schema_version":"scs-run-summary/v0.1.0","seed":42,"total_harvest":106.565938,"total_resources":240.0,"unmet_need":0.0}
```

**Known limitations:** the literal control policy intentionally has no energy cap. Outputs remain
in-memory except for the CLI summary. There are no shocks, learning, communication, institutions,
exchange, demographics, or persistent scientific bundles. The browser verifier rejects application
warnings and errors but narrowly permits one deterministic `jupyter-vue` legacy-template fallback
warning emitted by the pinned upstream Vue 2 compatibility layer.

## 2026-08-29 — Mechanism-focused primary literature audit

- Adopted a paired-evidence standard: every roadmap mechanism note records supporting evidence,
  counterevidence or boundary conditions, the justified commitment, and uncalibrated project choices.
- Reviewed primary sources for Q-learning, payoff-biased learning, complex diffusion, adaptive
  communication networks, costly enforcement, polycentric governance, and model-based regime
  discovery.
- No learning, diffusion, network, enforcement, governance, or clustering mechanism was authorized
  for implementation by this literature review.
- The review exposed unresolved design decisions for exposure source counts, trust feedback,
  enforcement scope and failure modes, governance nesting, and cluster-validation protocol.
## 2026-08-29 — Recoverable shock design checkpoint

- Selected separate immediate stock loss, temporary effective-capacity loss, and temporary
  effective-regeneration suppression.
- Selected exact finite linear, cell-local recovery; repeated hits compound against current effective
  state and restart recovery.
- Selected scope-specific Bernoulli hazards and concurrent synchronous correlated wavefronts with
  independent per-neighbour transmission and an explicit outward-round limit.
- Selected temporary stock overshoot above effective capacity, with baseline capacity remaining the
  hard bound and signed relaxation controlling subsequent stock change.
- Selected immutable per-tick event snapshots plus normalized exposure and simultaneous cell-damage
  records, using run-local monotonic event IDs.
- Selected stable RNG namespaces: policy `(1,)`, shock initiation `(2, 1)`, location `(2, 2)`, and
  propagation `(2, 3)`.
- All scientific shock fields are explicit; zero-effect sham shocks are valid matched controls.

## 2026-08-29 — Recoverable shock core and runtime verification

**Status at this checkpoint:** implemented and verified; persistent bundles were next

Implemented immutable recovery, event, exposure, and cell-damage contracts in the Mesa-independent
domain. Pure functions now cover signed resource relaxation, exact finite recovery, simultaneous
compound damage, scope-specific hazards, canonical torus-aware neighborhood geometry, and synchronous
correlated wavefront advancement. The Mesa runtime owns property layers, advances
recovery → regeneration → shock before observation, permits concurrent events, and retains normalized
append-only evidence independently of agent activation.

The permanent RNG registry now applies to every schema: policy `(1,)`; shock initiation `(2, 1)`;
location `(2, 2)`; transmission `(2, 3)`. This intentionally replaces the former unnamespaced v0.1
policy stream. The canonical baseline JSON remains byte-identical because its fixed trajectory never
draws a movement choice; other stochastic v0.1 trajectories require rebaselining.

`just check` passed 120 tests with 97.08% branch-aware coverage, Ruff formatting/lint, Pyright
standard, and lockfile-input consistency. Scientific ecology reached 99% coverage. Fixed-seed tests
cover concurrent correlated events and complete record equality; sham shocks leave policy and
physical trajectories unchanged; CLI summaries for both baseline and explicit v0.2 ecology match
checked-in bytes. Compatibility tests preserve legacy untagged v0.1 resource mappings and pin the
new `(1,)` stochastic movement trajectory. A Hypothesis run exposed and now guards a one-ulp recovery
overshoot at extremely small damage fractions.

At this checkpoint, v0.2 still lacked persistent Parquet/NetCDF bundles, batches,
sensitivity workflows, shock-aware visualization, clean-room lock installation, and browser
verification remain open.
