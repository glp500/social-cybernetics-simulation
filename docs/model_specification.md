# Model Specification: Social Cybernetics Sugarscape

## 1. Purpose and research question

This model studies how information-extending cognitive tools alter adaptive behaviour and how
private reinforcement, social learning, and norm diffusion can produce persistent institutions.
An institution is present only when a bounded group sustains a shared rule and repeatedly enforces
it. The intended contribution is an emergence mechanism, not a claim that tools or institutions
are universally beneficial.

The first executable version is a material control model. It asks:

> What survival, resource-access, unmet-need, and inequality dynamics arise from renewable spatial
> resources, energetic constraints, and simultaneous competition before cognitive tools, social
> learning, or institutions are introduced?

Later versions add one mechanism at a time so its causal contribution remains identifiable.

## 2. Entities, state, and scales

### World

The world is a rectangular lattice of cells connected by a Von Neumann neighbourhood. The default
world is a 5 by 5 torus. A cell has no occupancy limit.

### Cell

- `resource_stock` \(R_x(t)\)
- `resource_capacity` \(K_x\)
- `regeneration_rate` \(r_x\)
- later: shock state, terrain cost, resource type, and institutional scope

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

Each deterministic tick executes:

1. resource regeneration;
2. environmental shock stage (a no-op in version 0.1);
3. observation of the current cell;
4. belief update;
5. one action intent per living agent;
6. institutional filtering (allow-all in version 0.1);
7. simultaneous physical resolution;
8. energetic accounting;
9. mortality;
10. measurement.

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

Every random draw derives from one run seed through the model-owned generator. The same configuration,
software versions, and seed must reproduce the same trajectory.

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
summary. Measures include:

- survival and deaths;
- lifespan;
- energy and unmet need for the original cohort;
- cumulative harvest/consumption;
- total and mean environmental resources;
- inequality in non-negative energy, consumption, lifespan, and unmet need.

No composite welfare score is defined. Later versions persist normalised configuration, metadata,
Parquet model/agent/event tables, and optional NetCDF spatial arrays.

## 9. Institutional-regime analysis

Later analyses standardise rolling-window features for rule adoption, spatial connectivity, boundary
persistence, enforcement, rejection/reallocation, rule entropy, and cross-scope nesting. Seeded
Gaussian mixture models evaluate 1 through 6 components using BIC and 20 initialisations. Bootstrap
stability accompanies every categorical result. Cluster labels are secondary interpretations; raw
features remain the primary evidence.

## 10. Versioned variants and implementation status

| Version | Added mechanism | Status |
| --- | --- | --- |
| v0.1 | deterministic ecology, material agents, explicit cognition/action boundaries | implementing |
| v0.2 | heterogeneous ecology, shocks, persistent outputs, batch/sensitivity runs | specified |
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

