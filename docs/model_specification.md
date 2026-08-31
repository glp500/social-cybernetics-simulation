# Canonical Scientific Specification: Three-Study Opportunity Programme

**Status:** Project 1 frozen; Projects 2 and 3 fully specified but non-executable.

This document is the programme-level ODD+D entry point. Scientific detail is authoritative in the
linked study packages; software boundaries are authoritative in `docs/architecture.md` and ADR 0012.

## 1. Purpose

The programme asks how material outcomes change as opportunity becomes progressively mediated:

```text
Project 1: objective ecological opportunity
    -> Project 2: privately observed and adaptively actionable opportunity
        -> Project 3: socially accessible opportunity
```

Each project adds only the mechanisms needed for its transformation. Project 1 establishes what
renewable ecology, mobility, simultaneous competition, disturbance, and recovery can generate alone.
Project 2 adds bounded sensing, belief, and private adaptation. Project 3 adds reports, trust,
rewiring, capability diffusion, and bounded circulation probes.

The programme does not model institutions, governance, property, firms, wage labour, markets, class,
demographic reproduction, or general-purpose language-model agents. Those are separate future
programmes, not unfinished work in Projects 1–3.

## 2. Shared ontology

- **Objective opportunity:** resource state and physical accessibility independent of an agent's
  information.
- **Privately observed opportunity:** the signal available through an agent's sensing channel.
- **Actionable opportunity:** opportunity an agent can convert through its current policy.
- **Socially accessible opportunity:** opportunity made available through reports and relations.
- **Material outcome:** harvest, energy, shortfall, survival, ecological state, or their distribution.

These terms do not imply ownership, entitlement, welfare, power, or moral evaluation. The reserved
vocabulary and necessary conditions are defined in `docs/programme/shared_ontology.md`.

## 3. Project 1 — Ecology, provisioning, and inequality

### Purpose and entities

Project 1 tests whether ecological differences and competition are sufficient to generate unequal,
risky, or persistent material outcomes before information inequality or social relations are added.

- **World:** rectangular Von Neumann grid; canonical experiments use a 5×5 torus.
- **Cell:** baseline/effective capacity, stock, baseline/effective regeneration, recovery clock.
- **Agent:** stable ID, energy, alive state; Mesa cells own position.
- **Shock event:** stable run-local ID, scope, propagation state, damage, and evidence.
- **Time:** abstract discrete ticks; model units are dimensionless.

Resource, energy, action scheduling, observation/belief, and outcome records remain distinct. Project 1
agent state contains no holdings, debt, capability, trust, role, rule, institution, or demographic
state.

### Process ordering

Tick zero records initialized ecology and cohort. Every completed tick executes exactly:

1. recover existing ecological damage;
2. relax resource stock toward effective capacity;
3. propagate/initiate shocks and combine same-cell damage;
4. observe exact local stock;
5. copy observation into belief;
6. select one literal harvest-or-move intent;
7. apply the allow-all gate;
8. resolve harvest and movement simultaneously;
9. account for harvest conversion, basal cost, and movement cost;
10. clamp death energy to zero and remove dead agents from activation;
11. append immutable measurements and spatial state.

The causal path is:

```text
Environment -> Observation -> Belief -> Intent -> Gate -> Physical resolution -> Feedback
```

The gate is an interface boundary, not an institution. It allows every Project 1 action.

### Core submodels

Relaxation toward current effective capacity is:

```text
stock_next = clip(stock + effective_rate * (effective_capacity - stock), 0, baseline_capacity)
```

The literal policy harvests when believed local stock meets the threshold; otherwise it moves to a
uniformly sampled Von Neumann neighbour. There is no rest branch or energy cap.

Contested harvest is proportional to requests. If requests on a cell sum to `Q` and stock is `S`,
agent `i` receives its request when `Q <= S`, otherwise `S * request_i / Q`. Multi-occupancy removes
movement collision rules.

Energy changes by harvested resource times conversion efficiency minus basal and movement cost.
Energy at or below zero causes mortality; dead agents remain in cohort/evidence records.

### Recoverable disturbance

Enabled shocks require an event probability, three damage fractions, and recovery duration.
Correlated shocks also require spread probability and outward-round limit.

- `independent`: one Bernoulli draw per cell-tick;
- `correlated`: one Bernoulli initiation draw per tick, immediate epicentre damage, then synchronous
  independent frontier-edge transmissions;
- `system`: one Bernoulli draw per tick, with every cell damaged on success.

Concurrent events are allowed. Same-cell/event hits are normalized before one authoritative physical
mutation. Damage compounds against current stock/effective values and restarts exact finite linear,
cell-local recovery. Stock may temporarily exceed damaged effective capacity but never baseline
capacity. Newly damaged cells receive neither same-tick recovery nor compensating regeneration.

The model-owned RNG registry fixes policy/movement at stream `(1,)` and ecological initiation,
location, and transmission at `(2,1)`, `(2,2)`, and `(2,3)`. Adding a mechanism cannot shift an
existing stream.

### Initialization and canonical experiments

The baseline is seed 42, duration 100, 5×5 torus, stock/capacity 10, regeneration 0.1, one centred
agent, energy/target 10, basal cost 1, movement cost 0.25, harvest capacity 2, threshold 1, efficiency
1, no shock, literal policy, and allow-all gate.

The frozen P1-A–E design uses seeds 101–1010, 110 short 100-tick runs and 30 long 1,000-tick runs:

- P1-A mean-preserving homogeneous/checkerboard opportunity;
- P1-B density × movement cost;
- P1-C matched expected initial shock incidence across scopes;
- P1-D recovery 2 versus 10;
- P1-E control, heterogeneous-pressure, and correlated-slow-recovery persistence regimes.

Exact conditions and project-choice status are in `docs/studies/project_1/experiments.md`.

### Outputs and analysis

Every run can publish normalized configuration, summary, software/RNG provenance, immutable Parquet
records, and complete `(tick,x,y)` NetCDF ecology into a validated atomic no-overwrite bundle. Batch
and aggregate analysis bundles cross-check JSON, Parquet, configuration hashes, and child evidence.

The Project 1 outcome vector keeps these dimensions separate:

- aggregate harvest and survival;
- shortfall frequency, spells, depth, catastrophic transitions, and cumulative unmet need;
- harvest, energy, and unmet-need inequality plus fixed-group shares;
- material-rank persistence, transitions, advantage duration, and definedness;
- depletion, capacity/regeneration deficits, recovery duration, and cumulative recovery deficit.

No composite welfare score or regime ranking exists. Analysis reads only validated artifacts or
immutable records and never steps a live model.

The specification, literature, verification, sensitivity, experiment, analysis, and interpretation
gates are frozen in `docs/studies/project_1/validation.md`.

## 4. Project 2 — Private perception and action

Project 2 is scientifically and architecturally specified but has no executable state or accepted
configuration variant. It introduces:

- sensing channel `C = (radius, noise, delay)`;
- observation histories and belief construction distinct from objective ecology;
- fixed-policy controls and tabular Q-learning comparisons;
- explicit information inequality and opportunity-to-outcome conversion measures;
- separate RNG namespace and Project 2 state composed around the Project 1 material state.

It does not add social reports, networks, trust, diffusion, institutions, exchange, or demographics.
Its eight-document authority package begins at `docs/studies/project_2/specification.md`.

## 5. Project 3 — Social information and bounded circulation

Project 3 is scientifically and architecturally specified but has no executable state or accepted
configuration variant. It introduces:

- directed reports with source, content, age, and evidence provenance;
- trust updates and controlled network rewiring;
- complete-profile capability diffusion under declared exposure rules;
- D0–D3 circulation probes with conservation-checked material and credit accounting;
- relational accessibility, concentration, segregation, diffusion, and circulation measures.

Credit is a conserved analytical token distinct from physical material and from debt/obligation
claims. Project 3 does not add institutions, governance, firms, wage labour, capital ownership,
general markets, or demographic reproduction. Its eight-document authority package begins at
`docs/studies/project_3/specification.md`.

## 6. Cross-study design concepts

- **Separation:** environment, signal, belief, intent, physical result, and interpretation are never
  silently collapsed.
- **Identifiability:** each study retains matched controls for mechanisms added in that study.
- **Evidence:** runtimes record facts once; pure analysis derives named measures afterward.
- **Reproducibility:** stochastic functions receive registered generators explicitly; global random
  calls are prohibited in scientific code.
- **Publication:** scientific directories stage beside their destination, validate completely, and
  publish atomically without overwrite.
- **Interpretation:** every headline result states the pattern, mechanism, computational domain,
  disciplinary interpretations, alternatives, missing mechanisms, and prohibited conclusions.

## 7. Claims boundary

Project 1 evidence supports model-bounded claims about ecological sufficiency for named material
outcomes. Projects 2 and 3 may support additional claims only after their own seven gates freeze.
None of the programme's current mechanisms licenses empirical forecasts or claims about wealth,
class, exploitation, capitalism, governance, moral economy, biological fitness, or real communities.

The complete authority chain is:

1. `docs/programme/overview.md` and `scope.md`;
2. this canonical specification;
3. each study's eight-document package;
4. ADRs and software architecture;
5. versioned configuration and artifact schemas;
6. frozen evidence and interpretation registers.
