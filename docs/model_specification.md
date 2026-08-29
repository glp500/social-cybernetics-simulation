# Model Specification: Social Cybernetics Sugarscape

## 1. Purpose and research question

This model studies how information-extending cognitive tools alter adaptive behaviour and how
private reinforcement, social learning, and norm diffusion can produce persistent institutions.
An institution is present only when a bounded group sustains a shared rule and repeatedly enforces
it. The intended contribution is an emergence mechanism, not a claim that tools or institutions
are universally beneficial.

The verified first executable version is a material control model. It asks:

> What survival, resource-access, unmet-need, and inequality dynamics arise from renewable spatial
> resources, energetic constraints, and simultaneous competition before cognitive tools, social
> learning, or institutions are introduced?

Version 0.2 is now the active implementation phase. It adds ecological heterogeneity, shocks, and
reproducible experiment outputs while holding observation, policy, gating, competition, and agent
physiology fixed. Later versions continue to add one mechanism at a time so each causal contribution
remains identifiable.

## 2. Entities, state, and scales

### World

The world is a rectangular lattice of cells connected by a Von Neumann neighbourhood. The default
world is a 5 by 5 torus. A cell has no occupancy limit.

### Cell

- `resource_stock` \(R_x(t)\)
- `resource_capacity` \(K_x\)
- `regeneration_rate` \(r_x\)
- version 0.2: configured heterogeneous capacity and initial-stock fields plus transient shock effects
- later: terrain cost, resource type, and institutional scope

### Agent

- stable identifier
- `energy_reserve` \(E_i(t)\)
- location
- alive/dead state
- birth and optional death ticks
- lifetime harvest
- cumulative unmet need
- observation and belief state
- later: information capabilities, policy values, social ties, rule adoptions, holdings, and roles

### Institution (later versions)

Institutions are detected from persistent social dynamics rather than instantiated as governance
templates. They require:

1. a shared resource-access or allocation rule;
2. a connected and bounded adopting group; and
3. repeated costly enforcement.

Agents may hold compatible rules at local, regional, and system scopes. Nested persistent scopes are
the observable basis for recursive governance.

### Abstract scale

- one cell: an abstract local environment;
- one tick: an abstract decision interval;
- resource units: material resource;
- energy units: biological viability reserve.

No mapping to days, joules, kilograms, or geographic area is claimed without empirical calibration.

## 3. Stocks that must remain distinct

\[
R_x = \text{environmental resources},\quad
E_i = \text{energetic viability},\quad
T_i = \text{time/action capacity}
\]

\[
W_i = \text{stored material holdings},\quad
D_{ij} = \text{obligations},\quad
B_i = \text{belief/information state}
\]

The deterministic core implements \(R\), \(E\), \(T\), and \(B\). Later economic variants add
\(W\) before transfers or debt. Debt records claims and never creates resources or energy.

## 4. Process overview and scheduling

The causal pipeline is:

```text
Environment
  -> Observation
  -> Belief
  -> Action Intent
  -> Institutional Gate
  -> Physical Resolution
  -> Feedback
```

Each tick executes:

1. recovery of existing ecological damage (a no-op in version 0.1);
2. resource relaxation toward current effective capacity;
3. environmental shock propagation and initiation (a no-op in version 0.1);
4. observation of the current cell;
5. belief update;
6. one action intent per living agent;
7. institutional filtering (allow-all in version 0.1);
8. simultaneous physical resolution;
9. energetic accounting;
10. mortality;
11. measurement.

Initial state is measured at tick 0. A completed transition is then measured as tick 1, and so on.

## 5. Design concepts

### Observation and sensing

Agents never inspect arbitrary environmental state. In version 0.1 an observation contains the
current cell's exact resource stock, source `direct`, confidence 1, uncertainty 0, and no delay.
Later tools may change radius, accuracy, delay, memory, aggregation, or communication.

### Belief

Observation is not belief. Version 0.1 copies the latest direct observation into a belief state.
Later versions add forgetting, confidence, social reports, contradictory evidence, and prediction.

### Decision-making and adaptation

The material control policy is intentionally literal:

```text
if believed local resource >= harvest threshold:
    propose HARVEST for harvest capacity
else:
    propose MOVE to one uniformly selected neighbour
```

It has no REST branch and no energy cap. This intentionally permits reserve accumulation and is a
control condition, not a homeostatic theory of behaviour.

The first adaptive policy is tabular Q-learning over discretised energy and believed-resource states
with alpha 0.1, gamma 0.95, and epsilon 0.1. Its scalar private reward measures progress toward an
energy viability target, penalises unmet need and death, and assigns no extra reward above the target.
This private signal is distinct from system-level welfare measurement.

### Interaction and competition

Cells permit multiple agents. Movement therefore has no collision priority. Harvest requests on the
same cell are collected before resources change. If requests exceed available stock, allocation is
proportional:

\[
h_i^* = R_x\frac{h_i}{\sum_j h_j}.
\]

### Learning and social networks

Later versions keep two learning channels separate:

- private reinforcement updates action values from an agent's own outcomes;
- social learning transmits information capabilities and candidate rules.

Information capabilities spread through repeated, costly exposure. A learning action raises
proficiency by 0.2, adoption occurs at 1.0, and the action costs 0.5 energy. Communication ties have
trust that rises with useful information, falls with misleading information, decays when unused, and
occasionally explores new local contacts.

### Norms and institutions

Candidate resource rules are:

- open proportional allocation (control);
- members-only proportional allocation;
- members-only equal quota;
- members-only need-priority allocation.

Rules spread through payoff-biased pairwise imitation with rare innovation. Enforcement consumes the
agent's principal action, costs energy, and applies only to the current cell for that tick. Broader
institutions therefore require distributed local enforcement.

### Stochasticity

Every random draw derives from one run seed through model-owned, recorded NumPy substreams. Permanent
stream key `1` owns policy/movement. Ecological shocks use hierarchical namespace `2`: `(2, 1)` for
initiation, `(2, 2)` for locations, and `(2, 3)` for frontier-edge transmission. Adding a mechanism
must not shift an existing stream. The same configuration, software versions, seed, and stream
registry must reproduce the same trajectory.

### Version 0.2 recoverable shock semantics

Shock-enabled configurations explicitly provide `event_probability`, `stock_loss_fraction`,
`capacity_loss_fraction`, `regeneration_suppression_fraction`, and `recovery_ticks`. Correlated
wavefronts additionally provide `spread_probability` and `max_spread_ticks`. Probabilities and
fractions lie in `[0, 1]`, `recovery_ticks >= 1`, and `max_spread_ticks >= 0`. All damage fractions
may be zero for a sham-event control.

Each cell has immutable baseline capacity \(K_x^0\) and regeneration rate \(r_x^0\), plus recoverable
effective values \(K_x^e(t)\) and \(r_x^e(t)\). If \(m\) events hit a cell simultaneously, damage is
resolved once and order-independently:

\[
R'_x = R_x(1-d_R)^m,\quad
K_x^{e\prime} = K_x^e(1-d_K)^m,\quad
r_x^{e\prime} = r_x^e(1-d_r)^m.
\]

The hit restarts a cell-local linear recovery. Fixed increments return both effective values exactly
to baseline after `recovery_ticks` recovery stages. A later hit compounds against current effective
values and restarts the clock. Current stock may temporarily exceed effective capacity, but never
baseline capacity. Relaxation is therefore signed:

\[
R_x(t+1)=\operatorname{clip}\left(R_x(t)+r_x^e(t)(K_x^e(t)-R_x(t)),0,K_x^0\right).
\]

Shock scopes use distinct Bernoulli semantics:

- independent: one draw per cell per tick; every success is a one-cell event;
- correlated: one draw per tick starts a wavefront event at a uniformly selected epicentre;
- system: one draw per tick; success affects every cell in one event.

A correlated event damages its epicentre immediately. On each later tick, every frontier-to-unaffected
Von Neumann-neighbour edge receives an independent transmission draw. Successful targets form the
next tick's frontier and are damaged once by that event. Events propagate concurrently. The limit
`max_spread_ticks` counts outward rounds after initiation (`0` means epicentre only); an event ends
earlier when its frontier is exhausted.

The shock stage combines all event hits per cell before mutation. Immutable per-tick event snapshots
use run-local monotonic integer IDs. `EventCellExposure` records link events, exposing frontier
neighbours, ticks, and cells. `CellDamageApplication` records the three combined multipliers and links
all contributing event IDs to one authoritative pre/post ecological state and recovery-completion
tick, preventing double-counting.

Primary literature supports separating disturbance timing, spatial propagation, and recovery, but
does not calibrate these equations or parameter values. See the paired evidence and boundaries in
`docs/literature/items/turner-et-al-1989-landscape-disturbance.md`.

### Collectives and governance patterns

Governance labels describe rule-diffusion patterns rather than predefined authority roles:

- centralised: one dominant system-scope rule component;
- local: many persistent, weakly connected local components;
- polycentric: multiple persistent components with cross-component communication;
- recursive: persistent rule components nested across local, regional, and system scopes.

Raw continuous topology measures always accompany labels.

## 6. Deterministic submodels

### Renewable-resource dynamics

For each cell:

\[
R_x(t+1) = R_x(t) + r_x[K_x - R_x(t)].
\]

The implementation preserves \(0\le R_x\le K_x\), recovers from zero when \(r_x>0\), and does not
overshoot capacity for \(0\le r_x\le1\).

### Harvest and energetic accounting

Resolved harvest is removed from the environmental stock and converted directly into energy:

\[
E_i(t+1)=E_i(t)+\eta h_i^*-C_{basal}-C_{move}I(move).
\]

If the raw result is less than or equal to zero, recorded energy becomes zero and the agent dies.
Dead agents leave activation but remain in cohort and event records.

### Unmet need

For configured viability target \(E^*\):

\[
U_i(t)=\max(0,E^*-E_i(t)).
\]

Cumulative unmet need includes dead cohort members and therefore does not suffer survivor bias.

### Version 0.2 landscape input

A version 0.2 landscape is either the verified uniform scalar baseline or explicit two-dimensional
capacity and initial-stock matrices. Matrix indices are `(x, y)` and shapes must equal
`(world.width, world.height)`. Values are finite and satisfy
\(0\le R_x(0)\le K_x\). Explicit matrices are scientific inputs, not generated implicitly during
model construction; any procedure that creates them must save the realized matrices as provenance.

## 7. Initialisation and baseline input

The checked-in baseline uses:

| Parameter | Value |
| --- | ---: |
| seed | 42 |
| duration | 100 ticks |
| world | 5 x 5 Von Neumann torus |
| cell occupancy | unlimited |
| initial stock/capacity | 10 / 10 |
| regeneration rate | 0.1 |
| agents | 1, centred |
| initial energy/viability target | 10 / 10 |
| basal/movement cost | 1 / 0.25 |
| harvest capacity/threshold | 2 / 1 |
| harvest conversion efficiency | 1 |
| observation | current cell, exact |
| shock/gate | none / allow-all |

All scientific parameters enter through validated configuration.

## 8. Outputs and measures

Version 0.1 holds model, cohort, and event records in memory and emits a schema-versioned JSON run
summary. Version 0.2 retains that interface and implements an opt-in persistent bundle with normalized
configuration, software and RNG provenance, the same JSON summary, and schema-versioned Parquet
tables for model, cohort, agent-event, shock-event, shock-exposure, and cell-damage records. A
manifest fixes the artifact set and records byte counts, SHA-256 digests, schema versions, and row
counts. Bundles are validated in a sibling staging directory and atomically published only when the
requested destination is absent. The bundle also streams a required NetCDF history with `(tick, x, y)`
dimensions: stock, effective capacity, effective regeneration, and recovery remaining at tick zero
and after every completed measurement, plus static baseline capacity and regeneration. Measures
include:

- survival and deaths;
- lifespan;
- energy and unmet need for the original cohort;
- cumulative harvest/consumption;
- total and mean environmental resources;
- inequality in non-negative energy, consumption, lifespan, and unmet need.

No composite welfare score is defined. Batch and sensitivity outputs must retain raw continuous
outcomes and link every row to its realized configuration and seed.

Version 0.2 also implements deterministic sequential batches. A batch names a validated base
configuration and ordered, uniquely identified override mappings. Every override declares its seed;
duplicate seeds are permitted for intentional matched or repeated conditions. Nested mappings merge
recursively and scalars/lists replace. All resolved configurations validate before execution. The
complete attempt is atomically published with normalized base/override/resolved provenance,
configuration hashes, equivalent JSON and Parquet indexes, and complete child bundles for successful
runs. A failed run remains an indexed observation with no partial child and does not stop later runs.

### Version 0.2 sensitivity-screen design

The first global screen uses three separate ungrouped Morris designs in fixed order: independent,
correlated, and system shocks. `shock.kind` is never treated as a numeric factor. All scopes vary
`event_probability`, the three damage fractions, and `recovery_ticks`; only the correlated scope
varies `spread_probability` and `max_spread_ticks`.

Each scope uses four levels, 100 candidate trajectories, 10 locally optimized selected trajectories,
and design seed 42. Probability and fraction ranges are `[0, 1]`, recovery ticks use the integer range
`[1, 10]`, and maximum spread ticks use `[0, 3]`. Integer factors must land exactly on an integer grid;
generated values are never silently rounded.

Every design point is repeated with model seeds `101`, `202`, and `303` in that order. This common
seed block pairs comparisons while retaining three stochastic realizations. Point order from the
sampler and seed order are preserved in stable run IDs and full resolved configuration provenance.
The design contains 600 runs: 180 independent, 240 correlated, and 180 system runs. A configured
maximum of 600 fails closed if generation would exceed that budget.

Sensitivity execution resolves into the existing validated sequential batch contract and persistent
batch bundle; it does not define a parallel model runner or a second result format. Morris statistics
are screening evidence, not causal effects or variance shares. Raw continuous outcomes and
replicate-seed variation remain primary evidence. See the paired evidence in
`docs/literature/items/morris-screening-stochastic-simulators.md` and ADR 0011.

## 9. Institutional-regime analysis

Later analyses standardise rolling-window features for rule adoption, spatial connectivity, boundary
persistence, enforcement, rejection/reallocation, rule entropy, and cross-scope nesting. Seeded
Gaussian mixture models evaluate 1 through 6 components using BIC and 20 initialisations. Bootstrap
stability accompanies every categorical result. Cluster labels are secondary interpretations; raw
features remain the primary evidence.

## 10. Versioned variants and implementation status

| Version | Added mechanism | Status |
| --- | --- | --- |
| v0.1 | deterministic ecology, material agents, explicit cognition/action boundaries | implemented and verified |
| v0.2 | heterogeneous ecology, recoverable shocks, persistent outputs, batch/sensitivity runs | implemented and verified |
| v0.3 | fixed local/shared/unequal information capabilities | specified |
| v0.4 | private tabular Q-learning | specified |
| v0.5 | tool diffusion and coevolving communication network | specified |
| v0.6 | payoff-biased rule diffusion and costly local enforcement | specified |
| v0.7 | nested norm scopes and governance-regime analysis | specified |
| v0.8 | transfers, exchange, holdings, and debt | specified |
| v0.9 | births, demographic turnover, and inheritance | specified extension |

## 11. Verification expectations

Each version must include unit tests for mechanisms, property tests for conservation and bounds,
small-world integration tests, and fixed-seed regression traces. Scientific claims are not made from
unverified visual patterns. The specification and executable stage trace must agree before a version
is used for experiments.

Version 0.1 passed this gate on 2026-08-29: V0–V4 fixtures, property and architecture tests, complete
tiny-trajectory and CLI regressions, death retention, deterministic order checks, and the executable
stage trace all passed. The isolated browser verifier rendered and stepped the debugging page. See
`docs/experiment_log.md` for the exact environment, commands, and the single upstream visualization
warning that remains outside application code.

Version 0.2 passed its gate on 2026-08-30: a clean locked environment, pure shock/property tests,
fixed stochastic regressions, recursive run/batch validation, the 12-run artifact-only verification
set, canonical sensitivity-design resolution, exact scheduler tests, and isolated-browser stepping all
passed. The experiment log records commands, versions, outputs, and the remaining upstream warning.
